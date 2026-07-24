param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$momentumPath = Join-Path $root "firmware\momentum"
$manifestPath = Join-Path $root "firmware\flipper69\MANIFEST.json"
$manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json

Write-Host "FLIPPER69 firmware fork init" -ForegroundColor Red
Write-Host ("Upstream: " + $manifest.upstream.repo + " [" + $manifest.upstream.branch + "]")

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "git is required"
}

Push-Location $root
try {
    if (-not (Test-Path $momentumPath)) {
        if (Test-Path ".gitmodules") {
            Write-Host "Initializing submodule..."
            git submodule update --init --recursive firmware/momentum 2>$null
        }
        if (-not (Test-Path $momentumPath)) {
            Write-Host "Cloning Momentum-Firmware (shallow)..."
            New-Item -ItemType Directory -Force -Path (Split-Path $momentumPath) | Out-Null
            git clone --depth 1 --branch $manifest.upstream.branch `
                $manifest.upstream.repo $momentumPath
        }
    }

    if (-not (Test-Path $momentumPath)) {
        throw "Momentum tree missing at $momentumPath"
    }

    Push-Location $momentumPath
    $sha = (git rev-parse HEAD).Trim()
    Pop-Location

    $manifest.upstream.sha = $sha
    $manifest | ConvertTo-Json -Depth 8 | Set-Content $manifestPath -Encoding UTF8
    Write-Host "Pinned upstream SHA: $sha" -ForegroundColor Green

    $fbt = Get-Command ./fbt -ErrorAction SilentlyContinue
    if (-not $fbt) {
        Write-Host "Note: run fbt from firmware/momentum after toolchain setup (see Momentum wiki)" -ForegroundColor Yellow
    }
} finally {
    Pop-Location
}

Write-Host "Next: .\scripts\sync-faps-to-firmware.ps1" -ForegroundColor Magenta