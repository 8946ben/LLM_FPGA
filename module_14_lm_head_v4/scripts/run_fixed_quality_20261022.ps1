param([switch]$Run,[string]$Python='C:/Users/ben/AppData/Local/Programs/Python/Python312/python.exe')
# Offline PC GPU only. No FPGA/JTAG/network calls.
$ErrorActionPreference='Stop'
$taskModule=Split-Path -Parent $PSScriptRoot
$taskData=Join-Path $taskModule 'data/fixed_quality_20261022'
$taskReport=Join-Path $taskModule 'reports/fixed_quality_20261022'
$taskFreeze=Get-Content -LiteralPath (Join-Path $taskData 'IMPLEMENTATION_FREEZE.json') -Raw | ConvertFrom-Json
$taskEntry=Get-Content -LiteralPath (Join-Path $taskData 'EVALUATION_ENTRY_LOCK.json') -Raw | ConvertFrom-Json
foreach($taskLock in @($taskFreeze,$taskEntry)){
    foreach($taskProperty in $taskLock.source_sha256.PSObject.Properties){
        if((Get-FileHash -LiteralPath (Join-Path $taskModule $taskProperty.Name)).Hash.ToLowerInvariant() -ne $taskProperty.Value){throw "Frozen source changed: $($taskProperty.Name)"}
    }
}
if((Get-FileHash -LiteralPath (Join-Path $taskData 'holdout.jsonl')).Hash.ToLowerInvariant() -ne $taskEntry.corpus_sha256){throw 'Frozen corpus changed'}
if(-not $Run){'FIXED_QUALITY_WORKFLOW=PREPARED_ONLY; add -Run only under the verified GPU Python';return}
if(-not(Test-Path -LiteralPath $Python)){throw 'GPU Python missing; do not substitute an unqualified environment'}
New-Item -ItemType Directory -Path $taskReport -Force | Out-Null
$taskState=Join-Path $taskReport 'WORKFLOW.json'
if(Test-Path -LiteralPath $taskState){throw 'Preserve existing workflow and inspect before explicit resume'}
function Save-QualityState([string]$Stage,[string]$Detail){
    @{stage=$Stage;detail=$Detail;updated=(Get-Date -Format o);pid=$PID;python=$Python;
      scope='Offline local GPU quality only, fixed config, no board or network';board='NOT_RUN'} |
      ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $taskState -Encoding utf8
}
try {
    Save-QualityState 'TOKENIZER_RUNTIME_PREFLIGHT' 'Check all1000 actual input lengths/model/source before any new labels'
    & $Python -X utf8 (Join-Path $PSScriptRoot 'preflight_fixed_quality_runtime_20261022.py') *> (Join-Path $taskReport 'preflight.log')
    if($LASTEXITCODE -ne 0){throw 'Pre-label tokenizer/runtime validation failed; no resampling'}
    Save-QualityState 'COLLECTING_FROZEN_DENSE_TRAJECTORIES' 'Canonical eight-step head proof, then fresh1000 prompt-grouped labels; no tuning'
    & $Python -X utf8 (Join-Path $PSScriptRoot 'collect_hidden_fixed_20261022.py') --split holdout --max-new-tokens 16 --max-input-tokens 2048 *> (Join-Path $taskReport 'collection.log')
    if($LASTEXITCODE -ne 0){throw 'Frozen collection failed; preserve all records/settings'}
    $taskManifest=Get-Content -LiteralPath (Join-Path $taskModule 'data/hidden_fixed_20261022/holdout/MANIFEST.json') -Raw | ConvertFrom-Json
    if($taskManifest.state -ne 'PASS'){throw 'Collection not complete; no independent quality verdict'}
    if(Test-Path -LiteralPath (Join-Path $taskModule 'data/hidden_fixed_20261022/STOP_REQUESTED')){throw 'User pause marker; do not start evaluation'}
    Save-QualityState 'EVALUATING_FROZEN_ARITHMETIC' 'Same fixed route4/rank128/top16384; report single/hybrid coverage and candidate counts'
    & $Python -X utf8 (Join-Path $PSScriptRoot 'evaluate_fixed_quality_20261022.py') *> (Join-Path $taskReport 'evaluation.log')
    if($LASTEXITCODE -ne 0){throw 'Independent evaluation failed; no quality PASS'}
    $taskResult=Get-Content -LiteralPath (Join-Path $taskReport 'RESULT.json') -Raw | ConvertFrom-Json
    Save-QualityState 'COMPLETE_NOT_BOARD_ACCEPTED' $taskResult.state
    ('FIXED_QUALITY_WORKFLOW=COMPLETE '+$taskResult.state+'; NOT_BOARD')
} catch {
    Save-QualityState 'STOPPED_ON_ERROR_OR_PAUSE' $_.Exception.Message
    throw
}
