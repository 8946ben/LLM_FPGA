param([switch]$Run,[string]$Python='C:/Users/ben/AppData/Local/Programs/Python/Python312/python.exe')
# One finite, authorized CPU/GPU sequence. No watcher, heartbeat, retry or EDA/board stage.
$ErrorActionPreference='Stop'
$studyModule=Split-Path -Parent $PSScriptRoot
$studyReport=Join-Path $studyModule 'reports/quantization_20261023_r1'
$studyState=Join-Path $studyReport 'QUALITY_SEQUENCE.json'
if(-not $Run){'V4B_QUALITY_SEQUENCE=PREPARED_ONLY';return}
if(-not(Test-Path -LiteralPath (Join-Path $studyReport 'METHODS_CALIBRATION.json'))){throw 'Finish the bounded method study before sequence'}
if(Test-Path -LiteralPath $studyState){throw 'Existing sequence retained; inspect it rather than starting a duplicate'}
if(Test-Path -LiteralPath (Join-Path $studyReport 'ACTIVE.lock')){throw 'Another study phase owns ACTIVE.lock'}
function Save-StudyState([string]$Stage,[string]$Detail){
    @{stage=$Stage;detail=$Detail;parent_pid=$PID;parent_started=(Get-Process -Id $PID).StartTime.ToString('o');
      updated=(Get-Date -Format o);scope='One finite local CPU/GPU sequence; no EDA, no FPGA, no retry';board='NOT_RUN'} |
      ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $studyState -Encoding utf8
}
try{
    foreach($studyStep in @(
      @('review_refine.py','independent_review_final.log'),
      @('benchmark_packed.py','gpu_benchmark_r1.log'),
      @('lock_final_selection.py','selection_lock.log'),
      @('collect_final.py','fresh_collection_r1.log'),
      @('evaluate_final.py','fresh_evaluation_r1.log')
    )){
        if(Test-Path -LiteralPath (Join-Path $studyReport 'STOP_REQUESTED')){throw 'STOP_REQUESTED; do not launch next stage'}
        Save-StudyState $studyStep[0] 'Executing only this declared stage; any failure stops the sequence'
        & $Python -X utf8 (Join-Path $PSScriptRoot $studyStep[0]) *> (Join-Path $studyReport $studyStep[1])
        if($LASTEXITCODE -ne 0){throw "Stage failed: $($studyStep[0]); preserve all outputs"}
        & $Python -X utf8 (Join-Path $PSScriptRoot 'sync_execution.py') *> (Join-Path $studyReport 'page_sync.log')
        if($LASTEXITCODE -ne 0){throw 'Page synchronization failed; stop before any next experiment'}
    }
    Save-StudyState 'COMPLETE_OFFLINE_QUALITY_NOT_HARDWARE' 'Read FINAL_QUALITY.json for PASS/FAIL; exit0 alone is not quality PASS. No automatic hardware stage.'
}catch{
    Save-StudyState 'STOPPED_ON_ERROR_OR_PAUSE' $_.Exception.Message
    throw
}
