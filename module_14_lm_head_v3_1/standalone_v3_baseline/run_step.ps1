param(
    [ValidatePattern('^step_0[0-7]$')]
    [string]$Step,
    [switch]$WriteLogits,
    [ValidateRange(1, 1000)]
    [int]$RepeatCount = 1,
    [ValidateRange(1, 600)]
    [int]$TimeoutSeconds = 30,
    [string]$Xsct = "G:\Xilinx\Vitis\2021.1\bin\xsct.bat",
    [string]$PythonExe = $env:PYTHON,
    [string]$PackageDir
)

$ErrorActionPreference = "Stop"
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
$assetRoot = Join-Path $repoDir "artifacts\module14_v2_assets"
$traceDir = Join-Path $assetRoot "trace\$Step"
$manifestPath = Join-Path $assetRoot "manifest.json"
$manifest = Get-Content -Raw $manifestPath | ConvertFrom-Json
$golden = $manifest.trace | Where-Object { $_.step -eq $Step }
if (-not $golden) { throw "Step is missing from manifest: $Step" }

$hidden = Join-Path $traceDir "hidden.bf16.bin"
$history = Join-Path $traceDir "history_bitmap.u32.bin"
if (-not $PackageDir) { $PackageDir = Join-Path $moduleDir 'reports\board_package_20261009' }
$elf = Join-Path $PackageDir 'm14_v2_test.elf'
$tcl = Join-Path $standaloneDir "scripts\run_step.tcl"
foreach ($path in @($Xsct, $hidden, $history, $elf, $tcl)) {
    if (-not (Test-Path -LiteralPath $path)) { throw "Missing board input: $path" }
}
$hashManifest = Join-Path $PackageDir 'ARTIFACTS.sha256'
$elfHashEntry = Get-Content -LiteralPath $hashManifest | Where-Object { $_ -match '^([0-9a-f]{64})  m14_v2_test\.elf$' }
if (@($elfHashEntry).Count -ne 1 -or
    (Get-FileHash -LiteralPath $elf -Algorithm SHA256).Hash.ToLowerInvariant() -ne $elfHashEntry.Substring(0, 64)) {
    throw 'ELF package hash mismatch'
}
if ((Get-FileHash $hidden -Algorithm SHA256).Hash.ToLowerInvariant() -ne $golden.hidden_sha256) {
    throw "$Step hidden hash mismatch"
}
if ((Get-FileHash $history -Algorithm SHA256).Hash.ToLowerInvariant() -ne $golden.history_sha256) {
    throw "$Step history hash mismatch"
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss_fff"
$runDir = Join-Path $moduleDir "reports\board_runs\${stamp}_$Step"
New-Item -ItemType Directory -Path $runDir -Force | Out-Null
$mailbox = Join-Path $runDir "mailbox_input.bin"
$mailboxDump = Join-Path $runDir "mailbox_output.bin"
$logitsDump = if ($WriteLogits) { Join-Path $runDir "raw_logits.fp32.bin" } else { "-" }
$log = Join-Path $runDir "xsct.log"
$results = Join-Path $moduleDir "reports\board_runs\results.json"

$mailboxArgs = @(
    (Join-Path $standaloneDir "prepare_mailbox.py"), $mailbox,
    "--expected-token", [string]$golden.selected_token,
    "--expected-crc", [string]$golden.output_crc,
    "--repeat-count", [string]$RepeatCount,
    "--write-logits", $(if ($WriteLogits) { "1" } else { "0" })
)
& $PythonExe @mailboxArgs
if ($LASTEXITCODE -ne 0) { throw "Mailbox generation failed" }

& $Xsct $tcl $hidden $history $mailbox $elf $mailboxDump $logitsDump $TimeoutSeconds 2>&1 |
    Tee-Object -FilePath $log
$xsctExit = $LASTEXITCODE
$logText = Get-Content -Raw $log
$transportFailure = $null
$logitsFailure = $null
if ($xsctExit -ne 0 -or $logText -match 'M14_BOARD_RUN_ERROR' -or
    $logText -notmatch 'M14_BOARD_RUN_STEP=PASS') {
    $transportFailure = "Board step failed with exit code $xsctExit; log=$log"
}

$parseExit = 2
if (Test-Path -LiteralPath $mailboxDump) {
    # Persist the mailbox before reporting any transport, numerical, or hash
    # failure. parse_mailbox deliberately writes failed records before exit 1.
    $decoded = Join-Path $runDir "mailbox_decoded.json"
    & $PythonExe (Join-Path $standaloneDir "parse_mailbox.py") $mailboxDump `
        --step $Step --json-output $decoded --package-dir $PackageDir
    $parseExit = $LASTEXITCODE
    if (Test-Path -LiteralPath $decoded) {
        & $PythonExe (Join-Path $standaloneDir "parse_mailbox.py") $mailboxDump `
            --step $Step --json-output $results --append --package-dir $PackageDir
        if ($LASTEXITCODE -ne $parseExit) { throw "Mailbox parse results disagree" }
    }
}

if ($WriteLogits -and (Test-Path -LiteralPath $logitsDump)) {
    $actualLogitsHash = (Get-FileHash $logitsDump -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualLogitsHash -ne $golden.raw_logits_sha256) {
        $logitsFailure = "$Step raw logits hash mismatch: $actualLogitsHash"
    }
} elseif ($WriteLogits) {
    $logitsFailure = "$Step raw logits dump missing"
}

Write-Output "M14_BOARD_STEP_DIR=$runDir"
$failures = @()
if ($transportFailure) { $failures += $transportFailure }
if ($parseExit -ne 0) { $failures += "Mailbox result check failed (exit=$parseExit)" }
if ($logitsFailure) { $failures += $logitsFailure }
if ($failures.Count -gt 0) {
    throw ($failures -join "; ")
}
Write-Output "M14_BOARD_STEP=PASS step=$Step"
