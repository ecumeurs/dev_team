"""Tests for scripts/cve-watch.py: the exposure class and the host flag.

Offline: osv-scanner is replaced by a recorded result and NVD answers come
from a fresh cache entry, so no network is used.

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "cve-watch.py"
spec = importlib.util.spec_from_file_location("cve_watch", SCRIPT)
cw = importlib.util.module_from_spec(spec)
sys.modules["cve_watch"] = cw           # dataclasses look their module up there
spec.loader.exec_module(cw)

TODAY = dt.date.today().isoformat()
PGB_CPE = "cpe:2.3:a:pgbouncer:pgbouncer"
NGINX_CPE = "cpe:2.3:a:f5:nginx_open_source"
DOCKER_CPE = "cpe:2.3:a:docker:engine"

HEADER = 'schema = 1\nupdated = 2026-11-24\n'
PLATFORMS = f'''
[[platform]]
name = "PgBouncer"
version = "1.26.1"
cpe = "{PGB_CPE}"
exposure = "internal"

[[platform]]
name = "nginx (web front)"
version = "1.26.3"
cpe = "{NGINX_CPE}"
exposure = "exposed"

[[platform]]
name = "Docker Engine"
version = "29.0.0"
cpe = "{DOCKER_CPE}"
host = true
'''


def osv_package(path: Path, eco: str, name: str, version: str, vid: str, score: str) -> dict:
    return {"source": {"path": str(path)}, "packages": [{
        "package": {"ecosystem": eco, "name": name, "version": version},
        "vulnerabilities": [{"id": vid, "summary": f"{name} is vulnerable", "published": TODAY + "T00:00:00Z",
                             "affected": [{"package": {"name": name},
                                           "ranges": [{"events": [{"introduced": "0"}, {"fixed": "99.0"}]}]}]}],
        "groups": [{"ids": [vid], "aliases": [], "max_severity": score}],
    }]}


def nvd_item(cve: str, cpe: str, score: float) -> dict:
    return {"cve": {
        "id": cve, "published": TODAY + "T00:00:00", "vulnStatus": "Analyzed",
        "descriptions": [{"lang": "en", "value": f"{cve} description."}],
        "metrics": {"cvssMetricV31": [{"cvssData": {"baseScore": score}}]},
        "configurations": [{"nodes": [{"cpeMatch": [
            {"vulnerable": True, "criteria": cpe + ":*:*:*:*:*:*:*:*", "versionEndExcluding": "99.0"}]}]}],
    }}


class Env(unittest.TestCase):
    """A ~/work stand-in with one project, its cache, state and config."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.root = base / "work"
        self.project = self.root / "proj"
        (self.project / "bricks/api").mkdir(parents=True)
        (self.project / "bricks/api/requirements.txt").write_text("foo==1.0\n")
        (self.project / "bricks/web").mkdir(parents=True)
        (self.project / "bricks/web/requirements.txt").write_text("bar==1.0\n")
        (self.project / "sbom").mkdir()
        (self.project / "sbom/exporter.cdx.json").write_text("{}")
        config = base / "config.toml"
        config.write_text(f'root = "{self.root}"\nnotify = false\nreport_dir = "{base / "reports"}"\n')
        self.saved = {k: getattr(cw, k) for k in ("CONFIG_PATH", "CACHE_DIR", "STATE_DIR", "run_osv")}
        cw.CONFIG_PATH, cw.CACHE_DIR, cw.STATE_DIR = config, base / "cache", base / "state"
        self.osv = {"results": [
            osv_package(self.project / "bricks/api/requirements.txt", "PyPI", "foo", "1.0", "GHSA-int1-0000-0000", "7.5"),
            osv_package(self.project / "bricks/web/requirements.txt", "PyPI", "bar", "1.0", "GHSA-exp1-0000-0000", "7.5"),
            osv_package(self.project / "sbom/exporter.cdx.json", "Go", "golang.org/x/net", "0.1.0", "GO-2026-0001", "5.3"),
        ]}
        cw.run_osv = lambda cfg, project, tech, out: self.osv
        self.nvd_cache(PGB_CPE, "1.26.1", [nvd_item("CVE-2026-0001", PGB_CPE, 9.8)])
        self.nvd_cache(NGINX_CPE, "1.26.3", [nvd_item("CVE-2026-0002", NGINX_CPE, 7.5)])
        self.nvd_cache(DOCKER_CPE, "29.0.0", [nvd_item("CVE-2026-0003", DOCKER_CPE, 8.6)])

    def tearDown(self):
        for k, v in self.saved.items():
            setattr(cw, k, v)
        self.tmp.cleanup()

    def nvd_cache(self, cpe: str, version: str, items: list[dict]) -> None:
        name = cw.cpe_name(cpe, version)
        path = cw.CACHE_DIR / "nvd" / (hashlib.sha1(name.encode()).hexdigest() + ".json")
        cw.write_json(path, {"cpe": name, "vulnerabilities": items})

    def write_tech(self, text: str) -> None:
        (self.project / ".tech").write_text(HEADER + text)

    def run_cmd(self, fn, **kw) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = fn(argparse.Namespace(**kw), cw.load_config())
        return code, out.getvalue()

    def check(self, json_out: bool = False) -> tuple[int, str]:
        return self.run_cmd(cw.cmd_check, dir=str(self.project), package=None, min_severity=None,
                            json=json_out, verbose=False)

    def sweep(self, all_items: bool = True) -> int:
        code, _ = self.run_cmd(cw.cmd_sweep, days=None, all=all_items, min_severity=None, project=["proj"],
                               from_run=None, dry_run=False)
        return code

    def todo(self) -> str:
        path = self.project / cw.TODO_NAME
        return path.read_text() if path.exists() else ""


