# Rebuild only the repaired loader's IP/subnet variant with the frozen 100 MHz BSP.
$ErrorActionPreference='Stop'
$module=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$run=Join-Path $module 'build\board200_20261019\baseline_loader'
New-Item -ItemType Directory -Force $run | Out-Null
$bsp=Join-Path $module 'standalone\tcp_workspace\m14_tcp_platform\psu_cortexa53_0\standalone_domain\bsp\psu_cortexa53_0'
$bin='G:\Xilinx\Vitis\2021.1\gnu\aarch64\nt\aarch64-none\bin'
$ld=Join-Path $run 'loader.ld'
$text=(Get-Content -Raw (Join-Path $module 'standalone\src\lscript.ld')).Replace('LENGTH = 0x7FF00000','LENGTH = 0x10000000').Replace('_HEAP_SIZE : 0x2000','_HEAP_SIZE : 0x100000')
Set-Content -LiteralPath $ld -Value $text -Encoding ascii
$objects=@()
foreach($file in @('main.c','loader_core.c','platform_zynqmp.c')) {
    $object=Join-Path $run ($file+'.o')
    & "$bin\aarch64-none-elf-gcc.exe" '-Wall' '-Wextra' '-Werror' '-O2' '-g' '-DARMA53_64' '-c' "-I$bsp\include" "-I$PSScriptRoot\loader" (Join-Path $PSScriptRoot "loader\$file") '-o' $object
    if($LASTEXITCODE -ne 0) {throw "Baseline loader compilation failed: $file"}
    $objects+=$object
}
$elf=Join-Path $run 'm14_tcp_loader.elf'
& "$bin\aarch64-none-elf-gcc.exe" '-Wl,-T' "-Wl,$ld" "-L$bsp\lib" "-Wl,-Map=$run\loader.map" '-o' $elf @objects '-Wl,--start-group,-llwip4,-lxil,-lgcc,-lc,--end-group'
if($LASTEXITCODE -ne 0) {throw 'Baseline loader link failed'}
$undefined=(& "$bin\aarch64-none-elf-nm.exe" '-u' $elf) -join "`n"
if($LASTEXITCODE -ne 0 -or $undefined) {throw 'Baseline loader undefined symbols'}
Write-Output 'M14_BASELINE_LOADER_BUILD=PASS'
