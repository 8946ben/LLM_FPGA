param(
    [string]$Xsct = "G:\Xilinx\Vitis\2021.1\bin\xsct.bat",
    [string]$PackageDir
)

$ErrorActionPreference = "Stop"
$standaloneDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$moduleDir = Split-Path -Parent $standaloneDir
$repoDir = Split-Path -Parent $moduleDir
if (-not $PackageDir) { $PackageDir = Join-Path $moduleDir 'reports\board_package_20261009' }
$packageDir = $PackageDir
$bit = Join-Path $packageDir "m14_v2_system_wrapper.bit"
$psuInit = Join-Path $standaloneDir "workspace\m14_v2_platform\hw\psu_init.tcl"
$weight = Join-Path $repoDir "artifacts\module14_v2_assets\shared_vocab_weight.bf16.bin"
$manifest = Get-Content -Raw (Join-Path $repoDir "artifacts\module14_v2_assets\manifest.json") | ConvertFrom-Json
$tcl = Join-Path $standaloneDir "scripts\program_and_load.tcl"
$runRoot = Join-Path $moduleDir "reports\board_runs"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$log = Join-Path $runRoot "${stamp}_program_and_load.log"

foreach ($path in @($Xsct, $bit, $psuInit, $weight, $tcl)) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Required board input is missing: $path"
    }
}
New-Item -ItemType Directory -Path $runRoot -Force | Out-Null

$packageHashes = @{}
Get-Content (Join-Path $packageDir "ARTIFACTS.sha256") | ForEach-Object {
    if ($_ -match '^([0-9a-f]{64})  (.+)$') {
        $packageHashes[$Matches[2]] = $Matches[1]
    }
}
$actualBitHash = (Get-FileHash -LiteralPath $bit -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualBitHash -ne $packageHashes[[IO.Path]::GetFileName($bit)]) {
    throw "Bitstream hash mismatch"
}
$actualWeightHash = (Get-FileHash -LiteralPath $weight -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualWeightHash -ne $manifest.weight_sha256) {
    throw "BF16 weight hash mismatch"
}

& $Xsct $tcl $bit $psuInit $weight 2>&1 | Tee-Object -FilePath $log
$xsctExit = $LASTEXITCODE
$logText = Get-Content -Raw $log
if ($xsctExit -ne 0 -or $logText -match 'M14_BOARD_PROGRAM_ERROR' -or
    $logText -notmatch 'M14_BOARD_PROGRAM_AND_LOAD=PASS') {
    throw "Board program/load failed with exit code $xsctExit; log=$log"
}
Write-Output "M14_BOARD_PROGRAM_LOG=$log"
Write-Output "M14_BOARD_PROGRAM=PASS"
