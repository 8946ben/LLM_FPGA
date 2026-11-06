param([switch]$SkipPlatform,[switch]$ResumePlatform)
$ErrorActionPreference='Stop'
$module=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$run=Join-Path $module 'build\board_v31_20261019'
$tool='G:\Xilinx\Vitis\2021.1'
if(-not $SkipPlatform) {
    $platformArgs=@((Join-Path $PSScriptRoot 'platform.tcl'))
    if($ResumePlatform){
        $savedXsa=Join-Path $run 'workspace\m14_board_v31_platform\hw\m14_v31_single.xsa'
        $finalXsa=Join-Path $module 'reports\board_v31_20261019\hardware\m14_v31_single.xsa'
        if((Get-FileHash -LiteralPath $savedXsa).Hash -ne (Get-FileHash -LiteralPath $finalXsa).Hash){throw 'Resume platform XSA differs from final hardware'}
        $platformArgs+='resume'
    }
    & "$tool\bin\xsct.bat" @platformArgs 2>&1 | Tee-Object "$run\platform.log"
    if($LASTEXITCODE -ne 0 -or -not (Select-String -LiteralPath "$run\platform.log" -Pattern '^M14_V31_PLATFORM=PASS$' -Quiet)) {throw 'Platform generation failed or PASS marker absent'}
}
$bsp=Join-Path $run 'workspace\m14_board_v31_platform\psu_cortexa53_0\standalone_domain\bsp\psu_cortexa53_0'
foreach($required in @('include\xparameters.h','include\xlm_head_v2.h','lib\libxil.a','lib\liblwip4.a')){
    if(-not (Test-Path -LiteralPath (Join-Path $bsp $required))){throw "BSP incomplete: $required"}
}
$hardwareXsa=Join-Path $module 'reports\board_v31_20261019\hardware\m14_v31_single.xsa'
$platformXsa=Join-Path $run 'workspace\m14_board_v31_platform\hw\m14_v31_single.xsa'
$xsaHash=(Get-FileHash -LiteralPath $hardwareXsa -Algorithm SHA256).Hash.ToLowerInvariant()
if((Get-FileHash -LiteralPath $platformXsa -Algorithm SHA256).Hash.ToLowerInvariant() -ne $xsaHash){throw 'BSP platform XSA differs from final hardware'}
$sourceHashes=[ordered]@{}
foreach($folder in @((Join-Path $module 'standalone\src'),(Join-Path $PSScriptRoot 'drivers'),(Join-Path $PSScriptRoot 'loader'))){
    Get-ChildItem -LiteralPath $folder -File -Recurse | Where-Object {$_.Extension -in @('.c','.h','.ld')} | ForEach-Object {
        $relative=$_.FullName.Substring($module.Length+1).Replace('\','/')
        $sourceHashes[$relative]=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}
$bin=Join-Path $tool 'gnu\aarch64\nt\aarch64-none\bin'
$gcc=Join-Path $bin 'aarch64-none-elf-gcc.exe'
$sw=Join-Path $run 'software'
New-Item -ItemType Directory -Force $sw | Out-Null
$ld=Join-Path $module 'standalone\src\lscript.ld'
$testSources=@((Join-Path $PSScriptRoot 'drivers\lm_head_v2_driver.c'),
              (Join-Path $PSScriptRoot 'drivers\lm_head_v2_mmio.c'),
              (Join-Path $module 'standalone\src\main.c'))
$loaderSources=@('main.c','loader_core.c','platform_zynqmp.c') | ForEach-Object {Join-Path $PSScriptRoot "loader\$_"}
$loaderLd=Join-Path $sw 'loader.ld'
$text=(Get-Content -Raw $ld).Replace('LENGTH = 0x7FF00000','LENGTH = 0x10000000').Replace('_HEAP_SIZE : 0x2000','_HEAP_SIZE : 0x100000')
Set-Content -LiteralPath $loaderLd -Value $text -Encoding ascii
foreach($kind in @('test','loader','diag','calib_timeout')) {
    $sources=$testSources; $linker=$ld; $name='m14_v2_test'; $libs='-Wl,--start-group,-lxil,-lgcc,-lc,--end-group'
    if($kind -eq 'loader') {$sources=$loaderSources; $linker=$loaderLd; $name='m14_tcp_loader'; $libs='-Wl,--start-group,-llwip4,-lxil,-lgcc,-lc,--end-group'}
    $extraFlags=@()
    if($kind -eq 'diag') {$name='m14_pl_ddr_diag'; $extraFlags=@('-DLMH_V31_SELFTEST_ONLY')}
    if($kind -eq 'calib_timeout') {$name='m14_calib_timeout_test'; $extraFlags=@('-DLMH_V31_SELFTEST_ONLY','-DLMH_V31_TEST_CALIB_TIMEOUT')}
    $objects=@()
    foreach($source in $sources) {
        $object=Join-Path $sw ($kind+'_'+[IO.Path]::GetFileNameWithoutExtension($source)+'.o')
        & $gcc '-Wall' '-Wextra' '-Werror' '-O2' '-g' '-DARMA53_64' @extraFlags '-c' "-I$bsp\include" "-I$PSScriptRoot\drivers" "-I$module\standalone\src" "-I$PSScriptRoot\loader" $source '-o' $object
        if($LASTEXITCODE -ne 0) {throw "Compile failed: $source"}
        $objects+=$object
    }
    $elf=Join-Path $sw "$name.elf"
    & $gcc '-Wl,-T' "-Wl,$linker" "-L$bsp\lib" "-Wl,-Map=$sw\$name.map" '-o' $elf @objects $libs
    if($LASTEXITCODE -ne 0) {throw "Link failed: $kind"}
    $undefined=(& "$bin\aarch64-none-elf-nm.exe" '-u' $elf) -join "`n"
    if($LASTEXITCODE -ne 0 -or $undefined) {throw "Undefined symbols: $kind $undefined"}
    & "$bin\aarch64-none-elf-size.exe" $elf
    if($LASTEXITCODE -ne 0) {throw 'size failed'}
}
foreach($relative in $sourceHashes.Keys){
    if((Get-FileHash -LiteralPath (Join-Path $module $relative) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $sourceHashes[$relative]){throw 'Source changed during compilation'}
}
$elfHashes=[ordered]@{}
Get-ChildItem -LiteralPath $sw -Filter '*.elf' -File | ForEach-Object {$elfHashes[$_.Name]=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
@{format='M14_V31_SOFTWARE_BUILD_IDENTITY';hardware_xsa_sha256=$xsaHash;source_sha256=$sourceHashes;elf_sha256=$elfHashes;
  phy_patch_sha256=(Get-FileHash -LiteralPath (Join-Path (Split-Path -Parent $module) 'ref\xemacpsif_physpeed.c') -Algorithm SHA256).Hash.ToLowerInvariant()} |
    ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $sw 'BUILD_SOURCES.json') -Encoding UTF8
Write-Output 'M14_V31_SOFTWARE=PASS'
