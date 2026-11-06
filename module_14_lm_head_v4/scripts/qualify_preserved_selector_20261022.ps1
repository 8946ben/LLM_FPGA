param([ValidatePattern('^[a-zA-Z0-9_]+$')][string]$Attempt='r1')
# No simulation, board connection or asynchronous continuation is launched here.
$ErrorActionPreference='Stop'
$taskModule=Split-Path -Parent $PSScriptRoot
$taskReports=Join-Path $taskModule 'reports'
$taskStatePath=Join-Path $taskReports 'OFFLINE_SEQUENCE_20261022.json'
function Save-QualificationState([string]$Stage,[string]$Detail){
    @{stage=$Stage;detail=$Detail;updated=(Get-Date -Format o);pid=$PID;board='NOT_RUN';
      scope='Offline preserved RTL qualification only; no simulation/board/new background worker'} |
        ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $taskStatePath -Encoding utf8
}
$taskAuditLog=Join-Path $taskReports ('selector_rtl_trace_audit_recovery_20261022_'+$Attempt+'.log')
$taskPostLog=Join-Path $taskReports 'selector_repaired_postcheck_r2_20261021.log'
$taskCollect=Join-Path $taskReports 'selector_integration_collect_20261021.log'
foreach($taskLog in @($taskAuditLog,$taskPostLog,$taskCollect)){
    if(Test-Path -LiteralPath $taskLog){throw "Preserve existing qualification attempt: $taskLog"}
}
try {
    Save-QualificationState 'QUALIFYING_PRESERVED_RTL' 'Full checkpoint SHA, genuine testbench finish, all41943040 memory values and18 scalars; no rerun'
    $taskPython='C:/Users/ben/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
    & $taskPython -X utf8 (Join-Path $PSScriptRoot 'check_selector_rtl_traces.py') --recover-preserved *> $taskAuditLog
    if($LASTEXITCODE -ne 0){throw 'Full preserved trace audit failed; inspect preserved log'}
    Save-QualificationState 'ORIGINAL_C_POSTCHECK' 'Full RTL memory/scalar comparison PASS; running original generated C postcheck'
    $env:PATH='G:/Xilinx/Vitis_HLS/2021.1/tps/win64/msys64/mingw64/bin;G:/Xilinx/Vitis_HLS/2021.1/tps/win64/msys64/usr/bin;'+$env:PATH
    Push-Location (Join-Path $taskModule 'build/selector_full_cosim_r2/hls/solution1/sim/wrapc_pc')
    try {
        & .\cosim.pc.exe $taskModule --rtl *> $taskPostLog
        $taskPostExit=$LASTEXITCODE
        ('SELECTOR_REPAIRED_POSTCHECK_EXIT='+$taskPostExit) | Add-Content -LiteralPath $taskPostLog
        if($taskPostExit -ne 0){throw 'Original C postcheck failed'}
    } finally {Pop-Location}
    & $taskPython -X utf8 (Join-Path $PSScriptRoot 'collect_selector_integration.py') --repaired *> $taskCollect
    if($LASTEXITCODE -ne 0){throw 'Integrated evidence collection failed'}
    Save-QualificationState 'PASS_RTL_QUALIFICATION_PS_NOT_STARTED' 'Full preserved RTL compare and original C postcheck PASS; BSP/ELF/package remain sequential next step'
    'SELECTOR_PRESERVED_QUALIFICATION=PASS; NOT_BOARD'
} catch {
    Save-QualificationState 'STOPPED_QUALIFICATION_FAILED' $_.Exception.Message
    throw
}
