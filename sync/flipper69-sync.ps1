<#
.SYNOPSIS
    Fl1pp3r69 v3 desktop exfil bridge - USB serial + optional SD import.
    Prefer: python -m flipper69 sync --sd <path>
.DESCRIPTION
    Receives JSON-lines from Flipper USB serial OR imports an SD card tree.
    Verifies SHA-256 artifacts and writes TIMELINE.jsonl receipts.
.PARAMETER ComPort
    Serial port (e.g. COM7). Auto-detect if omitted (serial mode).
.PARAMETER OpsRoot
    Local operations root. Default: %USERPROFILE%\.flipper69\ops
    Override with env FLIPPER69_OPS_ROOT.
.PARAMETER SdImport
    Path to SD card root (or examples/sd_card) to bulk-import operations.
.PARAMETER Once
    Process one op then exit (serial mode waits forever by default).
.EXAMPLE
    .\flipper69-sync.ps1 -ComPort COM7
.EXAMPLE
    .\flipper69-sync.ps1 -SdImport ..\examples\sd_card
#>
param(
    [string]$ComPort,
    [string]$OpsRoot = $(if ($env:FLIPPER69_OPS_ROOT) { $env:FLIPPER69_OPS_ROOT } else { Join-Path $env:USERPROFILE ".flipper69\ops" }),
    [string]$SdImport,
    [switch]$Once
)

$ErrorActionPreference = "Stop"
$F69Version = "4.0.0"

function Write-Banner {
    Write-Host ""
    Write-Host "  +----------------------------------------------+" -ForegroundColor DarkRed
    Write-Host "  |  FL1PP3R69 EXFIL BRIDGE  v$F69Version            |" -ForegroundColor Red
    Write-Host "  |  the dolphin grew teeth                      |" -ForegroundColor DarkGray
    Write-Host "  +----------------------------------------------+" -ForegroundColor DarkRed
    Write-Host ""
}

function Get-FlipperComPort {
    Get-CimInstance Win32_PnPEntity |
        Where-Object { $_.Name -match "USB Serial|Flipper|STM32|CDC" } |
        ForEach-Object {
            if ($_.Name -match "\(COM(\d+)\)") { return "COM$($Matches[1])" }
        }
    return $null
}

function Write-TimelineEntry {
    param([string]$OpPath, [string]$Event, [hashtable]$Data = @{})
    $line = @{
        ts     = (Get-Date).ToUniversalTime().ToString("o")
        event  = $Event
        source = "flipper69-sync"
        ver    = $F69Version
        data   = $Data
    } | ConvertTo-Json -Compress
    $tl = Join-Path $OpPath "TIMELINE.jsonl"
    Add-Content -Path $tl -Value $line -Encoding UTF8
}

function Test-Sha256Match {
    param([string]$Path, [string]$Expected)
    if (-not $Expected) { return $true }
    $hash = (Get-FileHash -Path $Path -Algorithm SHA256).Hash.ToLower()
    return $hash -eq $Expected.ToLower()
}

