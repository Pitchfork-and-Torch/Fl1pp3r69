param(
    [ValidateSet(
        "casefile_ops", "probe_subghz", "probe_nfc", "probe_ir", "manifest_viewer",
        "probe_rfid", "probe_ibutton", "probe_ble", "probe_gpio", "probe_badusb", "all"
    )]
    [string]$App = "casefile_ops"
)

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$distDir = Join-Path $root "dist"

function Resolve-Ufbt {
    $cmd = Get-Command ufbt -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    py -m pip install --upgrade ufbt | Out-Null
    $cmd = Get-Command ufbt -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $scripts = Join-Path $env:LOCALAPPDATA "Programs\Python"
    if (Test-Path $scripts) {
        $found = Get-ChildItem -Path $scripts -Recurse -Filter ufbt.exe -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found) { return $found.FullName }
    }
    return $null
}

$ufbt = Resolve-Ufbt
if (-not $ufbt) { throw "ufbt not found. Install: py -m pip install --upgrade ufbt" }

$apps = if ($App -eq "all") {
    @(
        "casefile_ops", "probe_subghz", "probe_nfc", "probe_ir", "manifest_viewer",
        "probe_rfid", "probe_ibutton", "probe_ble", "probe_gpio", "probe_badusb"
    )
} else {
    @($App)
}

New-Item -ItemType Directory -Force -Path $distDir | Out-Null

foreach ($name in $apps) {
    $fapDir = Join-Path $root "fap\$name"
    if (-not (Test-Path (Join-Path $fapDir "application.fam"))) {
        Write-Warning "Skip $name"
        continue
    }

    Write-Host "FLIPPER69 BUILD $name" -ForegroundColor Red
    Push-Location $fapDir

    if (-not (Test-Path ".env")) {
        cmd /c "`"$ufbt`" dotenv_create >nul 2>nul"
    }
    if (-not (Test-Path ".ufbt\current")) {
        cmd /c "`"$ufbt`" update >nul 2>nul"
    }

    & $ufbt
    if ($LASTEXITCODE -ne 0) { throw "Build failed: $name" }

    $built = Get-ChildItem -Path "dist\*.fap" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($built) {
        Copy-Item $built.FullName (Join-Path $distDir $built.Name) -Force
        $hash = (Get-FileHash $built.FullName -Algorithm SHA256).Hash.ToLower()
        Write-Host "OK $($built.Name) $hash" -ForegroundColor Green
    }

    Pop-Location
}

Write-Host ("Done. Output: " + $distDir) -ForegroundColor Magenta