#requires -Version 5.1
<#
.SYNOPSIS
  Turn the dev_team agent set OFF for native Windows Claude Code.

.DESCRIPTION
  Windows equivalent of scripts/hookoff.sh, scoped to Claude Code only.
  Removes the junctions setup.ps1 created:
    %USERPROFILE%\.claude\agents
    %USERPROFILE%\.claude\skills\<name>  (each dev_team skill, by name)
  Does NOT remove:
    %USERPROFILE%\.local\share\dev_team\references  (inert reference docs,
      same rationale as hookoff.sh on Linux — not "team presence")
    %USERPROFILE%\.claude\CLAUDE.md / settings.json  (these were copied, not
      linked, and are meant to be edited per-machine — teardown never
      deletes machine config, only the links this script's counterpart made)

  Only removes a target if it is actually a junction pointing into this
  repo. A real folder (or a junction pointing elsewhere) is left untouched
  and reported.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$RepoDir   = Split-Path -Parent $PSScriptRoot
$ClaudeDir = Join-Path $env:USERPROFILE '.claude'

function Remove-IfOurJunction {
  param([string]$Dst, [string]$ExpectedSrc, [string]$Label)

  if (-not (Test-Path -LiteralPath $Dst)) {
    Write-Host "${Label}: $Dst does not exist; nothing to do."
    return
  }

  $item = Get-Item -LiteralPath $Dst -Force
  $isReparse = [bool]($item.Attributes -band [IO.FileAttributes]::ReparsePoint)

  if (-not $isReparse) {
    Write-Warning "${Label}: $Dst is a real folder, not a junction — leaving it alone."
    return
  }

  $target = $item.Target
  $resolvedTarget = $null
  if ($target) { $resolvedTarget = (Resolve-Path -LiteralPath $target -ErrorAction SilentlyContinue).Path }
  $resolvedExpected = (Resolve-Path -LiteralPath $ExpectedSrc -ErrorAction SilentlyContinue).Path

  if ($resolvedTarget -and $resolvedExpected -and $resolvedTarget -ne $resolvedExpected) {
    Write-Warning "${Label}: $Dst points elsewhere ($target) — leaving it alone."
    return
  }

  Remove-Item -LiteralPath $Dst -Force -Recurse
  Write-Host "${Label}: removed $Dst"
}

Remove-IfOurJunction -Dst (Join-Path $ClaudeDir 'agents') -ExpectedSrc (Join-Path $RepoDir 'claude-agents') -Label 'Claude Code agents'

$skillsSrcRoot = Join-Path $RepoDir 'skills'
$skillsDstRoot = Join-Path $ClaudeDir 'skills'
if (Test-Path -LiteralPath $skillsSrcRoot -PathType Container) {
  Get-ChildItem -LiteralPath $skillsSrcRoot -Directory | ForEach-Object {
    $name = $_.Name
    Remove-IfOurJunction -Dst (Join-Path $skillsDstRoot $name) -ExpectedSrc $_.FullName -Label "Skill:$name"
  }
}

Write-Host ""
Write-Host "dev_team agent/skill links removed. References junction and"
Write-Host "CLAUDE.md/settings.json were left untouched (see script header)."
