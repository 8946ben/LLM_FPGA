param(
    [string]$Xsct = "G:\Xilinx\Vitis\2021.1\bin\xsct.bat"
)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$script = Join-Path $here "scripts\create_and_build.tcl"

if (-not (Test-Path -LiteralPath $Xsct)) {
    throw "XSCT was not found: $Xsct"
}

& $Xsct $script
if ($LASTEXITCODE -ne 0) {
    throw "Standalone platform generation failed with exit code $LASTEXITCODE"
}

& (Join-Path $here "scripts\build_elf.ps1")
if ($LASTEXITCODE -ne 0) {
    throw "Standalone ELF build failed with exit code $LASTEXITCODE"
}
