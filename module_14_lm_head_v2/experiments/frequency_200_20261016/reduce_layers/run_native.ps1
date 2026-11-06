param(
    [string]$Cxx = 'g++.exe',
    [string]$HlsInclude = 'D:\Xilinx\Vivado\2017.4\include'
)
$ErrorActionPreference = 'Stop'
$module = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
$native = Join-Path $module 'build\frequency_200_20261016\reduce_layers\native'
$reports = Join-Path $module 'reports\frequency_200_20261016\reduce_layers'
New-Item -ItemType Directory -Path $native,$reports -Force | Out-Null
& python (Join-Path $PSScriptRoot 'validate_sources.py')
if ($LASTEXITCODE -ne 0) { throw 'Candidate source identity check failed' }
Copy-Item -LiteralPath (Join-Path $reports 'tested_sources.json') -Destination (Join-Path $reports 'tested_native_sources.json') -Force
$flags = @('-std=c++14','-O2','-fno-fast-math','-ffp-contract=off','-Wno-unknown-pragmas')
$started = [DateTimeOffset]::Now
$compiler = (& $Cxx --version | Select-Object -First 1)
function Run-Checked {
    param([string]$Program, [string[]]$Arguments, [string]$Log)
    $out = @(& $Program @Arguments 2>&1)
    if ($Log) { $out | Set-Content -LiteralPath $Log -Encoding utf8 }
    $out | ForEach-Object { Write-Output "$_" }
    if ($LASTEXITCODE -ne 0) { throw "Failed ($LASTEXITCODE): $Program" }
}
$reducer = Join-Path $native 'reducer_equivalence.exe'
Run-Checked $Cxx ($flags + @((Join-Path $PSScriptRoot 'tests\reducer_equivalence.cpp'),'-o',$reducer)) ''
Run-Checked $reducer @() (Join-Path $reports 'native_reducer.log')
foreach ($variant in @('baseline','candidate')) {
    $source = Join-Path $module 'src\lm_head_v2.cpp'
    if ($variant -eq 'candidate') { $source = Join-Path $PSScriptRoot 'src\lm_head_v2.cpp' }
    $binary = Join-Path $native "kernel_$variant.exe"
    $arguments = $flags + @('-DLMH_V2_TEST_FULL_HIDDEN',"-I$PSScriptRoot\tests", "-I$HlsInclude",
                           $source,(Join-Path $PSScriptRoot 'tests\kernel_equivalence.cpp'),'-o',$binary)
    Run-Checked $Cxx $arguments ''
    Run-Checked $binary @() (Join-Path $reports "native_kernel_$variant.log")
}
$metadata = [ordered]@{
    status = 'PASS'
    verification = 'native software regression; not Vitis HLS CSim, RTL or board validation'
    compiler = $compiler
    flags = $flags
    hls_simulation_headers = $HlsInclude
    started = $started.ToString('o')
    finished = [DateTimeOffset]::Now.ToString('o')
    reducer_samples = 50004
    reducer_inputs_per_sample = 128
    hidden = 896
    vocab = 64
    trials = 8
    exact_logits_per_kernel_variant = 512
    original_tests = @('penalty','tie/disabled IO','lane cancellation','invalid jobs')
    tested_sources_file = 'tested_native_sources.json'
    tested_sources_sha256 = (Get-FileHash -LiteralPath (Join-Path $reports 'tested_native_sources.json') -Algorithm SHA256).Hash.ToLowerInvariant()
    binaries = @{}
    rtl_pass = $null
    timing_pass = $null
    board_pass = $null
}
foreach ($name in @('reducer_equivalence','kernel_baseline','kernel_candidate')) {
    $metadata.binaries[$name] = (Get-FileHash -LiteralPath (Join-Path $native "$name.exe") -Algorithm SHA256).Hash.ToLowerInvariant()
}
$metadata | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $reports 'native_validation.json') -Encoding utf8
Write-Output 'M14_200_NATIVE_REGRESSION_PASS_NOT_HARDWARE_VALIDATION'
