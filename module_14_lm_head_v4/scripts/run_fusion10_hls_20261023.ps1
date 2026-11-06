param([ValidateSet('csim','csynth','cosim','export')][string]$Mode='csim',[string]$Run='')
$ErrorActionPreference='Stop'
$taskModule=Split-Path -Parent $PSScriptRoot
$taskExperiment=Join-Path $taskModule 'experiments/fusion_exp10_20261023'
$taskReport=Join-Path $taskModule 'reports/fusion_exp10_20261023_r1'
if(-not $Run){$Run='exp10_'+$Mode+'_r1'}
if($Run -notmatch '^[a-zA-Z0-9_-]+$'){throw 'Bad run name'}
if(-not(Test-Path -LiteralPath (Join-Path $taskExperiment 'MANIFEST.json'))){throw 'Selected hardware must be prepared first'}
$taskOther=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -in @('vivado.exe','xsim.exe','xsimk.exe','vitis_hls.exe','xelab.exe')})
if($taskOther.Count){throw 'Do not overlap heavy EDA; inspect existing task'}
$taskLog=Join-Path $taskReport ('hls_'+$Run+'.log')
if(Test-Path -LiteralPath $taskLog){throw 'Preserve prior run logs'}
if(Test-Path -LiteralPath (Join-Path $taskReport 'STOP_REQUESTED')){throw 'User stop marker, no launch'}
$env:LMH4_SELECTOR_MODE=$Mode;$env:LMH4_SELECTOR_RUN=$Run
@{stage='EXP10_HLS_'+$Mode;run=$Run;pid=$PID;updated=(Get-Date -Format o);board='NOT_RUN';log=$taskLog} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskReport 'EDA_PROGRESS.json') -Encoding utf8
try {
 & 'G:/Xilinx/Vitis_HLS/2021.1/bin/vitis_hls.bat' -f (Join-Path $taskExperiment 'hls_selector.tcl') *> $taskLog
 if($LASTEXITCODE -ne 0){throw ('HLS '+$Mode+' failed; preserve log')}
 if(-not(Select-String -LiteralPath $taskLog -SimpleMatch ('M14_V4_SELECTOR_'+$Mode+'=PASS') -Quiet)){throw 'Actual Tcl success marker absent; bat exit0 does not prove phase completion'}
 @{stage='EXP10_HLS_PHASE_COMPLETE';mode=$Mode;run=$Run;updated=(Get-Date -Format o);board='NOT_RUN'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskReport ('HLS_'+$Mode.ToUpperInvariant()+'.json')) -Encoding utf8
} catch {
 @{stage='EXP10_HLS_FAILED';mode=$Mode;run=$Run;error=$_.Exception.Message;updated=(Get-Date -Format o);board='NOT_RUN'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskReport 'EDA_PROGRESS.json') -Encoding utf8
 throw
}
