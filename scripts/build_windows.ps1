# Build the MizMap Windows installer.
#
# Two stages:
#   1. PyInstaller produces packaging/dist/mizmap/ (one-folder bundle).
#   2. Inno Setup wraps that folder into packaging/dist/mizmap-setup-<ver>.exe.
#
# Run from the repo root: `scripts/build_windows.ps1`. Add -Clean to wipe
# build/ and dist/ first.
#
# Requirements: uv (for `uv run pyinstaller`) and Inno Setup 6 (ISCC.exe).
# The script searches both Program Files and %LOCALAPPDATA%\Programs for
# ISCC, since winget installs Inno Setup per-user by default.

param(
    [switch]$Clean
)

# PS 5.1 wraps each stderr line from a native exe in an ErrorRecord; under
# 'Stop' that aborts the script as soon as PyInstaller or ISCC logs to
# stderr (which they do for INFO messages). Use 'Continue' and rely on
# explicit $LASTEXITCODE checks below.
$ErrorActionPreference = 'Continue'

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$DistDir  = Join-Path $RepoRoot 'packaging\dist'
$BuildDir = Join-Path $RepoRoot 'packaging\build'
$Spec     = Join-Path $RepoRoot 'packaging\mizmap.spec'
$Iss      = Join-Path $RepoRoot 'packaging\mizmap.iss'

if ($Clean) {
    Write-Host '== Cleaning packaging/dist + packaging/build =='
    if (Test-Path $DistDir)  { Remove-Item -Recurse -Force $DistDir }
    if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir }
}

# Pull AppVersion from mizmap/__init__.py — single source of truth.
$initPy = Get-Content (Join-Path $RepoRoot 'mizmap\__init__.py') -Raw
if ($initPy -notmatch '__version__\s*=\s*"([^"]+)"') {
    throw 'Could not find __version__ in mizmap/__init__.py'
}
$AppVersion = $Matches[1]
Write-Host "== Building MizMap $AppVersion =="

Write-Host '== Stage 1: PyInstaller =='
& uv run pyinstaller $Spec --noconfirm --distpath $DistDir --workpath $BuildDir
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed (exit $LASTEXITCODE)" }

# Locate Inno Setup. winget installs it per-user; some Anthropic-supplied
# images may install system-wide. Check both.
$IsccCandidates = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
)
$Iscc = $IsccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $Iscc) {
    throw 'Inno Setup 6 not found. Install with: winget install JRSoftware.InnoSetup'
}

Write-Host "== Stage 2: Inno Setup ($Iscc) =="
& $Iscc "/DAppVersion=$AppVersion" $Iss
if ($LASTEXITCODE -ne 0) { throw "ISCC failed (exit $LASTEXITCODE)" }

$Installer = Join-Path $DistDir "mizmap-setup-$AppVersion.exe"
if (Test-Path $Installer) {
    $size = [math]::Round((Get-Item $Installer).Length / 1MB, 1)
    Write-Host "== Done. Installer: $Installer ($size MB) =="
} else {
    Write-Warning "Installer not found at expected path: $Installer"
}
