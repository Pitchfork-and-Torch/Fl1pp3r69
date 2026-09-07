<#
.SYNOPSIS
    Create a Fl1pp3r69 v2 field operation on SD card layout (desktop simulation).
.PARAMETER OpType
    proximity | survey | replay | inject | unified
.PARAMETER Label
    Human label used in opId slug
.PARAMETER Pathnum
    Speed profile: imps | ds | slow | fast | emerg
.PARAMETER SdRoot
    Simulated SD root (default: examples/sd_card)
#>
param(
    [Parameter(Mandatory)]
    [ValidateSet("proximity", "survey", "replay", "inject", "unified")]
    [string]$OpType,
    [string]$Label = "field-test",
    [ValidateSet("imps", "ds", "slow", "fast", "emerg")]
    [string]$Pathnum = "ds",
    [string]$SdRoot
)

$ErrorActionPreference = "Stop"
$F69Version = "2.0.0"

if (-not $SdRoot) {
    $here = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
    if (-not $here) { $here = (Get-Location).Path }
    $SdRoot = Join-Path (Split-Path -Parent $here) "examples\sd_card"
}

$date = Get-Date -Format "yyyyMMdd"
$slug = $Label.ToLower() -replace '[^a-z0-9]+', '-'
$codename = "sim_$slug"
$salt = "{0:x8}" -f (Get-Random -Maximum 0x7fffffff)
$opId = "op-$date-$codename-$salt"

$opPath = Join-Path $SdRoot "flipper69\operations\$opId"
New-Item -ItemType Directory -Force -Path (Join-Path $opPath "captures") | Out-Null

$openedAt = (Get-Date).ToUniversalTime().ToString("o")
$pathnumInt = switch ($Pathnum) {
    "imps"  { 1 }
    "ds"    { 2 }
    "slow"  { 3 }
    "fast"  { 4 }
    "emerg" { 5 }
    default { 2 }
}

$op = [ordered]@{
    opId         = $opId
    codename     = $codename
    workspace    = ".f69_sim"
    opType       = $OpType
    pathnum      = $pathnumInt
    pathLabel    = $Pathnum
    phase        = "OP_PREP"
    openedAt     = $openedAt
    device       = @{
        firmware = "flipper69"
        version  = $F69Version
        codename = "FL1PP3R69"
        serial   = "DEV-SIM"
        region   = "US"
    }
    target       = @{
        label      = $Label
        notes      = "Simulated field op for manifest testing"
        authorized = $true
    }
    permissions  = @{
        opsec           = $true
        authorized      = $true
        txEnabled       = $false
        replayConfirmed = $false
    }
    captureCount = 0
    manifestHash = $null
}

$op | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $opPath "OPERATION.json") -Encoding UTF8

$notes = @"
# $codename
# FL1PP3R69 // $F69Version
# path: $Pathnum
# type: $OpType
"@
Set-Content (Join-Path $opPath "notes.txt") -Value $notes -Encoding UTF8

$timeline = @(
    (@{ ts = $openedAt; ver = $F69Version; event = "INTAKE"; detail = $codename } | ConvertTo-Json -Compress),
    (@{ ts = $openedAt; ver = $F69Version; event = "OP_PREP"; detail = $Pathnum } | ConvertTo-Json -Compress)
)
Set-Content (Join-Path $opPath "TIMELINE.jsonl") -Value $timeline -Encoding UTF8

# update index
$root = Join-Path $SdRoot "flipper69"
New-Item -ItemType Directory -Force -Path $root | Out-Null
$opsDir = Join-Path $root "operations"
$ops = @()
if (Test-Path $opsDir) {
    $ops = @(Get-ChildItem $opsDir -Directory | Where-Object { $_.Name -like "op-*" } | ForEach-Object { $_.Name })
}
$index = @{
    firmware   = "flipper69"
    version    = $F69Version
    updatedAt  = $openedAt
    operations = $ops
}
$index | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $root "index.json") -Encoding UTF8

Write-Host ""
Write-Host "FL1PP3R69 // Created $opId" -ForegroundColor Red
Write-Host "  type=$OpType  path=$Pathnum  ver=$F69Version" -ForegroundColor DarkGray
Write-Host "  $opPath" -ForegroundColor DarkGray
Write-Output $opId
