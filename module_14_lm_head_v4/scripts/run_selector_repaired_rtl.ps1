$ErrorActionPreference='Stop'
$taskModule=Split-Path -Parent $PSScriptRoot
$taskSim=Join-Path $taskModule 'build/selector_full_cosim_r2/hls/solution1/sim'
$taskReports=Join-Path $taskModule 'reports'
$taskVivado=@(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq 'vivado.exe' -and ($_.CommandLine -like '*board_v4_20261021/build_resume_r2.tcl*' -or $_.CommandLine -like '*m14_v4_system_wrapper.vdi*')
})
if($taskVivado.Count){throw 'Finish own Vivado run first; avoid16GiB memory pressure'}
$taskXsimLog=Join-Path $taskReports 'selector_repaired_xsim_r3_20261021.log'
$taskPostLog=Join-Path $taskReports 'selector_repaired_postcheck_r2_20261021.log'
if((Test-Path -LiteralPath $taskXsimLog) -or (Test-Path -LiteralPath $taskPostLog)){throw 'Preserve existing run logs'}
Push-Location (Join-Path $taskSim 'verilog')
try {
    & cmd.exe /d /c run_xsim_optimized.bat *> $taskXsimLog
    if($LASTEXITCODE -ne 0){throw 'Generated XSim runner failed; inspect log, no acceptance'}
} finally {Pop-Location}
$taskPython='C:/Users/ben/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $taskPython -X utf8 (Join-Path $PSScriptRoot 'check_selector_rtl_traces.py') *> (Join-Path $taskReports 'selector_rtl_trace_audit_20261021.log')
if($LASTEXITCODE -ne 0){throw 'Full RTL trace comparison failed; do not publish result'}
$env:PATH='G:/Xilinx/Vitis_HLS/2021.1/tps/win64/msys64/mingw64/bin;G:/Xilinx/Vitis_HLS/2021.1/tps/win64/msys64/usr/bin;'+$env:PATH
Push-Location (Join-Path $taskSim 'wrapc_pc')
try {
    & .\cosim.pc.exe $taskModule --rtl *> $taskPostLog
    $taskPostExit=$LASTEXITCODE
    ('SELECTOR_REPAIRED_POSTCHECK_EXIT='+$taskPostExit) | Add-Content -LiteralPath $taskPostLog
    if($taskPostExit -ne 0){throw 'Original C postcheck failed; inspect log'}
} finally {Pop-Location}
& $taskPython -X utf8 (Join-Path $PSScriptRoot 'collect_selector_integration.py') --repaired *> (Join-Path $taskReports 'selector_integration_collect_20261021.log')
if($LASTEXITCODE -ne 0){throw 'Integrated selector evidence audit failed'}
'SELECTOR_REPAIRED_RTL_SEQUENCE=PASS XSim+full_trace+original_C_postcheck; NOT_BOARD'
