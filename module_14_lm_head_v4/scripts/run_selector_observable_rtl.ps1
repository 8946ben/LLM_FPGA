$ErrorActionPreference='Stop'
$taskModule=Split-Path -Parent $PSScriptRoot
$taskSim=Join-Path $taskModule 'build/selector_full_cosim_r2/hls/solution1/sim'
$taskReports=Join-Path $taskModule 'reports'
$taskEda=@(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -in @('vivado.exe','xsim.exe','xsimk.exe','xelab.exe','vitis_hls.exe')
})
if($taskEda.Count){throw 'Preserve other EDA work and host memory; do not run concurrently'}
$taskXsimLog=Join-Path $taskReports 'selector_repaired_xsim_r5_20261021.log'
$taskPostLog=Join-Path $taskReports 'selector_repaired_postcheck_r2_20261021.log'
if((Test-Path -LiteralPath $taskXsimLog) -or (Test-Path -LiteralPath $taskPostLog)){throw 'Preserve existing logs'}
if(Test-Path -LiteralPath (Join-Path $taskSim 'verilog/lm_head_v4_selector.performance.result.transaction.xml')){throw 'Preserve prior completed transaction evidence; qualify existing r5 outputs instead of rerunning'}
Push-Location (Join-Path $taskSim 'verilog')
try {
    # Reuse the already compiled O3 snapshot; no re-elaboration or RTL changes.
    $taskTcl=(Join-Path $taskModule 'experiments/board_v4_20261021/selector_progress_r4.tcl').Replace('\','/')
    & 'G:/Xilinx/Vivado/2021.1/bin/xsim.bat' --noieeewarnings lm_head_v4_selector_o3 -tclbatch $taskTcl *> $taskXsimLog
    if($LASTEXITCODE -ne 0){throw 'Observable XSim failed; inspect preserved log'}
} finally {Pop-Location}
$taskPython='C:/Users/ben/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $taskPython -X utf8 (Join-Path $PSScriptRoot 'check_selector_rtl_traces.py') *> (Join-Path $taskReports 'selector_rtl_trace_audit_20261021.log')
if($LASTEXITCODE -ne 0){throw 'Full RTL trace comparison failed'}
$env:PATH='G:/Xilinx/Vitis_HLS/2021.1/tps/win64/msys64/mingw64/bin;G:/Xilinx/Vitis_HLS/2021.1/tps/win64/msys64/usr/bin;'+$env:PATH
Push-Location (Join-Path $taskSim 'wrapc_pc')
try {
    & .\cosim.pc.exe $taskModule --rtl *> $taskPostLog
    $taskPostExit=$LASTEXITCODE
    ('SELECTOR_REPAIRED_POSTCHECK_EXIT='+$taskPostExit) | Add-Content -LiteralPath $taskPostLog
    if($taskPostExit -ne 0){throw 'Original C postcheck failed'}
} finally {Pop-Location}
& $taskPython -X utf8 (Join-Path $PSScriptRoot 'collect_selector_integration.py') --repaired *> (Join-Path $taskReports 'selector_integration_collect_20261021.log')
if($LASTEXITCODE -ne 0){throw 'Integrated selector evidence audit failed'}
'SELECTOR_REPAIRED_RTL_SEQUENCE=PASS XSim+full_trace+original_C_postcheck; NOT_BOARD'
