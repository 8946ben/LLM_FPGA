param(
    [ValidateSet('csynth', 'csim', 'cosim', 'cosim_full_hidden', 'rtl896')][string]$Mode = 'csynth',
    [string]$VitisHls = 'G:\Xilinx\Vitis_HLS\2021.1\bin\vitis_hls.bat'
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $VitisHls)) {
    throw "Vitis HLS 2021.1 is unavailable: $VitisHls"
}
$module = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
$run = Join-Path $module 'build\frequency_200_20261016\reduce_layers'
& python (Join-Path $PSScriptRoot 'validate_sources.py')
if ($LASTEXITCODE -ne 0) { throw 'Candidate source identity check failed' }
if (Test-Path -LiteralPath (Join-Path $run $Mode)) {
    throw "Preserve existing candidate project: $(Join-Path $run $Mode)"
}
New-Item -ItemType Directory -Path $run -Force | Out-Null
$previousMode = $env:M14_200_MODE
$env:M14_200_MODE = $Mode
$started = [DateTimeOffset]::Now
Push-Location $run
try {
    $output = @(& $VitisHls -f (Join-Path $PSScriptRoot 'run_hls.tcl') 2>&1)
    $toolExit = $LASTEXITCODE
    $log = $output -join [Environment]::NewLine
    [IO.File]::WriteAllText((Join-Path $run "$Mode.log"), $log, [Text.UTF8Encoding]::new($false))
    if ($log -notmatch 'Vitis HLS[^\r\n]*v2021\.1') {
        throw 'Candidate comparison requires Vitis HLS 2021.1; inspect the recorded tool log'
    }
    $output | Where-Object {
        "$_" -match '^ERROR:|Estimated Fmax|Finished Command|M14_200_REDUCE_LAYERS_|LM_HEAD_V2_CSIM=|FULL_HIDDEN_EXACT_LOGITS='
    } | ForEach-Object { Write-Output "$_" }
    $recovered = $false
    # Precisely scoped recovery already required by the accepted 2021.1 flow:
    # the generated RTL scalar is hidden_size_r, while the C vector is hidden_size.
    if (($Mode -like 'cosim*' -or $Mode -eq 'rtl896') -and $log -match 'C/RTL co-simulation finished: FAIL') {
        $sim = Join-Path $run "$Mode\solution1\sim"
        $vectors = Join-Path $sim 'tv\cdatafile'
        $source = Join-Path $vectors 'c.lm_head_v2.autotvin_hidden_size.dat'
        $target = Join-Path $vectors 'c.lm_head_v2.autotvin_hidden_size_r.dat'
        $bat = Join-Path $sim 'verilog\sim.bat'
        if ((Test-Path -LiteralPath $source) -and
            -not (Test-Path -LiteralPath $target) -and (Test-Path -LiteralPath $bat)) {
            Copy-Item -LiteralPath $source -Destination $target
            Push-Location (Split-Path -Parent $bat)
            try {
                $retryOutput = @(& $bat 2>&1)
                $retryExit = $LASTEXITCODE
            } finally { Pop-Location }
            $retry = $retryOutput -join [Environment]::NewLine
            [IO.File]::WriteAllText((Join-Path $run "${Mode}_vector_recovery.log"), $retry,
                                   [Text.UTF8Encoding]::new($false))
            if ($retryExit -eq 0 -and $retry -notmatch '(?m)^ERROR:' -and
                $retry -match 'Starting C post checking' -and
                ([regex]::Matches($retry, 'LM_HEAD_V2_CSIM=PASS').Count -ge 2)) {
                $recovered = $true
                Write-Output 'M14_200_COSIM_VECTOR_RECOVERY_COMPLETE'
            }
        }
    }
    if (-not $recovered) {
        if ($toolExit -ne 0 -or $log -match '(?m)^ERROR:') {
            throw "Candidate $Mode failed: exit=$toolExit"
        }
        if ($log -notmatch "M14_200_REDUCE_LAYERS_${Mode}_COMPLETE_NOT_BOARD_ACCEPTANCE") {
            throw "Candidate $Mode did not reach its completion marker"
        }
    }
    $metadata = [ordered]@{
        mode = $Mode
        started = $started.ToString('o')
        finished = [DateTimeOffset]::Now.ToString('o')
        tool = $VitisHls
        tool_exit = $toolExit
        recovered_vector_name = $recovered
        board_acceptance = $false
    }
    $metadata | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $run "$Mode.execution.json") -Encoding utf8
} finally {
    Pop-Location
    $env:M14_200_MODE = $previousMode
}
