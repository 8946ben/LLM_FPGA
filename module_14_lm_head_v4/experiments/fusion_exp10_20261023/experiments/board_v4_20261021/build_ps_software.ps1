param([switch]$SkipPlatform,[switch]$ResumePlatform,[ValidatePattern('^[a-zA-Z0-9_]+$')][string]$PlatformAttempt='r2')
$ErrorActionPreference='Stop'
$taskModule=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$taskEda=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -in @('vivado.exe','xsim.exe','xsimk.exe','xelab.exe','vitis_hls.exe')})
if($taskEda.Count){throw 'Finish active EDA first; no parallel heavy BSP generation'}
if(-not $SkipPlatform){
    & (Join-Path $PSScriptRoot 'prepare_ps_platform.ps1') -Build -ResumePlatform:$ResumePlatform -Attempt $PlatformAttempt
}
$taskHardware=Join-Path $taskModule 'reports/board_v4_20261021/hardware_r2'
$taskAudit=Get-Content -LiteralPath (Join-Path (Split-Path -Parent $taskHardware) 'hardware_audit_r2.json') -Raw | ConvertFrom-Json
if($taskAudit.state -ne 'PASS_OFFLINE_SYSTEM'){throw 'Hardware audit not PASS'}
$taskWorkspace='D:/program/LLM_FPGA/.cache/e10_ps/m14_v4_private_r2'
$taskXsa=Join-Path $taskHardware 'm14_v4_single.xsa'
$taskXsaHash=(Get-FileHash -LiteralPath $taskXsa).Hash.ToLowerInvariant()
if($taskXsaHash -ne $taskAudit.xsa_sha256 -or
   (Get-FileHash -LiteralPath (Join-Path $taskWorkspace 'hw/m14_v4_single.xsa')).Hash.ToLowerInvariant() -ne $taskXsaHash){throw 'Final/platform XSA identity differs'}
if((Get-FileHash -LiteralPath (Join-Path $taskHardware 'm14_v4_system_wrapper.bit')).Hash.ToLowerInvariant() -ne $taskAudit.bit_sha256){throw 'bit identity changed'}
$taskBsp=Join-Path $taskWorkspace 'psu_cortexa53_0/standalone_domain/bsp/psu_cortexa53_0'
foreach($taskRequired in @('include/xparameters.h','include/xlm_head_v4_selector.h','include/xlm_head_v4_selector_hw.h','lib/libxil.a','lib/liblwip4.a')){
    if(-not(Test-Path -LiteralPath (Join-Path $taskBsp $taskRequired))){throw "New BSP incomplete: $taskRequired"}
}
$taskExport=Join-Path $taskModule 'ip_repo/lm_head_v4_selector/drivers/lm_head_v4_selector_v4_10/src'
if((Get-FileHash -LiteralPath (Join-Path $taskExport 'xlm_head_v4_selector_hw.h')).Hash -ne
   (Get-FileHash -LiteralPath (Join-Path $taskBsp 'include/xlm_head_v4_selector_hw.h')).Hash){throw 'Actual BSP register map differs from frozen IP'}
