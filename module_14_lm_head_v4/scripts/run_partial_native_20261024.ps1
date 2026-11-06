$ErrorActionPreference = 'Stop'
$modulePath=Split-Path -Parent $PSScriptRoot
$projectPath=Split-Path -Parent $modulePath
$experimentPath=Join-Path $modulePath 'experiments/partial_hw_20261024'
$reportPath=Join-Path $modulePath 'reports/partial_hw_20261024_r1'
$compilerPath='G:/Xilinx/Vitis_HLS/2021.1/tps/win64/msys64/mingw64/bin/g++.exe'
$buildPath=Join-Path $projectPath '.cache/p64/native'
$statePath=Join-Path $reportPath 'NATIVE_WORKFLOW.json'
$lockPath=Join-Path $reportPath 'ACTIVE.lock'
if ((Test-Path -LiteralPath $statePath) -or (Test-Path -LiteralPath $lockPath)) {throw 'Preserve prior run / lock.'}
if (Test-Path -LiteralPath (Join-Path $reportPath 'STOP_REQUESTED')) {throw 'Stop requested.'}
$plan=Get-Content -LiteralPath (Join-Path $reportPath 'PLAN.json') -Raw | ConvertFrom-Json
foreach($item in $plan.source_sha256.PSObject.Properties) {
    if((Get-FileHash -LiteralPath (Join-Path $projectPath $item.Name)).Hash.ToLowerInvariant() -ne $item.Value) {throw ('Source changed: '+$item.Name)}
}
$os=Get-CimInstance Win32_OperatingSystem
if([long]$os.FreePhysicalMemory -lt 1GB/1KB) {throw 'Native functional test needs1GiB free physical memory; compiled beat sizeof16, two weights521MiB plus workspace/runtime.'}
$env:PATH=(Split-Path -Parent $compilerPath)+';'+$env:PATH
$exePath=Join-Path $buildPath 'partial_proto_native.exe'
$arguments=@('-std=c++11','-O1','-ffp-contract=off','-fno-fast-math','-Wno-unknown-pragmas',
    '-IG:/Xilinx/Vitis_HLS/2021.1/include',('-I'+$experimentPath),('-I'+(Join-Path $experimentPath 'derived')),
    (Join-Path $experimentPath 'partial_proto.cpp'),(Join-Path $experimentPath 'derived/lm_head_v4_candidate.cpp'),
    (Join-Path $experimentPath 'proto_tb.cpp'),'-o',$exePath)
$state=[ordered]@{state='NATIVE_COMPILE';started=(Get-Date).ToString('o');parent_pid=$PID;
    parent_creation=(Get-Process -Id $PID).StartTime.ToString('o');runner_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;
    compiler=$compilerPath;compiler_sha256=(Get-FileHash -LiteralPath $compilerPath).Hash;arguments=$arguments;
    free_physical_kib=$os.FreePhysicalMemory;beat_object_bytes=16;mode='Vendor-header native C++ functional simulation; NOT official HLS Csim/RTL';board='NOT_RUN'}
function Save-NativeState {$state|ConvertTo-Json -Depth 7|Set-Content -LiteralPath $statePath -Encoding utf8;$state|ConvertTo-Json -Depth 7|Set-Content -LiteralPath $lockPath -Encoding utf8}
Save-NativeState
try {
    & $compilerPath @arguments *> (Join-Path $reportPath 'native_build.log')
    if($LASTEXITCODE -ne 0) {throw 'Native compilation failed; inspect preserved log.'}
    if(Test-Path -LiteralPath (Join-Path $reportPath 'STOP_REQUESTED')) {throw 'Stop at compile/run boundary.'}
    $state.state='NATIVE_FUNCTIONAL_RUN';$state['executable_sha256']=(Get-FileHash -LiteralPath $exePath).Hash;Save-NativeState
    & $exePath (Join-Path $experimentPath 'fixtures') *> (Join-Path $reportPath 'native_run.log')
    if($LASTEXITCODE -ne 0) {throw 'Native functional test failed; no HLS verdict.'}
    if((Get-Content -LiteralPath (Join-Path $reportPath 'native_run.log') -Raw) -notmatch 'PARTIAL_PROTO_CSIM_ALL_PASS valid=11 unique=9 negative=6') {throw 'Full native test marker missing.'}
    $state.state='NATIVE_COMPLETE_INDEPENDENT_REVIEW_PENDING'
} catch {$state.state='FAILED_NO_AUTOMATIC_RETRY';$state['error']=$_.Exception.Message;throw}
finally {$state['finished']=(Get-Date).ToString('o');$state|ConvertTo-Json -Depth 7|Set-Content -LiteralPath $statePath -Encoding utf8;if(Test-Path -LiteralPath $lockPath){Remove-Item -LiteralPath $lockPath}}
