param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$momentumPath = Join-Path $root "firmware\momentum"
$manifestPath = Join-Path $root "firmware\flipper69\MANIFEST.json"

if (-not (Test-Path $momentumPath)) {
    throw "Run .\scripts\init-firmware-fork.ps1 first"
}

$manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
$userRoot = Join-Path $momentumPath "applications_user"
New-Item -ItemType Directory -Force -Path $userRoot | Out-Null

function Link-Fap {
    param([string]$Source, [string]$Target)
    $src = Join-Path $root $Source
    $dst = Join-Path $momentumPath $Target

    if (-not (Test-Path $src)) {
        throw "Missing FAP source: $src"
    }

    $parent = Split-Path $dst -Parent
    New-Item -ItemType Directory -Force -Path $parent | Out-Null

    if (Test-Path $dst) {
        if ($Force) {
            Remove-Item $dst -Recurse -Force
        } else {
            Write-Host "Exists: $Target" -ForegroundColor DarkGray
            return
        }
    }

    cmd /c mklink /J "$dst" "$src" | Out-Null
    Write-Host "Linked: $Source -> $Target" -ForegroundColor Green
}

foreach ($fap in $manifest.faps) {
    Link-Fap -Source $fap.source -Target $fap.target
}

Write-Host "FAP junctions ready under applications_user/" -ForegroundColor Magenta
Write-Host "Next: .\scripts\apply-flipper69-patches.ps1" -ForegroundColor Magenta