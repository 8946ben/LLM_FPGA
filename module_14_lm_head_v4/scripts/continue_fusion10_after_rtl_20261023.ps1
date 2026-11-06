# One-shot dependency chain for this existing experiment, not a scheduler.
# No board/network operations; errors or STOP_REQUESTED end the chain.
param([switch]$Run,[int]$ExistingHlsPid=7696)
$ErrorActionPreference='Stop'
$taskModule=Split-Path -Parent $PSScriptRoot
$taskRoot=Split-Path -Parent $taskModule
$taskR=Join-Path $taskModule 'reports/fusion_exp10_20261023_r1'
$taskPython='C:/Users/ben/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
if(-not $Run){'PREPARED_ONLY; -Run observes existing CoSim then sequentially qualifies/builds offline';return}
$taskState=Join-Path $taskR 'OFFLINE_WORKFLOW.json'
if(Test-Path -LiteralPath $taskState){throw 'Inspect existing workflow; never launch a duplicate'}
function Check-Exp10Stop {if(Test-Path -LiteralPath (Join-Path $taskR 'STOP_REQUESTED')){throw 'User stop marker; no following phase'}}
function Save-Exp10Workflow([string]$Stage,[string]$Detail){
 @{stage=$Stage;detail=$Detail;updated=(Get-Date -Format o);pid=$PID;observed_hls_pid=$ExistingHlsPid;board='NOT_RUN';quality='QUALITY_FAIL_NO_RELEASE_NO_RETUNE';scope='One-shot local offline dependency chain, no new studies/quality evaluation or board jobs'} | ConvertTo-Json | Set-Content -LiteralPath $taskState -Encoding utf8
}
try {
 Check-Exp10Stop
 $taskProcess=Get-CimInstance Win32_Process -Filter "ProcessId=$ExistingHlsPid"
 $taskCreated=$null
 if($taskProcess){
   if($taskProcess.Name -ne 'vitis_hls.exe' -or $taskProcess.CommandLine -notmatch 'cosim_short\.tcl'){throw 'PID does not identify this existing Exp10 HLS run'}
   $taskCreated=$taskProcess.CreationDate
 }
 Save-Exp10Workflow 'WAITING_EXISTING_RTL' 'Only observing existing short-path HLS; no restart. Completion requires actual report/full strict compare, not process existence.'
 while($taskProcess -and $taskProcess.CreationDate -eq $taskCreated){
   Check-Exp10Stop
   Start-Sleep -Seconds 5
   $taskProcess=Get-CimInstance Win32_Process -Filter "ProcessId=$ExistingHlsPid"
 }
 Check-Exp10Stop
 $taskLog=Get-Content -LiteralPath (Join-Path $taskR 'hls_exp10_cosim_r2_short.log') -Raw -Encoding utf8
 if($taskLog -notmatch 'C/RTL co-simulation finished: PASS' -or $taskLog -notmatch 'EXP10_SHORT_COSIM=PASS'){throw 'Existing HLS ended without genuine CoSim PASS; preserve failure and stop'}
 Save-Exp10Workflow 'FULL_RTL_TRACE_QUALIFICATION' 'All41943040 memory values/18 scalars and official C postcheck, no resimulation'
 & $taskPython -X utf8 (Join-Path $PSScriptRoot 'qualify_fusion10_rtl_20261023.py') *> (Join-Path $taskR 'rtl_full_trace_qualification.log')
 if($LASTEXITCODE -ne 0){throw 'Full RTL qualification failed'}
 Check-Exp10Stop
 Save-Exp10Workflow 'SEQUENTIAL_OFFLINE_ENGINEERING' 'Qualified RTL, now export→full200MHz system→matching BSP/ELFs→research-only binding; quality failure retained'
 & (Join-Path $PSScriptRoot 'finish_fusion10_offline_20261023.ps1') -Run
 if($LASTEXITCODE -ne 0){throw 'Sequential offline engineering failed'}
 Check-Exp10Stop
 Save-Exp10Workflow 'FINAL_ARTIFACT_REVIEW_AND_DOCUMENTATION' 'Review actual complete products before publishing final state'
 & $taskPython -X utf8 (Join-Path $PSScriptRoot 'finalize_fusion10_offline_20261023.py') *> (Join-Path $taskR 'final_artifact_review.log')
 if($LASTEXITCODE -ne 0){throw 'Final artifact review failed'}
 & $taskPython -X utf8 (Join-Path $taskRoot 'tools/sync_v4_fusion10_20261023.py') *> (Join-Path $taskR 'final_page_sync.log')
 if($LASTEXITCODE -ne 0){throw 'Result page generation failed'}
 & $taskPython -X utf8 (Join-Path $taskRoot 'tools/check_v4_validation_page_20261022.py') *> (Join-Path $taskR 'final_page_check.log')
 if($LASTEXITCODE -ne 0){throw 'Result page static data/link/JavaScript check failed'}
 Save-Exp10Workflow 'COMPLETE_OFFLINE_QUALITY_FAILED_NOT_RELEASE' 'Offline chain and artifact/page checks complete; no automatic new experiment or board action'
 'EXP10_OFFLINE_WORKFLOW=COMPLETE_QUALITY_FAILED_NOT_RELEASE; BOARD_NOT_RUN'
} catch {
 Save-Exp10Workflow 'STOPPED_ON_ERROR_OR_USER_PAUSE' $_.Exception.Message
 throw
}
