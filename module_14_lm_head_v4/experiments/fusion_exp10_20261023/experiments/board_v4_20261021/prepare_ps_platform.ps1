param([switch]$Build,[switch]$ResumePlatform,[ValidatePattern('^[a-zA-Z0-9_]+$')][string]$Attempt='r2')
$ErrorActionPreference='Stop'
$taskModule=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$taskHardware=Join-Path $taskModule 'reports/board_v4_20261021/hardware_r2'
$taskAudit=Get-Content -LiteralPath (Join-Path (Split-Path -Parent $taskHardware) 'hardware_audit_r2.json') -Raw | ConvertFrom-Json
if($taskAudit.state -ne 'PASS_OFFLINE_SYSTEM'){throw 'Current hardware audit is not PASS'}
$taskXsa=Join-Path $taskHardware 'm14_v4_single.xsa'
$taskXsaHash=(Get-FileHash -LiteralPath $taskXsa -Algorithm SHA256).Hash.ToLowerInvariant()
if($taskXsaHash -ne $taskAudit.xsa_sha256){throw 'XSA changed since hardware audit'}
if((Get-FileHash -LiteralPath (Join-Path $taskHardware 'm14_v4_system_wrapper.bit')).Hash.ToLowerInvariant() -ne $taskAudit.bit_sha256){throw 'bit changed since hardware audit'}
$taskWorkspace='D:/program/LLM_FPGA/.cache/e10_ps'
$taskPlatform=Join-Path $taskWorkspace 'm14_v4_private_r2'
$taskSavedXsa=Join-Path $taskPlatform 'hw/m14_v4_single.xsa'
if($ResumePlatform -or (Test-Path -LiteralPath $taskPlatform)) {
    if(-not (Test-Path -LiteralPath $taskSavedXsa)){throw 'Existing platform incomplete; preserve it for diagnosis'}
    if((Get-FileHash -LiteralPath $taskSavedXsa).Hash.ToLowerInvariant() -ne $taskXsaHash){throw 'Existing platform XSA differs'}
}
if(-not $Build){
    'M14_V4_PS_PREFLIGHT=PASS_NO_EDA_NO_BOARD; BSP/ELF/loader not built'
    return
}
$taskEda=@(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -in @('vivado.exe','xsim.exe','xsimk.exe','xelab.exe','vitis_hls.exe')
})
if($taskEda.Count){throw 'Finish EDA simulation/implementation first; preserve host memory'}
if((Test-Path -LiteralPath $taskPlatform) -and -not $ResumePlatform){throw 'Explicit audited resume required; do not overwrite platform'}
$taskLog=Join-Path $taskModule ('reports/selector_ps_platform_'+$Attempt+'_20261021.log')
if(Test-Path -LiteralPath $taskLog){throw 'Preserve existing platform log; inspect prior result first'}
$taskArgs=@((Join-Path $PSScriptRoot 'platform.tcl').Replace('\','/'))
if($ResumePlatform){$taskArgs+='resume'}
& 'G:/Xilinx/Vitis/2021.1/bin/xsct.bat' @taskArgs *> $taskLog
if($LASTEXITCODE -ne 0 -or -not (Select-String -LiteralPath $taskLog -Pattern '^M14_V4_PRIVATE_PLATFORM=PASS_OFFLINE_BSP_ONLY$' -Quiet)){throw 'BSP generation failed or PASS marker absent'}
if((Get-FileHash -LiteralPath $taskXsa).Hash.ToLowerInvariant() -ne $taskXsaHash -or
   (Get-FileHash -LiteralPath $taskSavedXsa).Hash.ToLowerInvariant() -ne $taskXsaHash){throw 'Platform/XSA identity mismatch'}
$taskBsp=Join-Path $taskPlatform 'psu_cortexa53_0/standalone_domain/bsp/psu_cortexa53_0'
foreach($taskRequired in @('include/xparameters.h','include/xlm_head_v4_selector.h','lib/libxil.a','lib/liblwip4.a')) {
    if(-not(Test-Path -LiteralPath (Join-Path $taskBsp $taskRequired))){throw "BSP incomplete: $taskRequired"}
}
'M14_V4_PS_PLATFORM=PASS_OFFLINE_BSP_ONLY; no ELF, target loading or board access'