$taskHostResult=Get-Content -LiteralPath (Join-Path $taskModule 'reports/arena_loader_20261022/host_r2/RESULT.json') -Raw | ConvertFrom-Json
if($taskHostResult.state -ne 'PASS_HOST_ONLY_NO_BSP_ELF_BOARD'){throw 'Host loader qualification absent'}
foreach($taskTested in @('standalone/arena_loader/loader_core.c','standalone/arena_loader/loader_core.h','standalone/upload_arena_tcp.py')){
    if((Get-FileHash -LiteralPath (Join-Path $taskModule $taskTested)).Hash.ToLowerInvariant() -ne $taskHostResult.source_sha256.$taskTested){throw "Tested loader source changed: $taskTested"}
}
$taskSw=Join-Path $taskModule 'build/board_v4_20261021/software_r1'
$taskReport=Join-Path $taskModule 'reports/ps_software_20261022_r1'
if((Test-Path -LiteralPath $taskSw) -or (Test-Path -LiteralPath $taskReport)){throw 'Preserve existing software campaign'}
New-Item -ItemType Directory -Path $taskSw,$taskReport | Out-Null
$taskSourceHashes=[ordered]@{}
Get-ChildItem -LiteralPath (Join-Path $taskModule 'standalone') -File -Recurse | Where-Object {$_.Extension -in @('.c','.h','.ld','.py')} | ForEach-Object {
    $taskRel=$_.FullName.Substring($taskModule.Length+1).Replace('\','/')
    $taskSourceHashes[$taskRel]=(Get-FileHash -LiteralPath $_.FullName).Hash.ToLowerInvariant()
}
$taskBin='G:/Xilinx/Vitis/2021.1/gnu/aarch64/nt/aarch64-none/bin'
$taskGcc=Join-Path $taskBin 'aarch64-none-elf-gcc.exe'
$taskPhy=Join-Path $taskBsp 'libsrc/lwip211_v1_5/src/contrib/ports/xilinx/netif/xemacpsif_physpeed.c'
$taskPhyRef=Join-Path 'D:/program/LLM_FPGA' 'ref/xemacpsif_physpeed.c'
if((Get-FileHash -LiteralPath $taskPhy).Hash -ne (Get-FileHash -LiteralPath $taskPhyRef).Hash){throw 'Actual BSP PHY fallback differs from tested reference'}
$taskExpanded=(@('#include "xparameters.h"','M4A_GEM_BASE XPAR_XEMACPS_0_BASEADDR') | & $taskGcc -E -P -x c "-I$taskBsp/include" -) -join "`n"
if($LASTEXITCODE -ne 0 -or $taskExpanded -notmatch '(?im)^M4A_GEM_BASE\s+(0x[0-9a-f]+)[uUlL]*\s*$'){throw 'Cannot resolve actual GEM instance address'}
$taskGemValue=[uint64]::Parse($matches[1].Substring(2),[Globalization.NumberStyles]::HexNumber)
if($taskGemValue -notin @(0xff0b0000L,0xff0c0000L,0xff0d0000L,0xff0e0000L)){throw 'Unexpected ZynqMP GEM address'}
$taskGemBase='0x{0:x8}' -f $taskGemValue
$taskExpanded | Set-Content -LiteralPath (Join-Path $taskReport 'GEM_BASE.txt') -Encoding utf8
$taskElfHashes=[ordered]@{}
foreach($taskKind in @('arena_loader','selector_test')){
    if($taskKind -eq 'arena_loader'){
        $taskSources=@('standalone/arena_loader/main.c','standalone/arena_loader/loader_core.c','standalone/arena_loader/platform_zynqmp.c')
        $taskLibs='-Wl,--start-group,-llwip4,-lxil,-lgcc,-lc,--end-group'
    } else {
        $taskSources=@('standalone/selector_ps_main.c','standalone/selector_control.c','standalone/arena_loader/loader_core.c')
        $taskLibs='-Wl,--start-group,-lxil,-lgcc,-lc,--end-group'
    }
    $taskObjects=@();$taskLog=Join-Path $taskReport ($taskKind+'.log')
    foreach($taskSource in $taskSources){
        $taskObject=Join-Path $taskSw ($taskKind+'_'+[IO.Path]::GetFileNameWithoutExtension($taskSource)+'.o')
        & $taskGcc -std=gnu11 -Wall -Wextra -Werror -O2 -g -DARMA53_64 -c "-I$taskBsp/include" "-I$taskModule/standalone" "-I$taskModule/standalone/arena_loader" (Join-Path $taskModule $taskSource) -o $taskObject 2>&1 | Tee-Object -FilePath $taskLog -Append
        if($LASTEXITCODE -ne 0){throw "Actual v4 BSP compile failed: $taskSource"}
        $taskObjects+=$taskObject
    }
    $taskName='m14_v4_'+$taskKind
    $taskElf=Join-Path $taskSw ($taskName+'.elf')
    & $taskGcc '-Wl,-T' "-Wl,$taskModule/standalone/arena_loader.ld" "-L$taskBsp/lib" "-Wl,-Map=$taskSw/$taskName.map" -o $taskElf @taskObjects $taskLibs 2>&1 | Tee-Object -FilePath $taskLog -Append
    if($LASTEXITCODE -ne 0){throw "Actual v4 BSP link failed: $taskKind"}
    $taskUndefined=(& (Join-Path $taskBin 'aarch64-none-elf-nm.exe') -u $taskElf) -join "`n"
    if($LASTEXITCODE -ne 0 -or $taskUndefined){throw "Undefined symbols: $taskKind"}
    & (Join-Path $taskBin 'aarch64-none-elf-readelf.exe') -h -lW $taskElf *> (Join-Path $taskReport ($taskKind+'_elf_headers.txt'))
    if($LASTEXITCODE -ne 0){throw 'ELF header audit extraction failed'}
    & (Join-Path $taskBin 'aarch64-none-elf-size.exe') $taskElf | Tee-Object -FilePath $taskLog -Append
    if($LASTEXITCODE -ne 0){throw 'ELF size check failed'}
    $taskElfHashes[$taskName+'.elf']=(Get-FileHash -LiteralPath $taskElf).Hash.ToLowerInvariant()
}
foreach($taskRelative in $taskSourceHashes.Keys){
    if((Get-FileHash -LiteralPath (Join-Path $taskModule $taskRelative)).Hash.ToLowerInvariant() -ne $taskSourceHashes[$taskRelative]){throw 'Source changed while compiling'}
}
$taskPython='C:/Users/ben/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $taskPython -X utf8 (Join-Path $taskModule 'scripts/audit_ps_elf.py') --elf (Join-Path $taskSw 'm14_v4_arena_loader.elf') --elf (Join-Path $taskSw 'm14_v4_selector_test.elf') --out (Join-Path $taskReport 'ELF_LAYOUT_AUDIT.json')
if($LASTEXITCODE -ne 0){throw 'Independent ELF architecture/LOAD range audit failed'}
$taskLibraries=[ordered]@{}
foreach($taskItem in @('include/xparameters.h','include/xtime_l.h','include/xlm_head_v4_selector_hw.h','lib/libxil.a','lib/liblwip4.a')){
    $taskLibraries[$taskItem]=(Get-FileHash -LiteralPath (Join-Path $taskBsp $taskItem)).Hash.ToLowerInvariant()
}
@{state='PASS_MATCHING_V4_BSP_ELF_BUILD_ONLY';hardware_xsa_sha256=$taskXsaHash;bit_sha256=$taskAudit.bit_sha256;
  source_sha256=$taskSourceHashes;bsp_sha256=$taskLibraries;elf_sha256=$taskElfHashes;private_gpio_signature='0x4D345A0A';
  ethernet_base=$taskGemBase;phy_patch_sha256=(Get-FileHash -LiteralPath $taskPhy).Hash.ToLowerInvariant();
  loader_protocol='M4AR/version1/port1415/full335544320B arena';target_runtime='NOT_RUN';board_acceptance='NOT_RUN';
  timing_scope='selector_test records raw XTime around full verified-token control call; no IP hardware-cycle counter or LLM TTFT'} |
    ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $taskReport 'BUILD_SOURCES.json') -Encoding utf8
'M14_V4_PS_SOFTWARE=PASS_MATCHING_BSP_ELF_BUILD_ONLY; NOT_BOARD'
