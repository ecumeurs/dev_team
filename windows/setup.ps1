#requires -Version 5.1
<#
.SYNOPSIS
  Turn the dev_team agent set ON for native Windows Claude Code (no RTK).

.DESCRIPTION
  Windows equivalent of scripts/hookup.sh, scoped to Claude Code only:
    %USERPROFILE%\.claude\agents               -> <repo>\claude-agents
    %USERPROFILE%\.claude\skills\<name>         -> <repo>\skills\<name>   (one at a time)
    %USERPROFILE%\.local\share\dev_team\references -> <repo>\references
  Plus, if they don't already exist (or -Force is passed):
    %USERPROFILE%\.claude\CLAUDE.md    <- windows\CLAUDE.md    (copied, not linked)
    %USERPROFILE%\.claude\settings.json <- windows\settings.json (copied, not linked)

  Uses directory JUNCTIONS (New-Item -ItemType Junction), which — unlike
  symlinks on Windows — do NOT require admin rights or Developer Mode.
  Junctions only work within the same volume; if your user profile and this
  repo are on different drives, re-run with -Copy to fall back to a plain
  recursive copy instead (loses "edit repo, changes apply immediately").

  Idempotent: safe to re-run after `git pull`.

.PARAMETER Force
  Overwrite an existing CLAUDE.md / settings.json instead of skipping it.

.PARAMETER Copy
  Use recursive copies instead of junctions for agents/skills/references.
  Use this if the repo lives on a different drive than %USERPROFILE%.
#>
[CmdletBinding()]
param(
  [switch]$Force,
  [switch]$Copy
)

$ErrorActionPreference = 'Stop'

$RepoDir    = Split-Path -Parent $PSScriptRoot   # windows\.. -> repo root
$ClaudeDir  = Join-Path $env:USERPROFILE '.claude'
$failed     = $false

function Ensure-Link {
  param(
    [string]$Src,
    [string]$Dst,
    [string]$Label
  )

  if (-not (Test-Path -LiteralPath $Src -PathType Container)) {
    Write-Warning "$Src does not exist; skipping $Label."
    return
  }

  $dstParent = Split-Path -Parent $Dst
  if (-not (Test-Path -LiteralPath $dstParent)) {
    New-Item -ItemType Directory -Path $dstParent -Force | Out-Null
  }

  if (Test-Path -LiteralPath $Dst) {
    $item = Get-Item -LiteralPath $Dst -Force
    $isReparse = [bool]($item.Attributes -band [IO.FileAttributes]::ReparsePoint)

    if ($isReparse) {
      $target = (Get-Item -LiteralPath $Dst -Force).Target
      $resolvedTarget = $null
      if ($target) { $resolvedTarget = (Resolve-Path -LiteralPath $target -ErrorAction SilentlyContinue).Path }
      $resolvedSrc = (Resolve-Path -LiteralPath $Src).Path
      if ($resolvedTarget -eq $resolvedSrc) {
        Write-Host "${Label}: already linked ($Dst -> $Src)"
        return
      }
      Write-Host "${Label}: junction points elsewhere ($target); replacing."
      Remove-Item -LiteralPath $Dst -Force -Recurse
    }
    else {
      Write-Warning "${Label}: refusing to touch $Dst — it exists and is not a junction."
      Write-Warning "  Move it aside manually if you want dev_team to manage it."
      $script:failed = $true
      return
    }
  }

  if ($Copy) {
    Copy-Item -LiteralPath $Src -Destination $Dst -Recurse -Force
    Write-Host "${Label}: copied $Dst <- $Src"
  }
  else {
    New-Item -ItemType Junction -Path $Dst -Target $Src | Out-Null
    Write-Host "${Label}: linked $Dst -> $Src"
  }
}

# --- agents ---
Ensure-Link -Src (Join-Path $RepoDir 'claude-agents') -Dst (Join-Path $ClaudeDir 'agents') -Label 'Claude Code agents'

# --- references (shared docs spec-writer/ux-writer read) ---
$refDst = Join-Path $env:USERPROFILE '.local\share\dev_team\references'
Ensure-Link -Src (Join-Path $RepoDir 'references') -Dst $refDst -Label 'References'

# --- skills, one subdirectory at a time (never the whole skills\ folder) ---
$skillsSrcRoot = Join-Path $RepoDir 'skills'
$skillsDstRoot = Join-Path $ClaudeDir 'skills'
$linkedSkills = @()
if (Test-Path -LiteralPath $skillsSrcRoot -PathType Container) {
  Get-ChildItem -LiteralPath $skillsSrcRoot -Directory | ForEach-Object {
    $name = $_.Name
    Ensure-Link -Src $_.FullName -Dst (Join-Path $skillsDstRoot $name) -Label "Skill:$name"
    $linkedSkills += $name
  }
}

# --- CLAUDE.md / settings.json: copied, not linked (these are meant to be
#     edited per-machine, not kept byte-identical to the repo) ---
function Copy-IfAbsent {
  param([string]$Src, [string]$Dst, [string]$Label)
  if ((Test-Path -LiteralPath $Dst) -and (-not $Force)) {
    Write-Host "${Label}: $Dst already exists; leaving it alone (use -Force to overwrite)."
    return
  }
  $dstParent = Split-Path -Parent $Dst
  if (-not (Test-Path -LiteralPath $dstParent)) {
    New-Item -ItemType Directory -Path $dstParent -Force | Out-Null
  }
  Copy-Item -LiteralPath $Src -Destination $Dst -Force
  Write-Host "${Label}: wrote $Dst"
}

Copy-IfAbsent -Src (Join-Path $PSScriptRoot 'CLAUDE.md')     -Dst (Join-Path $ClaudeDir 'CLAUDE.md')     -Label 'Global CLAUDE.md'
Copy-IfAbsent -Src (Join-Path $PSScriptRoot 'settings.json') -Dst (Join-Path $ClaudeDir 'settings.json') -Label 'Global settings.json'

if ($failed) {
  Write-Error "One or more links could not be established; see warnings above."
  exit 1
}

Write-Host ""
Write-Host "dev_team agents are now live for Claude Code (Windows, no RTK):"
$agentNames = Get-ChildItem -LiteralPath (Join-Path $RepoDir 'claude-agents') -Filter '*.md' |
  ForEach-Object { $_.BaseName }
Write-Host ("  " + ($agentNames -join ', '))

if ($linkedSkills.Count -gt 0) {
  Write-Host ""
  Write-Host "Skills linked into $skillsDstRoot :"
  Write-Host ("  " + ($linkedSkills -join ', '))
}
