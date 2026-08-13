param(
    [ValidateSet("faps", "package", "all")]
    [string]$Target = "all"
)

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$momentumPath = Join-Path $root "firmware\momentum"
$outDir = Join-Path $root "dist\firmware"
$rootDist = Join-Path $root "dist"
$fapSrc = Join-Path $momentumPath "build\f7-firmware-C\.extapps"

if (-not (Test-Path $momentumPath)) {
    throw "Run .\scripts\init-firmware-fork.ps1 first"
}

New-Item -ItemType Directory -Force -Path $outDir | Out-Null

function Copy-BuiltFaps {
    if (-not (Test-Path $fapSrc)) { return }
    Copy-Item (Join-Path $fapSrc "flipper69_*.fap") $rootDist -Force
    Copy-Item (Join-Path $fapSrc "flipper69_*.fap") $outDir -Force
    Get-ChildItem $rootDist\flipper69_*.fap | ForEach-Object {
        $hash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower()
        Write-Host "OK $($_.Name) $hash" -ForegroundColor Green
    }
}

Push-Location $momentumPath
try {
    $fbtCmd = if (Test-Path ".\fbt.cmd") { ".\fbt.cmd" } else { ".\fbt" }

    if ($Target -eq "faps" -or $Target -eq "all") {
        Write-Host "Building Fl1pp3r69 FAPs..." -ForegroundColor Red
        & $fbtCmd fap_flipper69_casefile_ops fap_flipper69_probe_nfc fap_flipper69_probe_subghz fap_flipper69_manifest_viewer
        if ($LASTEXITCODE -ne 0) { throw "FAP build failed" }
        Copy-BuiltFaps
    }

    if ($Target -eq "package" -or $Target -eq "all") {
        Write-Host "Building updater minpackage (Momentum base)..." -ForegroundColor Red
        & $fbtCmd COMPACT=1 DEBUG=0 SKIP_EXTERNAL=1 updater_minpackage
        if ($LASTEXITCODE -ne 0) { throw "updater_minpackage failed" }

        $built = Get-ChildItem -Path "dist\f7-C" -Filter "flipper-z-f7-update-*.tgz" -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($built) {
            Copy-Item $built.FullName $outDir -Force
            $hash = (Get-FileHash $built.FullName -Algorithm SHA256).Hash.ToLower()
            Write-Host "Firmware package: $($built.Name) $hash" -ForegroundColor Green
        }
    }
} finally {
    Pop-Location
}

Write-Host ("Output: " + $outDir) -ForegroundColor Magenta