function Import-SdTree {
    param([string]$SdRoot, [string]$DestRoot)
    $opsSrc = Join-Path $SdRoot "flipper69\operations"
    if (-not (Test-Path $opsSrc)) {
        throw "No flipper69/operations under $SdRoot"
    }
    $destOps = Join-Path $DestRoot "operations"
    New-Item -ItemType Directory -Force -Path $destOps | Out-Null

    $imported = 0
    $verified = 0
    Get-ChildItem -Path $opsSrc -Directory | Where-Object { $_.Name -like "op-*" } | ForEach-Object {
        $opId = $_.Name
        $target = Join-Path $destOps $opId
        Write-Host "[>] IMPORT $opId" -ForegroundColor Cyan
        if (Test-Path $target) {
            Remove-Item -Recurse -Force $target
        }
        Copy-Item -Recurse -Force $_.FullName $target

        # Verify BEFORE any receipt writes (preserves TIMELINE.jsonl hashes).
        $manifest = Join-Path $target "CASEFILE-MANIFEST.json"
        $mismatch = @()
        $missing = @()
        if (Test-Path $manifest) {
            try {
                $man = Get-Content $manifest -Raw | ConvertFrom-Json
                if ($man.items) {
                    foreach ($item in $man.items) {
                        if (-not $item.path -or -not $item.hash) { continue }
                        $art = Join-Path $target $item.path
                        if (-not (Test-Path $art)) {
                            Write-Warning "  missing artifact: $($item.path)"
                            $missing += $item.path
                            continue
                        }
                        if (Test-Sha256Match -Path $art -Expected $item.hash) {
                            $verified++
                        } else {
                            Write-Warning "  HASH MISMATCH: $($item.path)"
                            $mismatch += $item.path
                        }
                    }
                }
            } catch {
                Write-Warning "  manifest parse issue: $_"
            }
        }

        # v3: desktop receipts live outside CASEFILE TIMELINE so hashes stay valid
        $receipt = Join-Path $target "DESKTOP-RECEIPTS.jsonl"
        $receiptLine = @{
            ts     = (Get-Date).ToUniversalTime().ToString("o")
            event  = "sd_import"
            source = "flipper69-sync"
            ver    = $F69Version
            data   = @{
                source   = $SdRoot
                mismatch = $mismatch
                missing  = $missing
            }
        } | ConvertTo-Json -Compress
        Add-Content -Path $receipt -Value $receiptLine -Encoding UTF8

        $imported++
        Write-Host "[+] STORED $target" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "IMPORT COMPLETE  ops=$imported  hashes_ok=$verified" -ForegroundColor Magenta
    Write-Host "vault: $destOps" -ForegroundColor DarkGray
}

function Start-SerialExfil {
    param([string]$PortName, [string]$DestRoot, [switch]$Once)

    $port = New-Object System.IO.Ports.SerialPort $PortName, 115200, None, 8, one
    $port.NewLine = "`n"
    $port.ReadTimeout = 5000
    $port.Open()
    Write-Host "listening $PortName @ 115200 -> $DestRoot" -ForegroundColor DarkGray
    Write-Host "device: CASEFILE Ops -> [5] EXFIL TO DESKTOP" -ForegroundColor DarkGray
    Write-Host ""

    $currentOp = $null
    $opPath = $null
    $closed = 0

    try {
        while ($true) {
            try {
                $line = $port.ReadLine().Trim()
            } catch [System.TimeoutException] {
                continue
            }
            if (-not $line) { continue }
            if ($line -notmatch '^\s*\{') {
                Write-Host "  raw: $line" -ForegroundColor DarkGray
                continue
            }

            try {
                $msg = $line | ConvertFrom-Json
            } catch {
                Write-Warning "bad json: $line"
                continue
            }

            switch ($msg.type) {
                "op_header" {
                    $currentOp = $msg.opId
                    $opPath = Join-Path $DestRoot "operations" $currentOp
                    New-Item -ItemType Directory -Force -Path $opPath | Out-Null
                    New-Item -ItemType Directory -Force -Path (Join-Path $opPath "captures") | Out-Null

                    $op = @{
                        opId     = $currentOp
                        opType   = $msg.opType
                        phase    = $msg.phase
                        openedAt = (Get-Date).ToUniversalTime().ToString("o")
                        device   = @{ firmware = "flipper69"; version = $F69Version }
                        source   = "field_serial"
                    }
                    $op | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $opPath "OPERATION.json") -Encoding UTF8
                    Write-TimelineEntry -OpPath $opPath -Event "exfil_start" -Data @{ opType = $msg.opType }
                    Write-Host "[+] OP OPEN: $currentOp" -ForegroundColor Green
                }
                "manifest" {
                    if (-not $opPath) { continue }
                    $manifestPath = Join-Path $opPath "CASEFILE-MANIFEST.json"
                    $msg | ConvertTo-Json -Depth 10 | Set-Content $manifestPath -Encoding UTF8
                    Write-Host "[+] MANIFEST: $currentOp" -ForegroundColor Cyan
                }
                "artifact" {
                    if (-not $opPath) { continue }
                    $dest = Join-Path $opPath $msg.path
                    $destDir = Split-Path $dest -Parent
                    if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Force -Path $destDir | Out-Null }

                    if ($msg.b64) {
                        [IO.File]::WriteAllBytes($dest, [Convert]::FromBase64String($msg.b64))
                        if (-not (Test-Sha256Match -Path $dest -Expected $msg.sha256)) {
                            Write-Warning "HASH MISMATCH: $($msg.path)"
                            Write-TimelineEntry -OpPath $opPath -Event "hash_mismatch" -Data @{ path = $msg.path }
                        } else {
                            Write-Host "[+] ARTIFACT OK: $($msg.path)" -ForegroundColor Green
                        }
                    }
                }
                "op_close" {
                    if (-not $opPath) { continue }
                    $opFile = Join-Path $opPath "OPERATION.json"
                    $op = Get-Content $opFile | ConvertFrom-Json
                    $op.phase = "CLOSE"
                    $op | Add-Member -NotePropertyName closedAt -NotePropertyValue ((Get-Date).ToUniversalTime().ToString("o")) -Force
                    $op | Add-Member -NotePropertyName manifestHash -NotePropertyValue $msg.manifestHash -Force
                    $op | ConvertTo-Json -Depth 5 | Set-Content $opFile -Encoding UTF8
                    Write-TimelineEntry -OpPath $opPath -Event "exfil_complete" -Data @{ manifestHash = $msg.manifestHash }

                    $ack = @{
                        type        = "ack"
                        opId        = $currentOp
                        status      = "stored"
                        desktopPath = $opPath
                        ver         = $F69Version
                    } | ConvertTo-Json -Compress
                    $port.WriteLine($ack)

                    Write-Host "[+] OP CLOSED: $currentOp" -ForegroundColor Magenta
                    $currentOp = $null
                    $opPath = $null
                    $closed++
                    if ($Once) { break }
                }
                "ping" {
                    $pong = @{ type = "pong"; ver = $F69Version; ts = (Get-Date).ToUniversalTime().ToString("o") } | ConvertTo-Json -Compress
                    $port.WriteLine($pong)
                    Write-Host "[.] pong" -ForegroundColor DarkGray
                }
            }
        }
    } finally {
        if ($port.IsOpen) { $port.Close() }
        $port.Dispose()
        Write-Host "serial closed  ops_sealed=$closed" -ForegroundColor DarkGray
    }
}

# --- main ---
Write-Banner
New-Item -ItemType Directory -Force -Path (Join-Path $OpsRoot "operations") | Out-Null

if ($SdImport) {
    Write-Host "MODE: SD import" -ForegroundColor Yellow
    Import-SdTree -SdRoot $SdImport -DestRoot $OpsRoot
    exit 0
}

if (-not $ComPort) {
    $ComPort = Get-FlipperComPort
    if (-not $ComPort) {
        throw "No Flipper COM port found. Specify -ComPort or use -SdImport."
    }
}

Write-Host "MODE: USB serial" -ForegroundColor Yellow
Start-SerialExfil -PortName $ComPort -DestRoot $OpsRoot -Once:$Once
