param([ValidateSet('hls','create_bd','build')][string]$Stage)
$ErrorActionPreference='Stop'
$module=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$run=Join-Path $module 'build\board200_20261019\launch'
New-Item -ItemType Directory -Force $run | Out-Null
$script=Join-Path $PSScriptRoot "$Stage.tcl"
$tool='G:\Xilinx\Vivado\2021.1\bin\vivado.bat'
$arguments=@('-mode','batch','-source',$script,'-log',"$Stage.log",'-journal',"$Stage.jou")
if($Stage -eq 'hls') {$tool='G:\Xilinx\Vitis_HLS\2021.1\bin\vitis_hls.bat'; $arguments=@('-f',$script)}
$start=[DateTimeOffset]::Now
Push-Location $run
try {
    & $tool @arguments 2>&1 | Tee-Object -FilePath "$Stage.stdout.log" | Out-Null
    $code=$LASTEXITCODE
    $log=Get-Content -Raw "$Stage.stdout.log"
    if($code -ne 0 -or $log -match '(?m)^ERROR:') {throw "Stage $Stage failed, exit=$code"}
    $marker=switch($Stage) {'hls' {'M14_BOARD200_CSYNTH=PASS'} 'create_bd' {'M14_BOARD200_BD_CREATED_ACTUAL_MHZ='} 'build' {'M14_BOARD200_HARDWARE=PASS'}}
    if($log -notmatch $marker) {throw 'Missing stage completion marker'}
    Write-Output "M14_BOARD200_STAGE_PASS=$Stage"
    @{stage=$Stage; started=$start.ToString('o'); finished=[DateTimeOffset]::Now.ToString('o'); exit_code=$code} | ConvertTo-Json | Set-Content "$Stage.execution.json" -Encoding utf8
} finally {Pop-Location}