class Lint(Env):
    def lint(self) -> tuple[list[str], list[str]]:
        _, errors, warnings = cw.load_tech(self.project)
        return errors, warnings

    def test_valid_class_and_table_are_clean(self):
        self.write_tech(PLATFORMS + '\n[exposure]\ninternal = ["bricks/api/requirements.txt", "sbom/*.cdx.json"]\n')
        self.assertEqual(self.lint(), ([], []))

    def test_unknown_platform_exposure_is_an_error(self):
        self.write_tech('[[platform]]\nname = "X"\nversion = "1"\ncpe = "cpe:2.3:a:x:x"\nexposure = "private"\n')
        errors, _ = self.lint()
        self.assertEqual(errors, ['.tech: platform `X` exposure must be "exposed" or "internal"'])

    def test_host_platform_cannot_be_internal(self):
        self.write_tech('[[platform]]\nname = "X"\nversion = "1"\ncpe = "cpe:2.3:a:x:x"\n'
                        'exposure = "internal"\nhost = true\n')
        self.assertIn("cannot be \"internal\"", self.lint()[0][0])

    def test_host_must_be_boolean(self):
        self.write_tech('[[platform]]\nname = "X"\nversion = "1"\ncpe = "cpe:2.3:a:x:x"\nhost = "yes"\n')
        self.assertEqual(self.lint()[0], [".tech: platform `X` host must be true or false"])

    def test_table_errors_and_warnings(self):
        self.write_tech('[exposure]\ninternal = ["../other/requirements.txt", "gone/requirements.txt"]\n'
                        'exposed = ["x"]\n')
        errors, warnings = self.lint()
        self.assertIn(".tech: exposure: unknown key `exposed` (only `internal`)", errors)
        self.assertIn(".tech: exposure `internal` entry `../other/requirements.txt` must stay inside the project",
                      errors)
        self.assertEqual(warnings, [".tech: exposure `internal` entry `gone/requirements.txt` does not exist"])

    def test_table_must_list_strings(self):
        self.write_tech('[exposure]\ninternal = "bricks/api"\n')
        self.assertEqual(self.lint()[0], [".tech: exposure `internal` must be a list of paths relative to the root"])

    def test_source_matching(self):
        pats = ["bricks/api", "sbom/*.cdx.json"]
        self.assertTrue(cw.source_is_internal("bricks/api/requirements.txt", pats))
        self.assertTrue(cw.source_is_internal("sbom/exporter.cdx.json", pats))
        self.assertFalse(cw.source_is_internal("bricks/apiserver/requirements.txt", pats))
        self.assertFalse(cw.source_is_internal("bricks/web/requirements.txt", pats))


