param([string]$Xsct='G:\Xilinx\Vitis\2021.1\bin\xsct.bat',
      [string]$ToolBin='G:\Xilinx\Vitis\2021.1\gnu\aarch64\nt\aarch64-none\bin',
      [switch]$SkipPlatform)
$ErrorActionPreference='Stop'
$here=Split-Path -Parent $MyInvocation.MyCommand.Path
$module=Split-Path -Parent $here
$root=Split-Path -Parent $module
if (-not $SkipPlatform) {
    & $Xsct (Join-Path $here 'scripts\create_tcp_platform.tcl')
    if ($LASTEXITCODE -ne 0) { throw 'TCP BSP generation failed' }
}
$bsp=Join-Path $here 'tcp_workspace\m14_tcp_platform\psu_cortexa53_0\standalone_domain\bsp\psu_cortexa53_0'
$src=Join-Path $here 'tcp_loader'
$build=Join-Path $here 'build\tcp_loader'
New-Item -ItemType Directory -Force $build | Out-Null
# Retain the Xilinx license headers in these unchanged platform support files.
foreach ($file in @('platform_zynqmp.c','platform.h','platform_config.h')) {
    Copy-Item -LiteralPath (Join-Path $root "realFpga\vitis\workspace\lm_head_net_diag\src\$file") -Destination (Join-Path $src $file) -Force
}
$ld=(Get-Content -Raw (Join-Path $here 'src\lscript.ld')).Replace('LENGTH = 0x7FF00000','LENGTH = 0x10000000').Replace('_HEAP_SIZE : 0x2000','_HEAP_SIZE : 0x100000')
Set-Content -LiteralPath (Join-Path $build 'lscript.ld') -Value $ld -Encoding ascii
$gcc=Join-Path $ToolBin 'aarch64-none-elf-gcc.exe'
$objects=@()
foreach ($file in @('main.c','loader_core.c','platform_zynqmp.c')) {
    $object=Join-Path $build ($file+'.o')
    & $gcc '-Wall' '-Wextra' '-Werror' '-O2' '-g' '-DARMA53_64' '-c' "-I$bsp\include" "-I$src" (Join-Path $src $file) '-o' $object
    if ($LASTEXITCODE -ne 0) { throw "TCP loader compilation failed: $file" }
    $objects+=$object
}
$elf=Join-Path $build 'm14_tcp_loader.elf'
& $gcc '-Wl,-T' "-Wl,$build\lscript.ld" "-L$bsp\lib" "-Wl,-Map=$build\m14_tcp_loader.map" '-o' $elf @objects '-Wl,--start-group,-llwip4,-lxil,-lgcc,-lc,--end-group'
if ($LASTEXITCODE -ne 0) { throw 'TCP loader link failed' }
$undefined=(& (Join-Path $ToolBin 'aarch64-none-elf-nm.exe') '-u' $elf) -join "`n"
if ($LASTEXITCODE -ne 0 -or $undefined) { throw "Undefined symbols: $undefined" }
& (Join-Path $ToolBin 'aarch64-none-elf-size.exe') $elf
if ($LASTEXITCODE -ne 0) { throw 'size failed' }
Write-Output "M14_TCP_LOADER_ELF=$elf"
Write-Output 'M14_TCP_LOADER_BUILD=PASS'
