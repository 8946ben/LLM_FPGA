param(
    [ValidateSet('csim', 'cosim', 'csynth', 'export')]
    [string]$Action = 'csim',
    [string]$VitisHls = $env:VITIS_HLS_BIN
)

$ErrorActionPreference = 'Stop'
$moduleDir = Split-Path -Parent $PSScriptRoot

if (-not $VitisHls) {
    $candidates = @(
        'D:\install\Xilinx\Vitis_HLS\2021.1\bin\vitis_hls.bat',
        'F:\Xilinx\Vitis_HLS\2021.1\bin\vitis_hls.bat',
        'C:\Xilinx\Vitis_HLS\2021.1\bin\vitis_hls.bat'
    )
    $VitisHls = $candidates | Where-Object { Test-Path -LiteralPath $_ } |
        Select-Object -First 1
}

if (-not $VitisHls -or -not (Test-Path -LiteralPath $VitisHls)) {
    throw 'Vitis HLS 2021.1 not found. Set VITIS_HLS_BIN to vitis_hls.bat.'
}

$scriptMap = @{
    csim = 'run_csim.tcl'
    cosim = 'run_cosim.tcl'
    csynth = 'run_csynth.tcl'
    export = 'run_export_ip.tcl'
}
$successMarkerMap = @{
    csim = 'LM_HEAD_V2_CSIM_PASS'
    cosim = 'LM_HEAD_V2_COSIM_PASS'
    csynth = 'LM_HEAD_V2_CSYNTH_PASS'
    export = 'LM_HEAD_V2_EXPORT_PASS'
}

function Repair-LegacyCoreRevisionAndPack {
    param([string]$ModuleDirectory)

    $ipDir = Join-Path $ModuleDirectory 'build\lm_head_v2_export\solution1\impl\ip'
    $ipPackTcl = Join-Path $ipDir 'run_ippack.tcl'
    $packBat = Join-Path $ipDir 'pack.bat'
    if (-not (Test-Path -LiteralPath $ipPackTcl) -or
        -not (Test-Path -LiteralPath $packBat)) {
        throw 'Legacy IP export failed before run_ippack.tcl/pack.bat was generated.'
    }

    # Vivado <= 2021.1 may encode YYMMDDHHMM as a signed 32-bit
    # core_revision. Dates from 2022 onward overflow that field. Unix seconds
    # remain unique per build and fit until 2038, so use them only for this
    # precisely detected legacy failure and leave newer tool flows untouched.
    $revision = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    if ($revision -gt [int]::MaxValue) {
        throw 'Unix-time core_revision no longer fits in a signed 32-bit integer.'
    }

    $source = [IO.File]::ReadAllText($ipPackTcl)
    $patched = [regex]::Replace(
        $source,
        '(?m)^set Revision\s+"[0-9]+"\r?$',
        ('set Revision    "{0}"' -f $revision),
        1
    )
    if ($patched -eq $source) {
        throw 'Could not locate the generated core_revision in run_ippack.tcl.'
    }
    [IO.File]::WriteAllText($ipPackTcl, $patched, [Text.UTF8Encoding]::new($false))
    Write-Host "Applied legacy core_revision recovery: $revision"

    Push-Location $ipDir
    try {
        $packOutput = @(& $packBat 2>&1)
        $packExitCode = $LASTEXITCODE
        $packOutput | ForEach-Object { Write-Host "$_" }
        $packText = $packOutput -join [Environment]::NewLine
        if ($packExitCode -ne 0 -or $packText -match '(?m)^ERROR:') {
            throw "Vivado IP Packager recovery failed with exit code $packExitCode."
        }
    } finally {
        Pop-Location
    }

    $componentXml = Join-Path $ipDir 'component.xml'
    $archive = Join-Path $ipDir 'user_org_llm_fpga_lm_head_v2_2_0.zip'
    if (-not (Test-Path -LiteralPath $componentXml) -or
        -not (Test-Path -LiteralPath $archive)) {
        throw 'Vivado IP Packager returned without the expected component.xml and IP archive.'
    }
}

