param([switch]$Run,[string]$Python='C:/Users/ben/AppData/Local/Programs/Python/Python312/python.exe')
$ErrorActionPreference='Stop'
$taskModule=Split-Path -Parent $PSScriptRoot
$taskReport=Join-Path $taskModule 'reports/fusion_exp10_20261023_r1'
$taskData=Join-Path $taskModule 'data/hidden_fusion10_20261023'
if(-not $Run){'EXP10_QUALITY_PREPARED_ONLY; explicit -Run performs frozen local GPU collection/evaluation';return}
if(-not(Test-Path -LiteralPath (Join-Path $taskModule 'data/fusion10_quality_20261023/EVALUATION_ENTRY_LOCK.json'))){throw 'Numerical/final-test entry must be frozen first'}
if(Test-Path -LiteralPath (Join-Path $taskReport 'QUALITY_WORKFLOW.json')){throw 'Inspect prior workflow; preserve results before explicit resume revision'}
function Check-FusionStop {
 foreach($taskMarker in @((Join-Path $taskReport 'STOP_REQUESTED'),(Join-Path $taskData 'STOP_REQUESTED'))){if(Test-Path -LiteralPath $taskMarker){throw 'User stop request, do not start next quality stage'}}
}
function Save-FusionQuality([string]$Stage,[string]$Detail){@{stage=$Stage;detail=$Detail;updated=(Get-Date -Format o);pid=$PID;board='NOT_RUN';python=$Python} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskReport 'QUALITY_WORKFLOW.json') -Encoding utf8}
try {
 Check-FusionStop
 Save-FusionQuality 'COLLECTING_NEW_FROZEN_DENSE_TRAJECTORIES' '1000 fresh complete question groups; canonical8step head proof first'
 & $Python -X utf8 (Join-Path $PSScriptRoot 'collect_hidden_fusion10_20261023.py') --split holdout --max-new-tokens 16 --max-input-tokens 2048 *> (Join-Path $taskReport 'fresh_collection.log')
 if($LASTEXITCODE -ne 0){throw 'New collection failed; preserve records/source and stop'}
 $taskManifest=Get-Content -LiteralPath (Join-Path $taskData 'holdout/MANIFEST.json') -Raw -Encoding utf8 | ConvertFrom-Json
 if($taskManifest.state -ne 'PASS' -or $taskManifest.excluded_prompts -ne 0){throw 'New collection incomplete/excluded; no final quality verdict'}
 Check-FusionStop
 Save-FusionQuality 'EVALUATING_LOCKED_SELECTED_AND_BASELINE' 'No fit or retune; record proposed independent point gate for both predeclared configs'
 & $Python -X utf8 (Join-Path $PSScriptRoot 'evaluate_fusion10_final_20261023.py') *> (Join-Path $taskReport 'fresh_evaluation.log')
 if($LASTEXITCODE -ne 0){throw 'Final evaluation execution failed; do not change/retune cohort'}
 $taskResult=Get-Content -LiteralPath (Join-Path $taskReport 'FINAL_QUALITY.json') -Raw -Encoding utf8 | ConvertFrom-Json -AsHashtable
 Save-FusionQuality 'FINAL_QUALITY_COMPLETE_NOT_BOARD' $taskResult.state
 ('EXP10_QUALITY='+$taskResult.state)
} catch {Save-FusionQuality 'STOPPED_ON_ERROR_OR_PAUSE' $_.Exception.Message;throw}
