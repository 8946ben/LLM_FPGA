param([Parameter(Mandatory=$true)][ValidateSet('csim','csynth')][string]$Phase)
$ErrorActionPreference = 'Stop'
$modulePath = Split-Path -Parent $PSScriptRoot
$projectPath = Split-Path -Parent $modulePath
$reportPath = Join-Path $modulePath 'reports/partial_hw_20261024_r1'
$entryPath = Join-Path $modulePath 'experiments/partial_hw_20261024/proto.tcl'
$toolPath = 'G:/Xilinx/Vitis_HLS/2021.1/bin/vitis_hls.bat'
$phasePath = Join-Path $reportPath ($Phase + '_WORKFLOW.json')
$logPath = Join-Path $reportPath ($Phase + '.log')
if (Test-Path -LiteralPath $phasePath) { throw 'Preserve prior workflow; do not silently restart.' }
if (Test-Path -LiteralPath (Join-Path $reportPath 'STOP_REQUESTED')) { throw 'Stop requested.' }
if (-not (Test-Path -LiteralPath $toolPath)) { throw 'HLS tool missing.' }
$plan = Get-Content -LiteralPath (Join-Path $reportPath 'PLAN.json') -Raw | ConvertFrom-Json
foreach ($property in $plan.source_sha256.PSObject.Properties) {
    $actual = (Get-FileHash -LiteralPath (Join-Path $projectPath $property.Name) -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $property.Value) { throw ('Frozen source changed: ' + $property.Name) }
}
if ($Phase -eq 'csynth') {
    $qualification = Get-Content -LiteralPath (Join-Path $reportPath 'CSIM_QUALIFICATION.json') -Raw | ConvertFrom-Json
    if ($qualification.state -ne 'PASS_FULL_CSIM_ARRAYS') { throw 'Independent Csim qualification required before synthesis.' }
}
$eda = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(vivado|vivado_hls|vitis_hls|xsim|xelab)\.exe$' } | Select-Object ProcessId,CreationDate,Name,CommandLine)
if ($eda.Count -ne 0) { throw 'Another heavy EDA process exists; preserve it and defer this run.' }
$os = Get-CimInstance Win32_OperatingSystem
if ([long]$os.FreePhysicalMemory -lt 3GB/1KB) { throw 'Need at least3GiB free physical memory before heavy EDA.' }
$workflow = [ordered]@{ phase=$Phase; state='EXECUTING'; started=(Get-Date).ToString('o'); parent_pid=$PID;
    parent_creation=(Get-Process -Id $PID).StartTime.ToString('o'); source_plan_sha256=(Get-FileHash -LiteralPath (Join-Path $reportPath 'PLAN.json')).Hash;
    runner_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash; free_physical_kib=$os.FreePhysicalMemory; log=$logPath;
    command=@($toolPath,'-f',$entryPath); board='NOT_RUN'; automatic_next_stage=$false }
$lockPath = Join-Path $reportPath 'ACTIVE.lock'
if (Test-Path -LiteralPath $lockPath) { throw 'Another owning workflow lock exists.' }
$workflow | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $phasePath -Encoding utf8
$workflow | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $lockPath -Encoding utf8
$previousMode = $env:PARTIAL_PROTO_MODE
try {
    $env:PARTIAL_PROTO_MODE = $Phase
    & $toolPath -f $entryPath *> $logPath
    $workflow['wrapper_exit_code']=$LASTEXITCODE
    $log = Get-Content -LiteralPath $logPath -Raw
    if ($log -notmatch ('PARTIAL_PROTO_' + $Phase + '=PASS')) { throw 'Tool/Tcl completion marker missing; wrapper exit code alone is not a PASS.' }
    if ($Phase -eq 'csim' -and $log -notmatch 'PARTIAL_PROTO_CSIM_ALL_PASS valid=11 unique=9 negative=6') { throw 'Csim full testbench marker missing.' }
    $workflow.state='TOOL_COMPLETE_AWAITING_INDEPENDENT_REVIEW'
} catch {
    $workflow.state='FAILED_NO_AUTOMATIC_RETRY'; $workflow['error']=$_.Exception.Message
    throw
} finally {
    $workflow['finished']=(Get-Date).ToString('o')
    $workflow | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $phasePath -Encoding utf8
    if (Test-Path -LiteralPath $lockPath) { Remove-Item -LiteralPath $lockPath }
    if ($null -eq $previousMode) { Remove-Item -LiteralPath 'Env:PARTIAL_PROTO_MODE' -ErrorAction SilentlyContinue } else { $env:PARTIAL_PROTO_MODE=$previousMode }
}
