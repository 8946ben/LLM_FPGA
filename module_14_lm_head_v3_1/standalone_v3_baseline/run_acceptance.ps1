param(
    [string]$PythonExe = 'C:\Users\ben\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe',
    [string]$Xsct = 'G:\Xilinx\Vitis\2021.1\bin\xsct.bat',
    [string]$PackageDir,
    [ValidateRange(30, 1000)][int]$PerformanceSamples = 30,
    [ValidateRange(1000, 1000)][int]$StabilityRepeats = 1000
)
# Run only after program/load and exact sentinel checks have passed.
# This campaign does not program the PL or reload the shared weight.
$ErrorActionPreference = 'Stop'
$moduleDir = Split-Path -Parent $PSScriptRoot
if (-not $PackageDir) { $PackageDir = Join-Path $moduleDir 'reports\board_package_20261009' }
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss_fff'
$campaignDir = Join-Path $moduleDir "reports\board_runs\${stamp}_acceptance"
New-Item -ItemType Directory -Path $campaignDir -Force | Out-Null
$campaignPath = Join-Path $campaignDir 'campaign.json'
$script:campaign = [ordered]@{
    format = 'M14_V2_INDEPENDENT_ACCEPTANCE'
    package_dir = $PackageDir
    state = 'RUNNING'
    records = @()
}

function Save-Campaign {
    $script:campaign | ConvertTo-Json -Depth 10 |
        Set-Content -LiteralPath $campaignPath -Encoding utf8
}

function Invoke-CampaignRun {
    param([string]$Phase, [string]$Step = 'step_00', [switch]$WriteLogits,
          [int]$RepeatCount = 1, [string]$NegativeTest)
    if (Test-Path -LiteralPath (Join-Path $moduleDir 'reports\board_runs\STOP_REQUESTED')) {
        throw 'M14_STOP_REQUESTED: user requested pause at a completed run boundary'
    }
    $sequence = $script:campaign.records.Count
    $runLog = Join-Path $campaignDir ('{0:d3}_{1}.log' -f $sequence, $Phase)
    Write-Output "M14_CAMPAIGN_RUN_BEGIN phase=$Phase step=$Step sequence=$sequence"
    if ($Phase -eq 'golden_failure') {
        $output = @(& (Join-Path $PSScriptRoot 'run_failure_regression.ps1') `
            -Xsct $Xsct -PythonExe $PythonExe -PackageDir $PackageDir 2>&1)
        $marker = '^M14_FAILURE_REGRESSION_DIR=(.+)$'
    } elseif ($NegativeTest) {
        $output = @(& (Join-Path $PSScriptRoot 'run_negative.ps1') -Test $NegativeTest `
            -Xsct $Xsct -PythonExe $PythonExe -PackageDir $PackageDir 2>&1)
        $marker = '^M14_BOARD_NEGATIVE_DIR=(.+)$'
    } else {
        $arguments = @{Step=$Step; RepeatCount=$RepeatCount; Xsct=$Xsct;
                       PythonExe=$PythonExe; PackageDir=$PackageDir;
                       TimeoutSeconds=$(if ($RepeatCount -gt 1) {600} else {30})}
        if ($WriteLogits) { $arguments.WriteLogits = $true }
        $output = @(& (Join-Path $PSScriptRoot 'run_step.ps1') @arguments 2>&1)
        $marker = '^M14_BOARD_STEP_DIR=(.+)$'
    }
    $output | Set-Content -LiteralPath $runLog -Encoding utf8
    $directoryLine = @($output | Where-Object { "$_" -match $marker })
    if ($directoryLine.Count -ne 1) { throw "Missing run directory marker: $Phase" }
    $runDirectory = ([regex]::Match("$($directoryLine[0])", $marker)).Groups[1].Value
    $decodedPath = Join-Path $runDirectory 'mailbox_decoded.json'
    if (-not (Test-Path -LiteralPath $decodedPath)) {
        & $PythonExe (Join-Path $PSScriptRoot 'parse_mailbox.py') `
            (Join-Path $runDirectory 'mailbox_output.bin') --step $NegativeTest `
            --json-output $decodedPath --package-dir $PackageDir | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Negative mailbox decode failed: $Phase" }
    }
    $decoded = Get-Content -Raw -LiteralPath $decodedPath | ConvertFrom-Json
    $record = $decoded.records[0]
    $record | Add-Member -NotePropertyName campaign_phase -NotePropertyValue $Phase
    $record | Add-Member -NotePropertyName campaign_sequence -NotePropertyValue $sequence
    $script:campaign.records += $record
    Save-Campaign
    Write-Output "M14_CAMPAIGN_RUN_PASS phase=$Phase sequence=$sequence token=$($record.selected_token) cycles=$($record.perf_cycles_total) repeats=$($record.repeat_count)"
}

Save-Campaign
try {
    # The first two runs explicitly regress the new golden and result capture.
    Invoke-CampaignRun -Phase 'accuracy_production' -Step 'step_00'
    Invoke-CampaignRun -Phase 'accuracy_logits' -Step 'step_00' -WriteLogits
    Invoke-CampaignRun -Phase 'golden_failure' -Step 'step_00'
    foreach ($index in 1..7) {
        $stepName = 'step_{0:d2}' -f $index
        Invoke-CampaignRun -Phase 'accuracy_production' -Step $stepName
        Invoke-CampaignRun -Phase 'accuracy_logits' -Step $stepName -WriteLogits
    }
    foreach ($testName in @('bad_abi','bad_flags','bad_dimension','numeric_error')) {
        Invoke-CampaignRun -Phase 'negative' -NegativeTest $testName
    }
    foreach ($index in 1..3) { Invoke-CampaignRun -Phase 'warmup' }
    foreach ($index in 1..$PerformanceSamples) { Invoke-CampaignRun -Phase 'performance' }
    Invoke-CampaignRun -Phase 'stability' -RepeatCount $StabilityRepeats
    $script:campaign.state = 'PASS'
    Save-Campaign
    Write-Output "M14_ACCEPTANCE_CAMPAIGN=PASS directory=$campaignDir"
} catch {
    $script:campaign.state = $(if ($_.Exception.Message -like 'M14_STOP_REQUESTED:*') {'PAUSED'} else {'FAIL'})
    $script:campaign['error'] = $_.Exception.Message
    Save-Campaign
    Write-Output "M14_ACCEPTANCE_CAMPAIGN=$($script:campaign.state) directory=$campaignDir"
    throw
}
