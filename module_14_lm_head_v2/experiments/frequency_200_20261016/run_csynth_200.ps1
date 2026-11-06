param([string]$VitisHls = 'G:\Xilinx\Vitis_HLS\2021.1\bin\vitis_hls.bat')
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $VitisHls)) {
    throw 'Vitis HLS 2021.1 is unavailable. Restore the G: tool disk or pass -VitisHls.'
}
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$module = Split-Path -Parent (Split-Path -Parent $here)
$project = Join-Path $module 'build\frequency_200_20261016\lm_head_v2_200_diagnostic'
if (Test-Path -LiteralPath $project) { throw "Existing diagnostic must be preserved: $project" }
$run = Join-Path $module 'build\frequency_200_20261016'
New-Item -ItemType Directory -Force -Path $run | Out-Null
Push-Location $run
try {
    $output = @(& $VitisHls -f (Join-Path $here 'run_csynth_200.tcl') 2>&1)
    $toolExitCode = $LASTEXITCODE
    $text = $output -join [Environment]::NewLine
    [IO.File]::WriteAllText((Join-Path $run 'csynth_200.log'), $text, [Text.UTF8Encoding]::new($false))
    $output | Where-Object {
        "$_" -match '^ERROR:|Estimated Fmax|Finished Command csynth_design|Total CPU user time|M14_200_CSYNTH_COMPLETE_NOT_TIMING_ACCEPTANCE|\*\*\*\* SW Build'
    } | ForEach-Object { Write-Output "$_" }
    if ($toolExitCode -ne 0 -or $text -match '(?m)^ERROR:') {
        throw "200 MHz diagnostic synthesis failed: exit=$toolExitCode"
    }
    if ($text -notmatch 'M14_200_CSYNTH_COMPLETE_NOT_TIMING_ACCEPTANCE') {
        throw 'Diagnostic did not reach the final marker.'
    }
    Write-Output 'HLS completed. Review achieved II, estimated timing and warnings; no 200 MHz implementation/board acceptance is implied.'
} finally { Pop-Location }
