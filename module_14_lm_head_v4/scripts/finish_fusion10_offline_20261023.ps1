# Explicit sequential offline completion. Never waits for or accesses a board.
param([switch]$Run)
$ErrorActionPreference='Stop'
$taskModule=Split-Path -Parent $PSScriptRoot
$taskX=Join-Path $taskModule 'experiments/fusion_exp10_20261023'
$taskR=Join-Path $taskModule 'reports/fusion_exp10_20261023_r1'
$taskPython='C:/Users/ben/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$taskHls='G:/Xilinx/Vitis_HLS/2021.1/bin/vitis_hls.bat'
$taskVivado='G:/Xilinx/Vivado/2021.1/bin/vivado.bat'
if(-not $Run){'PREPARED_ONLY; requires already qualified RTL and explicit -Run';return}
if(-not(Test-Path -LiteralPath (Join-Path $taskR 'RTL_QUALIFICATION.json'))){throw 'Complete and independently qualify RTL first'}
$taskRtl=Get-Content -LiteralPath (Join-Path $taskR 'RTL_QUALIFICATION.json') -Raw | ConvertFrom-Json -AsHashtable
if($taskRtl.state -notlike 'PASS_*'){throw 'RTL qualification did not pass'}
if(@(Get-CimInstance Win32_Process | Where-Object {$_.Name -in @('vitis_hls.exe','vivado.exe','xelab.exe','xsim.exe','xsimk.exe')}).Count){throw 'Do not overlap heavy EDA'}
function Stop-Check {
 if(Test-Path -LiteralPath (Join-Path $taskR 'STOP_REQUESTED')){throw 'Stop marker: no further stage'}
}
function Save-Exp10([string]$Stage,[string]$Detail){
 Stop-Check
 @{stage=$Stage;detail=$Detail;updated=(Get-Date -Format o);pid=$PID;board='NOT_RUN';quality='QUALITY_FAIL_NO_RELEASE_NO_RETUNE'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskR 'EDA_PROGRESS.json') -Encoding utf8
}
function Invoke-Checked([string]$Exe,[string[]]$Arguments,[string]$Log,[string]$Marker){
 Stop-Check
 if(Test-Path -LiteralPath $Log){throw ('Preserve prior log: '+$Log)}
 if($Exe -eq $taskVivado){$Arguments+=@('-log',($Log+'.vivado.log'),'-journal',($Log+'.jou'))}
 & $Exe @Arguments *> $Log
 if($LASTEXITCODE -ne 0 -or -not(Select-String -LiteralPath $Log -SimpleMatch $Marker -Quiet)){throw ('Native phase lacks real completion marker: '+$Log)}
}
try {
 Save-Exp10 'EXP10_EXPORT_IP' 'Export exactly the synthesized/co-simulated short-path solution, no resynthesis'
 $taskExportLog=Join-Path $taskR 'export_existing_r1.log'
 if(Test-Path -LiteralPath $taskExportLog){throw 'Preserve previous export'}
 & $taskHls -f (Join-Path $taskX 'export_existing.tcl') *> $taskExportLog
 $taskExportOk=$LASTEXITCODE -eq 0 -and (Select-String -LiteralPath $taskExportLog -SimpleMatch 'EXP10_EXPORT=PASS' -Quiet) -and -not(Select-String -LiteralPath $taskExportLog -Pattern '^ERROR:' -Quiet)
 if(-not $taskExportOk){
   # Only the independently demonstrated 2026 signed-revision overflow is repaired.
   # Preserve failure and exact original generated metadata, never installation/source.
   $taskPatch=Join-Path $PSScriptRoot 'repair_fusion10_ip_revision_20261023.py'
   & $taskPython -X utf8 $taskPatch
   if($LASTEXITCODE -ne 0){throw 'Export failed for unrecognized reason; no automatic retry'}
   Save-Exp10 'EXP10_LOCAL_GENERATED_IP_REVISION_REPAIR' 'Only generated metadata signed core_revision; original and SHA retained'
   Push-Location 'D:/program/LLM_FPGA/.cache/e10/hls/solution1/impl/ip'
   try {Invoke-Checked $taskVivado @('-mode','batch','-source','run_ippack.tcl','-notrace') (Join-Path $taskR 'export_ippack_revision_r2.log') 'Exiting Vivado'} finally {Pop-Location}
 }
 & $taskPython -X utf8 (Join-Path $PSScriptRoot 'freeze_fusion10_ip_20261023.py') *> (Join-Path $taskR 'freeze_ip.log')
 if($LASTEXITCODE -ne 0){throw 'Private IP/register/synthesized-RTL audit failed'}
 Save-Exp10 'EXP10_CREATE_FULL_PL_DDR_BD' 'New private signature/configuration, both AXI64 masters to PL DDR'
 Invoke-Checked $taskVivado @('-mode','batch','-source',(Join-Path $taskX 'experiments/board_v4_20261021/create_bd.tcl'),'-notrace') (Join-Path $taskX 'reports/selector_bd_create_r1_20261021.log') 'M14_V4_BD_CREATED=PASS'
 Save-Exp10 'EXP10_200MHZ_IMPLEMENTATION' 'Synthesis/P&R/STA/CDC/DRC/bit/XSA, jobs1/maxThreads2, no board'
 Invoke-Checked $taskVivado @('-mode','batch','-source',(Join-Path $taskX 'experiments/board_v4_20261021/build.tcl'),'-notrace') (Join-Path $taskR 'system_build_r1.log') 'M14_V4_HARDWARE=PASS'
 & $taskPython -X utf8 (Join-Path $taskX 'scripts/audit_selector_system.py') *> (Join-Path $taskR 'system_audit.log')
 if($LASTEXITCODE -ne 0){throw 'Independent full-system audit failed'}
 Save-Exp10 'EXP10_MATCHING_BSP_AND_ELFS' 'Offline XSCT platform generation only, matching XSA, actual BSP GEM and PHY'
 & (Join-Path $taskX 'experiments/board_v4_20261021/build_ps_software.ps1') *> (Join-Path $taskR 'ps_build_r1.log')
 if($LASTEXITCODE -ne 0){throw 'Matching PS build failed'}
 Save-Exp10 'EXP10_OFFLINE_ASSET_BINDING' 'Four arenas, actual two ELFs, XSA/bit/PS init and research-only SHA bundle'
 & $taskPython -X utf8 (Join-Path $PSScriptRoot 'package_fusion10_offline_20261023.py') *> (Join-Path $taskR 'package_audit.log')
 if($LASTEXITCODE -ne 0){throw 'Offline asset binding failed'}
 Save-Exp10 'OFFLINE_TESTS_COMPLETE_QUALITY_FAILED_NOT_RELEASE' 'All selected offline phases checked; quality failure retained; FPGA/TTFT NOT_RUN'
 'EXP10_OFFLINE_ENGINEERING=COMPLETE_QUALITY_FAILED_NOT_RELEASE; BOARD_NOT_RUN'
} catch {
 @{stage='EXP10_STOPPED_OFFLINE_STAGE_FAILED_OR_PAUSED';error=$_.Exception.Message;updated=(Get-Date -Format o);pid=$PID;board='NOT_RUN';quality='QUALITY_FAIL_NO_RELEASE_NO_RETUNE'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskR 'EDA_PROGRESS.json') -Encoding utf8
 throw
}
