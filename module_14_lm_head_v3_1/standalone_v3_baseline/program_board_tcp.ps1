param([string]$Xsct='G:\Xilinx\Vitis\2021.1\bin\xsct.bat',
      [string]$PythonExe='C:\Users\ben\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe',
      [string]$BoardIP='192.168.8.190', [string]$PackageDir, [string]$LoaderPackageDir,
      [switch]$RetainHardware)
$ErrorActionPreference='Stop'
$here=Split-Path -Parent $MyInvocation.MyCommand.Path
$module=Split-Path -Parent $here
$root=Split-Path -Parent $module
if (-not $PackageDir) { $PackageDir=Join-Path $module 'reports\board_package_20261009' }
if (-not $LoaderPackageDir) { $LoaderPackageDir=Join-Path $module 'reports\tcp_loader_package_20261010' }
$bit=Join-Path $PackageDir 'm14_v2_system_wrapper.bit'
$loader=Join-Path $LoaderPackageDir 'm14_tcp_loader.elf'
$psu=Join-Path $LoaderPackageDir 'psu_init.tcl'
foreach ($path in @($Xsct,$PythonExe,$bit,$loader,$psu)) {
    if (-not (Test-Path -LiteralPath $path)) { throw "Missing frozen loader/package input: $path" }
}
$loaderHashes=@{}
Get-Content -LiteralPath (Join-Path $LoaderPackageDir 'ARTIFACTS.sha256') | ForEach-Object {
    if ($_ -match '^([0-9a-f]{64})  (.+)$') {$loaderHashes[$Matches[2]]=$Matches[1]}
}
foreach ($path in @($loader,$psu)) {
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $loaderHashes[[IO.Path]::GetFileName($path)]) {
        throw "TCP loader package hash mismatch: $path"
    }
}
$hashLine=@(Get-Content (Join-Path $PackageDir 'ARTIFACTS.sha256') | Where-Object {$_ -match '^([0-9a-f]{64})  m14_v2_system_wrapper\.bit$'})
if ($hashLine.Count -ne 1 -or (Get-FileHash $bit -Algorithm SHA256).Hash.ToLowerInvariant() -ne ($hashLine[0] -split '  ')[0]) {throw 'Bitstream hash mismatch'}
& $PythonExe (Join-Path $here 'board_profile.py') $PackageDir $LoaderPackageDir $BoardIP
if ($LASTEXITCODE -ne 0) {throw 'Hardware/loader package pairing check failed before board initialization'}
$run=Join-Path $module ('reports\board_runs\'+(Get-Date -Format 'yyyyMMdd_HHmmss_fff')+'_tcp_weight')
New-Item -ItemType Directory -Force $run | Out-Null
$initFlag=$(if ($RetainHardware) {0} else {1})
& $Xsct (Join-Path $here 'scripts\start_tcp_loader.tcl') $bit $psu $loader $initFlag *> (Join-Path $run 'start_loader.log')
if ($LASTEXITCODE -ne 0 -or (Get-Content -Raw (Join-Path $run 'start_loader.log')) -notmatch 'M14_TCP_LOADER_START=PASS') {throw "Loader start failed: $run"}
# PHY negotiation may need several seconds. Connection retries do not write DDR.
$connected=$false
foreach ($attempt in 1..30) {
    $socket=[Net.Sockets.TcpClient]::new()
    try {
        $task=$socket.ConnectAsync($BoardIP,1414)
        if ($task.Wait(1000) -and $socket.Connected) {$connected=$true; break}
    } catch {} finally {$socket.Dispose()}
    Start-Sleep -Seconds 1
}
if (-not $connected) {throw "TCP loader unavailable at ${BoardIP}:1414; log=$run"}
& $PythonExe (Join-Path $here 'upload_weight_tcp.py') --host $BoardIP --report (Join-Path $run 'upload.json') 2>&1 | Tee-Object -FilePath (Join-Path $run 'upload.log')
if ($LASTEXITCODE -ne 0) {throw "TCP weight upload failed: $run"}
& $Xsct (Join-Path $here 'scripts\verify_weight_sentinels.tcl') (Join-Path $root 'artifacts\module14_v2_assets\shared_vocab_weight.bf16.bin') *> (Join-Path $run 'sentinels.log')
if ($LASTEXITCODE -ne 0 -or (Get-Content -Raw (Join-Path $run 'sentinels.log')) -notmatch 'M14_SENTINEL_VERIFY=PASS') {throw "TCP sentinel verification failed: $run"}
Get-FileHash $loader -Algorithm SHA256 | Format-List | Out-String | Set-Content (Join-Path $run 'loader_sha256.txt')
Write-Output "M14_TCP_WEIGHT_DIR=$run"
Write-Output 'M14_BOARD_TCP_PROGRAM=PASS'
