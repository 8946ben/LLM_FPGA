param(
    [string]$VitisHls = "D:\install\Xilinx\Vitis_HLS\2021.1\bin\vitis_hls.bat",
    [string]$Vivado = "D:\install\Xilinx\Vivado\2021.1\bin\vivado.bat"
)

$ErrorActionPreference = "Stop"
$moduleDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$exportTcl = Join-Path $moduleDir "run_export_ip.tcl"
$ipDir = Join-Path $moduleDir "build\lm_head_export\solution1\impl\ip"
$ipPackTcl = Join-Path $ipDir "run_ippack.tcl"
$componentXml = Join-Path $ipDir "component.xml"

& $VitisHls -f $exportTcl
$hlsExitCode = $LASTEXITCODE
if ($hlsExitCode -eq 0 -and (Test-Path -LiteralPath $componentXml)) {
    Write-Host "LMH IP export completed without compatibility workaround."
    exit 0
}

if (-not (Test-Path -LiteralPath $ipPackTcl)) {
    throw "Vitis HLS did not produce component.xml and failed before generating run_ippack.tcl. Reported exit code: $hlsExitCode."
}

$content = [System.IO.File]::ReadAllText($ipPackTcl)
$pattern = 'set Revision\s+"([0-9]+)"'
$match = [regex]::Match($content, $pattern)
if (-not $match.Success) {
    throw "Cannot find the generated core Revision in run_ippack.tcl."
}

$revision = [uint64]$match.Groups[1].Value
if ($revision -le [int]::MaxValue) {
    throw "Vitis HLS export failed, but core Revision $revision is not a 32-bit overflow. Inspect the HLS log."
}

$content = [regex]::Replace($content, $pattern, 'set Revision    "1"', 1)
[System.IO.File]::WriteAllText(
    $ipPackTcl,
    $content,
    [System.Text.UTF8Encoding]::new($false)
)

Push-Location $ipDir
try {
    & $Vivado -notrace -mode batch -source run_ippack.tcl
    if ($LASTEXITCODE -ne 0) {
        throw "Vivado IP packaging failed with exit code $LASTEXITCODE."
    }
} finally {
    Pop-Location
}

if (-not (Test-Path -LiteralPath $componentXml)) {
    throw "Vivado exited successfully but component.xml is missing."
}

Write-Host "LMH IP export completed after applying the Vitis HLS 2021.1 core_revision workaround."
