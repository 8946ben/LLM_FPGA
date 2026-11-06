param(
    [string]$PythonExe = 'C:\Users\ben\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe',
    [string]$Xsct = 'G:\Xilinx\Vitis\2021.1\bin\xsct.bat',
    [string]$PackageDir
)
$ErrorActionPreference = 'Stop'
$moduleDir = Split-Path -Parent $PSScriptRoot
$repoDir = Split-Path -Parent $moduleDir
if (-not $PackageDir) { $PackageDir = Join-Path $moduleDir 'reports\board_package_20261009' }
$assetRoot = Join-Path $repoDir 'artifacts\module14_v2_assets'
$manifest = Get-Content -Raw -LiteralPath (Join-Path $assetRoot 'manifest.json') | ConvertFrom-Json
$golden = $manifest.trace | Where-Object { $_.step -eq 'step_00' }
$hidden = Join-Path $assetRoot 'trace\step_00\hidden.bf16.bin'
$history = Join-Path $assetRoot 'trace\step_00\history_bitmap.u32.bin'
foreach ($entry in @(@($hidden, $golden.hidden_sha256), @($history, $golden.history_sha256))) {
    if ((Get-FileHash -LiteralPath $entry[0] -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry[1]) {
        throw 'Failure regression input hash mismatch'
    }
}
$elf = Join-Path $PackageDir 'm14_v2_test.elf'
$elfEntry = Get-Content -LiteralPath (Join-Path $PackageDir 'ARTIFACTS.sha256') |
    Where-Object { $_ -match '^([0-9a-f]{64})  m14_v2_test\.elf$' }
if (@($elfEntry).Count -ne 1 -or
    (Get-FileHash -LiteralPath $elf -Algorithm SHA256).Hash.ToLowerInvariant() -ne $elfEntry.Substring(0,64)) {
    throw 'Failure regression ELF hash mismatch'
}
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss_fff'
$runDir = Join-Path $moduleDir "reports\board_runs\${stamp}_golden_failure"
New-Item -ItemType Directory -Path $runDir -Force | Out-Null
$mailboxInput = Join-Path $runDir 'mailbox_input.bin'
$dump = Join-Path $runDir 'mailbox_output.bin'
$decoded = Join-Path $runDir 'mailbox_decoded.json'
$log = Join-Path $runDir 'xsct.log'
$wrongCrc = [uint32]$golden.output_crc -bxor [uint32]1
& $PythonExe (Join-Path $PSScriptRoot 'prepare_mailbox.py') $mailboxInput `
    --expected-token $golden.selected_token --expected-crc $wrongCrc
if ($LASTEXITCODE -ne 0) { throw 'Failure regression mailbox generation failed' }
& $Xsct (Join-Path $PSScriptRoot 'scripts\run_step.tcl') $hidden $history $mailboxInput $elf $dump '-' 30 2>&1 |
    Tee-Object -FilePath $log
$exitCode = $LASTEXITCODE
$logText = Get-Content -Raw -LiteralPath $log
if ($exitCode -ne 0 -or $logText -match 'M14_BOARD_RUN_ERROR' -or $logText -notmatch 'M14_BOARD_RUN_STEP=PASS') {
    throw "Failure regression transport failed: $log"
}
& $PythonExe (Join-Path $PSScriptRoot 'parse_mailbox.py') $dump --step step_00 --json-output $decoded --package-dir $PackageDir
$parseExit = $LASTEXITCODE
$record = (Get-Content -Raw -LiteralPath $decoded | ConvertFrom-Json).records[0]
if ($parseExit -ne 1 -or $record.state -ne '0x4641494c' -or $record.driver_status -ne 7 -or
    $record.status_code -ne 0 -or $record.selected_token -ne $golden.selected_token -or
    $record.selected_score_bits -ne $golden.selected_score_bits -or $record.output_crc -ne $golden.output_crc -or
    $record.wall_ticks -le 0 -or $record.timer_counts_per_second -le 0 -or
    $record.perf_cycles_total -le 0 -or $record.weight_read_beats_128 -ne 17016832) {
    throw "Failure regression did not preserve the expected hardware result and positive elapsed time: $decoded"
}
Write-Output "M14_FAILURE_REGRESSION_DIR=$runDir"
Write-Output "M14_FAILURE_REGRESSION=PASS wall_ticks=$($record.wall_ticks) ip_cycles=$($record.perf_cycles_total)"
