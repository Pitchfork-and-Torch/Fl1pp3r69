param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$overlay = Join-Path $root "firmware\flipper69"
$momentumPath = Join-Path $root "firmware\momentum"
$manifestPath = Join-Path $overlay "MANIFEST.json"

if (-not (Test-Path $momentumPath)) {
    throw "Run .\scripts\init-firmware-fork.ps1 first"
}

$manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json

foreach ($patch in $manifest.patches) {
    $src = Join-Path $overlay $patch.file
    if (-not (Test-Path $src)) {
        $alt = Join-Path $overlay ("patches\" + (Split-Path $patch.file -Leaf))
        if (Test-Path $alt) { $src = $alt } else { throw "Missing patch: $($patch.file)" }
    }

    $dst = Join-Path $momentumPath $patch.target
    $parent = Split-Path $dst -Parent
    if (-not $DryRun) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
        Copy-Item $src $dst -Force
    }
    Write-Host ("Patch " + $(if ($DryRun) { "(dry) " } else { "" }) + "$($patch.file) -> $($patch.target)") -ForegroundColor Green
}

$themeSrc = Join-Path $overlay $manifest.theme.file
$themeDst = Join-Path $momentumPath $manifest.theme.target
if (Test-Path $themeSrc) {
    if (-not $DryRun) {
        New-Item -ItemType Directory -Force -Path (Split-Path $themeDst -Parent) | Out-Null
        Copy-Item $themeSrc $themeDst -Force
    }
    Write-Host "Theme -> $($manifest.theme.target)" -ForegroundColor Green
}

Write-Host "Patches applied. Wire service registration in P2 (application.fam)." -ForegroundColor Magenta