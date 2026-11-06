param(
    [ValidateSet('verify-ip', 'create', 'build')]
    [string]$Action = 'verify-ip',
    [string]$VivadoBin = $env:VIVADO_BIN
)

$ErrorActionPreference = 'Stop'
$moduleDir = Split-Path -Parent $PSScriptRoot
if (-not $VivadoBin) {
    $candidates = @(
        'D:\install\Xilinx\Vivado\2021.1\bin\vivado.bat',
        'F:\Xilinx\Vivado\2021.1\bin\vivado.bat',
        'C:\Xilinx\Vivado\2021.1\bin\vivado.bat'
    )
    $VivadoBin = $candidates | Where-Object { Test-Path -LiteralPath $_ } |
        Select-Object -First 1
}
if (-not $VivadoBin -or -not (Test-Path -LiteralPath $VivadoBin)) {
    throw 'Vivado 2021.1 not found. Set VIVADO_BIN to vivado.bat.'
}

$ipRepository = Join-Path $moduleDir 'build\lm_head_v2_export\solution1\impl\ip'
$script = switch ($Action) {
    'verify-ip' { Join-Path $PSScriptRoot 'verify_m14_v2_ip.tcl' }
    'create' { Join-Path $PSScriptRoot 'create_m14_v2_single_bd.tcl' }
    'build' { Join-Path $PSScriptRoot 'build_m14_v2_single.tcl' }
}
$arguments = @('-mode', 'batch', '-source', $script)
if ($Action -eq 'verify-ip') {
    $arguments += @('-tclargs', $ipRepository)
}

Push-Location $moduleDir
try {
    & $VivadoBin @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Vivado failed with exit code $LASTEXITCODE"
    }
} finally {
    Pop-Location
}
