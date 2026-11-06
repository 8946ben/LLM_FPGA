param(
    [ValidateSet('create','build')][string]$Action='create',
    [string]$Vivado='G:\Xilinx\Vivado\2021.1\bin\vivado.bat'
)
$ErrorActionPreference='Stop'
$module=Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
$run=Join-Path $module 'build\frequency_200_20261016\reduce_layers\vivado_launch'
New-Item -ItemType Directory -Path $run -Force | Out-Null
$script=Join-Path $PSScriptRoot 'create_bd.tcl'
if ($Action -eq 'build') {$script=Join-Path $PSScriptRoot 'build.tcl'}
$started=[DateTimeOffset]::Now
Push-Location $run
try {
    $output=@(& $Vivado -mode batch -source $script -log "$Action.log" -journal "$Action.jou" 2>&1)
    $code=$LASTEXITCODE
    $log=$output -join [Environment]::NewLine
    [IO.File]::WriteAllText((Join-Path $run "$Action.stdout.log"),$log,[Text.UTF8Encoding]::new($false))
    $output | Where-Object {"$_" -match '^ERROR:|^M14_200_|^M14_V2_PL0_ACTUAL|^M14_V2_CREATE'} |
        ForEach-Object {Write-Output "$_"}
    if ($code -ne 0 -or $log -match '(?m)^ERROR:') {throw "Diagnostic Vivado $Action failed; inspect $run"}
    $marker='M14_200_DIAGNOSTIC_BD_CREATED_ACTUAL_MHZ='
    if ($Action -eq 'build') {$marker='M14_200_ROUTE_COMPLETED_REVIEW_ALL_REPORTS_NOT_BOARD_ACCEPTANCE'}
    if ($log -notmatch $marker) {throw 'Expected Vivado completion marker missing'}
    [ordered]@{action=$Action; started=$started.ToString('o'); finished=[DateTimeOffset]::Now.ToString('o');
               tool=$Vivado;exit_code=$code;board_access=$false} |
        ConvertTo-Json | Set-Content -LiteralPath (Join-Path $run "$Action.execution.json") -Encoding utf8
} finally {Pop-Location}
