param([string]$VitisHls='G:\Xilinx\Vitis_HLS\2021.1\bin\vitis_hls.bat')
$ErrorActionPreference='Stop'
$module=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$run=Join-Path $module 'build\board200_20261019'
$ip=Join-Path $run 'hls\solution1\impl\ip'
if (Test-Path -LiteralPath (Join-Path $ip 'component.xml')) {throw 'Preserve existing candidate IP'}
$launch=Join-Path $run 'export_launch'
New-Item -ItemType Directory -Path $launch -Force | Out-Null
Push-Location $launch
try {
    $output=@(& $VitisHls -f (Join-Path $PSScriptRoot 'export.tcl') 2>&1)
    $code=$LASTEXITCODE
    $log=$output -join [Environment]::NewLine
    [IO.File]::WriteAllText((Join-Path $run 'export.log'),$log,[Text.UTF8Encoding]::new($false))
    $overflow=($log -match 'core_revision') -and
        ($log -match 'bad lexical cast|is an invalid argument. Please specify an integer value')
    if ($overflow) {
        $packScript=Join-Path $ip 'run_ippack.tcl'
        $packBat=Join-Path $ip 'pack.bat'
        if (-not (Test-Path -LiteralPath $packScript) -or -not (Test-Path -LiteralPath $packBat)) {
            throw 'Legacy revision overflow detected before recovery files were generated'
        }
        $revision=[DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
        if ($revision -gt [int]::MaxValue) {throw 'Revision exceeds signed 32-bit range'}
        $source=[IO.File]::ReadAllText($packScript)
        $patched=[regex]::Replace($source,'(?m)^set Revision\s+"[0-9]+"\r?$',
                                ('set Revision "{0}"' -f $revision),1)
        if ($source -eq $patched) {throw 'Generated revision assignment not found'}
        [IO.File]::WriteAllText($packScript,$patched,[Text.UTF8Encoding]::new($false))
        Push-Location $ip
        try {
            $repack=@(& $packBat 2>&1)
            $repackExit=$LASTEXITCODE
        } finally {Pop-Location}
        $repackText=$repack -join [Environment]::NewLine
        [IO.File]::WriteAllText((Join-Path $run 'export_revision_recovery.log'),$repackText,
                              [Text.UTF8Encoding]::new($false))
        if ($repackExit -ne 0 -or $repackText -match '(?m)^ERROR:') {throw 'IP revision recovery failed'}
        Write-Output "M14_CANDIDATE_REVISION_RECOVERY=$revision"
    } elseif ($code -ne 0 -or $log -match '(?m)^ERROR:' -or
        $log -notmatch 'M14_BOARD200_EXPORT=PASS') {
        throw "Candidate export failed: $code; inspect export.log"
    }
    if (-not (Test-Path -LiteralPath (Join-Path $ip 'component.xml'))) {throw 'Export missing component.xml'}
    Write-Output "M14_CANDIDATE_IP=$ip"
} finally {Pop-Location}
