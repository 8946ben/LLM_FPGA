param(
    [ValidateSet("bad_abi", "bad_flags", "bad_dimension", "numeric_error")]
    [string]$Test,
    [string]$Xsct = "G:\Xilinx\Vitis\2021.1\bin\xsct.bat",
    [string]$PythonExe = $env:PYTHON,
    [string]$PackageDir
)

$ErrorActionPreference = "Stop"
$stopFile = Join-Path (Split-Path -Parent $PSScriptRoot) 'reports\board_runs\STOP_REQUESTED'
if (Test-Path -LiteralPath $stopFile) {
    throw 'M14_STOP_REQUESTED: user requested a pause before the next board phase'
}
if (-not $PythonExe) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) { $PythonExe = $pythonCommand.Source }
}
if (-not $PythonExe -or -not (Test-Path -LiteralPath $PythonExe)) {
    throw "Python not found; pass -PythonExe or set PYTHON"
}

$standaloneDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$moduleDir = Split-Path -Parent $standaloneDir
$repoDir = Split-Path -Parent $moduleDir
$traceDir = Join-Path $repoDir "artifacts\module14_v2_assets\trace\step_00"
$hidden = Join-Path $traceDir "hidden.bf16.bin"
$history = Join-Path $traceDir "history_bitmap.u32.bin"
if (-not $PackageDir) { $PackageDir = Join-Path $moduleDir 'reports\board_package_20261009' }
$elf = Join-Path $PackageDir 'm14_v2_test.elf'
$tcl = Join-Path $standaloneDir "scripts\run_step.tcl"
foreach ($path in @($Xsct, $hidden, $history, $elf, $tcl)) {
    if (-not (Test-Path -LiteralPath $path)) { throw "Missing board input: $path" }
}
$elfHashEntry = Get-Content -LiteralPath (Join-Path $PackageDir 'ARTIFACTS.sha256') |
    Where-Object { $_ -match '^([0-9a-f]{64})  m14_v2_test\.elf$' }
if (@($elfHashEntry).Count -ne 1 -or
    (Get-FileHash -LiteralPath $elf -Algorithm SHA256).Hash.ToLowerInvariant() -ne $elfHashEntry.Substring(0, 64)) {
    throw 'ELF package hash mismatch'
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss_fff"
$runDir = Join-Path $moduleDir "reports\board_runs\${stamp}_$Test"
New-Item -ItemType Directory -Path $runDir -Force | Out-Null
$mailbox = Join-Path $runDir "mailbox_input.bin"
$mailboxDump = Join-Path $runDir "mailbox_output.bin"
$log = Join-Path $runDir "xsct.log"
$results = Join-Path $moduleDir "reports\board_runs\negative_results.json"

$caseArgs = switch ($Test) {
    "bad_abi"       { @("--abi-version", "1", "--expected-status", "1") }
    "bad_flags"     { @("--flags", "0x80000000", "--expected-status", "11") }
    "bad_dimension" { @("--valid-rows", "2", "--expected-status", "2") }
    "numeric_error" { @("--penalty", "0.5", "--expected-status", "9") }
}
$mailboxArgs = @(
    (Join-Path $standaloneDir "prepare_mailbox.py"), $mailbox,
    "--expected-token", "0", "--bypass-host-validation"
) + $caseArgs
& $PythonExe @mailboxArgs
if ($LASTEXITCODE -ne 0) { throw "Negative mailbox generation failed" }

& $Xsct $tcl $hidden $history $mailbox $elf $mailboxDump "-" 10 2>&1 |
    Tee-Object -FilePath $log
$xsctExit = $LASTEXITCODE
$logText = Get-Content -Raw $log
if ($xsctExit -ne 0 -or $logText -match 'M14_BOARD_RUN_ERROR' -or
    $logText -notmatch 'M14_BOARD_RUN_STEP=PASS') {
    throw "Negative board run failed with exit code $LASTEXITCODE; log=$log"
}

& $PythonExe (Join-Path $standaloneDir "parse_mailbox.py") $mailboxDump `
    --step $Test --json-output $results --append --package-dir $PackageDir
if ($LASTEXITCODE -ne 0) { throw "Negative mailbox result check failed" }
Write-Output "M14_BOARD_NEGATIVE_DIR=$runDir"
Write-Output "M14_BOARD_NEGATIVE=PASS test=$Test"
