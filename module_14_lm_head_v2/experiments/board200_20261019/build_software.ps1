param([switch]$SkipPlatform)
$ErrorActionPreference='Stop'
$module=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$run=Join-Path $module 'build\board200_20261019'
$tool='G:\Xilinx\Vitis\2021.1'
if(-not $SkipPlatform) {
    & "$tool\bin\xsct.bat" (Join-Path $PSScriptRoot 'platform.tcl') 2>&1 | Tee-Object "$run\platform.log"
    if($LASTEXITCODE -ne 0) {throw 'Platform generation failed'}
}
$bsp=Join-Path $run 'workspace\m14_board200_platform\psu_cortexa53_0\standalone_domain\bsp\psu_cortexa53_0'
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
foreach($kind in @('test','loader')) {
    $sources=$testSources; $linker=$ld; $name='m14_v2_test'; $libs='-Wl,--start-group,-lxil,-lgcc,-lc,--end-group'
    if($kind -eq 'loader') {$sources=$loaderSources; $linker=$loaderLd; $name='m14_tcp_loader'; $libs='-Wl,--start-group,-llwip4,-lxil,-lgcc,-lc,--end-group'}
    $objects=@()
    foreach($source in $sources) {
        $object=Join-Path $sw ($kind+'_'+[IO.Path]::GetFileNameWithoutExtension($source)+'.o')
        & $gcc '-Wall' '-Wextra' '-Werror' '-O2' '-g' '-DARMA53_64' '-c' "-I$bsp\include" "-I$PSScriptRoot\drivers" "-I$module\standalone\src" "-I$PSScriptRoot\loader" $source '-o' $object
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
Write-Output 'M14_BOARD200_SOFTWARE=PASS'