class Check(Env):
    def test_default_is_exposed_and_unchanged(self):
        self.write_tech(PLATFORMS.replace('exposure = "internal"', ""))
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertTrue(out.startswith("proj: 6 at or above medium, 0 below, 0 accepted in .tech\n"))
        self.assertNotIn("internal", out)

    def test_internal_reported_but_not_counted(self):
        self.write_tech(PLATFORMS + '\n[exposure]\ninternal = ["bricks/api/requirements.txt"]\n')
        code, out = self.check()
        first = out.splitlines()[0]
        self.assertEqual(first, "proj: 4 at or above medium, 0 below, 0 accepted in .tech; "
                                "2 internal (2 at or above medium), reported only")
        internal_part = out.split("internal, reported only")[1]
        self.assertIn("CVE-2026-0001", internal_part)          # PgBouncer platform
        self.assertIn("GHSA-int1-0000-0000", internal_part)    # lockfile mapped internal
        self.assertIn("i critical 9.8", internal_part)
        self.assertEqual(code, 1)                              # nginx and the rest still count

    def test_only_internal_findings_exit_zero(self):
        self.write_tech(PLATFORMS.replace('exposure = "exposed"', 'exposure = "internal"')
                        .replace("host = true", 'exposure = "internal"')
                        + '\n[exposure]\ninternal = ["bricks", "sbom"]\n')
        code, out = self.check()
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("proj: 0 at or above medium, 0 below"))

    def test_mixed_sources_stay_exposed(self):
        self.osv["results"].append(osv_package(self.project / "bricks/web/requirements.txt",
                                               "PyPI", "foo", "1.0", "GHSA-int1-0000-0000", "7.5"))
        self.write_tech('\n[exposure]\ninternal = ["bricks/api"]\n')
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertNotIn("internal, reported only", out)

    def test_host_flag_and_json(self):
        self.write_tech(PLATFORMS)
        code, out = self.check(json_out=True)
        data = {f["id"]: f for f in json.loads(out)["findings"]}
        self.assertEqual(data["CVE-2026-0003"]["host"], True)
        self.assertEqual(data["CVE-2026-0003"]["exposure"], "exposed")
        self.assertEqual(data["CVE-2026-0001"]["exposure"], "internal")
        self.assertEqual(data["GHSA-exp1-0000-0000"]["exposure"], "exposed")
        _, text = self.check()
        self.assertIn("CVE-2026-0003", text)
        self.assertIn("[reaches the host]", text)


class Sweep(Env):
    def test_internal_writes_no_item(self):
        self.write_tech(PLATFORMS + '\n[exposure]\ninternal = ["bricks/api/requirements.txt"]\n')
        self.assertEqual(self.sweep(), 0)
        todo = self.todo()
        for key in ("CVE-2026-0002:platform/nginx (web front)", "GHSA-exp1-0000-0000:PyPI/bar",
                    "GO-2026-0001:Go/golang.org/x/net", "CVE-2026-0003:platform/Docker Engine"):
            self.assertIn(f"<!-- cve-watch:{key} -->", todo)
        self.assertNotIn("CVE-2026-0001", todo)
        self.assertNotIn("GHSA-int1-0000-0000", todo)
        self.assertIn("· reaches the host", todo)
        state = json.loads((cw.STATE_DIR / "state.json").read_text())["seen"]["proj"]
        self.assertNotIn("GHSA-int1-0000-0000:PyPI/foo", state)
        report = (Path(self.tmp.name) / "reports" / f"{TODAY}.proj.md").read_text()
        self.assertIn("- **Internal, reported only (no item, `.tech` classes them internal):** 2", report)
        self.assertIn("2 internal findings (reported only", report)

    def test_open_item_ticked_when_class_turns_internal(self):
        self.write_tech(PLATFORMS.replace('exposure = "internal"', ""))
        self.sweep()
        self.assertIn("- [ ] **critical 9.8** CVE-2026-0001", self.todo())
        self.write_tech(PLATFORMS)
        self.sweep()
        line = next(x for x in self.todo().splitlines() if "CVE-2026-0001" in x)
        self.assertTrue(line.startswith("- [x]"))
        self.assertIn(f"· internal in .tech {TODAY}", line)

    def test_internal_becoming_exposed_gets_an_item(self):
        self.write_tech(PLATFORMS + '\n[exposure]\ninternal = ["bricks/api/requirements.txt"]\n')
        self.sweep(all_items=False)
        self.assertNotIn("GHSA-int1-0000-0000", self.todo())
        self.write_tech(PLATFORMS)
        # Outside the date window: only "first seen" can raise it.
        self.osv["results"][0]["packages"][0]["vulnerabilities"][0]["published"] = "2020-01-01T00:00:00Z"
        self.sweep(all_items=False)
        self.assertIn("<!-- cve-watch:GHSA-int1-0000-0000:PyPI/foo -->", self.todo())


if __name__ == "__main__":
    unittest.main()
