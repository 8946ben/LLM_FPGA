$ErrorActionPreference='Stop'
$taskModule=Split-Path -Parent $PSScriptRoot
$taskRoot=Split-Path -Parent $taskModule
$taskReport=Join-Path $taskModule 'reports/arena_loader_20261022/host_r1'
$taskBuild=Join-Path $taskModule 'build/arena_loader_host_20261022/r1'
if((Test-Path -LiteralPath $taskReport) -or (Test-Path -LiteralPath $taskBuild)){throw 'Preserve previous host campaign'}
New-Item -ItemType Directory -Path $taskReport,$taskBuild | Out-Null
$taskSources=[ordered]@{}
$taskFiles=@('standalone/upload_arena_tcp.py','tests/arena_loader_core_test.c','tests/test_arena_transport.py','standalone/arena_loader.ld')
$taskFiles+=Get-ChildItem -LiteralPath (Join-Path $taskModule 'standalone/arena_loader') -File | Where-Object {$_.Extension -in @('.c','.h')} | ForEach-Object {'standalone/arena_loader/'+$_.Name}
foreach($taskFile in $taskFiles){$taskSources[$taskFile]=(Get-FileHash -LiteralPath (Join-Path $taskModule $taskFile)).Hash.ToLowerInvariant()}
$taskDerivation=Get-Content -LiteralPath (Join-Path $taskModule 'standalone/arena_loader/SOURCE_DERIVATION.json') -Raw | ConvertFrom-Json
foreach($taskItem in $taskDerivation.files.PSObject.Properties){
    if((Get-FileHash -LiteralPath (Join-Path $taskRoot $taskItem.Value.parent)).Hash.ToLowerInvariant() -ne $taskItem.Value.parent_sha256){throw 'Sealed parent source changed'}
}
$env:PATH='G:/Xilinx/Vitis_HLS/2021.1/tps/win64/msys64/mingw64/bin;'+$env:PATH
$taskGcc='G:/Xilinx/Vitis_HLS/2021.1/tps/win64/msys64/mingw64/bin/gcc.exe'
& $taskGcc -std=c11 -Wall -Wextra -Werror -O2 (Join-Path $taskModule 'tests/arena_loader_core_test.c') (Join-Path $taskModule 'standalone/arena_loader/loader_core.c') -o (Join-Path $taskBuild 'arena_loader_core_test.exe') *> (Join-Path $taskReport 'gcc.log')
if($LASTEXITCODE -ne 0){throw 'Portable loader compilation failed'}
& (Join-Path $taskBuild 'arena_loader_core_test.exe') *> (Join-Path $taskReport 'core.log')
if($LASTEXITCODE -ne 0 -or -not(Select-String -LiteralPath (Join-Path $taskReport 'core.log') -Pattern '^M4A_LOADER_CORE_HOST=PASS' -Quiet)){throw 'Portable loader tests failed'}
$taskPython='C:/Users/ben/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
Push-Location $taskModule
try {
    & $taskPython -X utf8 -m unittest discover -s tests -p test_arena_transport.py -v *> (Join-Path $taskReport 'transport.log')
    if($LASTEXITCODE -ne 0){throw 'Mock transport tests failed'}
} finally {Pop-Location}
$taskText=Get-Content -LiteralPath (Join-Path $taskReport 'transport.log') -Raw
if($taskText -notmatch 'Ran 13 tests' -or $taskText -notmatch '(?m)^OK\s*$' -or $taskText -match 'skipped='){throw 'Expected full fixture13 tests without skips'}
& $taskPython -X utf8 (Join-Path $taskModule 'standalone/upload_arena_tcp.py') --report (Join-Path $taskReport 'HOST_PREFLIGHT.json') *> (Join-Path $taskReport 'preflight.log')
if($LASTEXITCODE -ne 0){throw 'Real arena host preflight failed'}
foreach($taskFile in $taskSources.Keys){
    if((Get-FileHash -LiteralPath (Join-Path $taskModule $taskFile)).Hash.ToLowerInvariant() -ne $taskSources[$taskFile]){throw 'Sources changed during test'}
}
@{state='PASS_HOST_ONLY_NO_BSP_ELF_BOARD';updated=(Get-Date -Format o);python_tests=13;target_copy_alignment_length_combinations=88;
  scope='C protocol/64bit bounds/CRC/aligned-copy/partial-ACK; Python fragmented replies + full320MiB mock transfer and negative cases; local real image preflight';
  mock_scope='CRC of received bytes and READ from reference file; not physical DDR, lwIP receive path, or actual network';
  source_sha256=$taskSources;host_exe_sha256=(Get-FileHash -LiteralPath (Join-Path $taskBuild 'arena_loader_core_test.exe')).Hash.ToLowerInvariant();
  parent_v31_sources_unchanged=$true;target_main_compiled=$false;target_pl_ddr='NOT_RUN';network_access='NONE';board='NOT_RUN'} |
    ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $taskReport 'RESULT.json') -Encoding utf8
'M4A_HOST_PHASE=PASS C+13Python+real_image_preflight; mocks only, no BSP/ELF/board'