function Repair-Vitis2021CosimHiddenSizeVector {
    param([string]$ModuleDirectory)

    $simDir = Join-Path $ModuleDirectory 'build\lm_head_v2_cosim\solution1\sim'
    $cdataDir = Join-Path $simDir 'tv\cdatafile'
    $sourceVector = Join-Path $cdataDir 'c.lm_head_v2.autotvin_hidden_size.dat'
    $rtlVector = Join-Path $cdataDir 'c.lm_head_v2.autotvin_hidden_size_r.dat'
    $simBat = Join-Path $simDir 'verilog\sim.bat'
    if (-not (Test-Path -LiteralPath $sourceVector) -or
        -not (Test-Path -LiteralPath $simBat)) {
        throw 'Vitis 2021.1 CoSim recovery files were not generated.'
    }

    # Vitis HLS 2021.1 names this AXI-Lite port hidden_size_r in RTL, while
    # its C wrapper writes the same vector as hidden_size.  The generated
    # simulator therefore stops at time zero unless both names are present.
    Copy-Item -LiteralPath $sourceVector -Destination $rtlVector -Force
    Write-Host 'Applied Vitis HLS 2021.1 hidden_size_r CoSim vector recovery.'

    Push-Location (Split-Path -Parent $simBat)
    try {
        $simOutput = @(& $simBat 2>&1)
        $simExitCode = $LASTEXITCODE
        $simText = $simOutput -join [Environment]::NewLine
        $simOutput |
            Where-Object {
                "$_" -match 'LM_HEAD_V2_CSIM=PASS|RTL Simulation|Starting C post checking|ERROR:'
            } |
            ForEach-Object { Write-Host "$_" }
        if ($simExitCode -ne 0 -or $simText -match '(?m)^ERROR:') {
            throw "Vitis 2021.1 CoSim recovery failed with exit code $simExitCode."
        }
        if ($simText -notmatch 'Starting C post checking' -or
            ([regex]::Matches($simText, 'LM_HEAD_V2_CSIM=PASS').Count -lt 2)) {
            throw 'Vitis 2021.1 CoSim recovery did not complete RTL and C post checking.'
        }
    } finally {
        Pop-Location
    }
}

$tcl = Join-Path $PSScriptRoot $scriptMap[$Action]
Push-Location $moduleDir
try {
    $toolOutput = @(& $VitisHls -f $tcl 2>&1)
    $exitCode = $LASTEXITCODE
    $toolOutput | ForEach-Object { Write-Host "$_" }
    $toolText = $toolOutput -join [Environment]::NewLine
    $recoveredLegacyExport = $false
    $recoveredVitis2021Cosim = $false
    $legacyRevisionOverflow =
        (($toolText -match 'bad lexical cast') -and
         ($toolText -match 'core_revision')) -or
        (($toolText -match "is an invalid argument\. Please specify an integer value") -and
         ($toolText -match 'set_property core_revision'))
    if ($Action -eq 'export' -and $legacyRevisionOverflow) {
        Repair-LegacyCoreRevisionAndPack -ModuleDirectory $moduleDir
        $recoveredLegacyExport = $true
        Write-Host $successMarkerMap[$Action]
    }
    if ($Action -eq 'cosim' -and
        $toolText -match 'C/RTL co-simulation finished: FAIL' -and
        (Test-Path -LiteralPath (Join-Path $moduleDir 'build\lm_head_v2_cosim\solution1\sim\tv\cdatafile\c.lm_head_v2.autotvin_hidden_size.dat')) -and
        -not (Test-Path -LiteralPath (Join-Path $moduleDir 'build\lm_head_v2_cosim\solution1\sim\tv\cdatafile\c.lm_head_v2.autotvin_hidden_size_r.dat'))) {
        Repair-Vitis2021CosimHiddenSizeVector -ModuleDirectory $moduleDir
        $recoveredVitis2021Cosim = $true
        Write-Host $successMarkerMap[$Action]
    }
    $recovered = $recoveredLegacyExport -or $recoveredVitis2021Cosim
    if ($exitCode -ne 0 -and -not $recovered) {
        throw "Vitis HLS failed with exit code $exitCode"
    }
    if ($toolText -match '(?m)^ERROR:' -and -not $recovered) {
        throw 'Vitis HLS reported an ERROR even though the process exit code was zero.'
    }
    if ($toolText -notmatch [regex]::Escape($successMarkerMap[$Action]) -and
        -not $recovered) {
        throw "Vitis HLS did not emit the expected success marker for $Action."
    }
} finally {
    Pop-Location
}
