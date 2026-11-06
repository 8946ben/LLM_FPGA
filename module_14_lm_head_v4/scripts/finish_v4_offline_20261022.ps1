param([switch]$ResumePlatform,[ValidatePattern('^[a-zA-Z0-9_]+$')][string]$PlatformAttempt='r2',
      [ValidatePattern('^[a-zA-Z0-9_]+$')][string]$BuildAttempt='r1')
# Direct sequential build, only after completed RTL qualification. No waiter.
$ErrorActionPreference='Stop'
$taskModule=Split-Path -Parent $PSScriptRoot
$taskReports=Join-Path $taskModule 'reports'
$taskStatePath=Join-Path $taskReports 'OFFLINE_SEQUENCE_20261022.json'
function Save-BuildState([string]$Stage,[string]$Detail){
    @{stage=$Stage;detail=$Detail;updated=(Get-Date -Format o);pid=$PID;board='NOT_RUN';
      scope='Direct sequential offline BSP/ELF/package build; no board/daemon/old waiter'} |
      ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $taskStatePath -Encoding utf8
}
$taskRtl=Get-Content -LiteralPath (Join-Path $taskReports 'SELECTOR_INTEGRATION_RESULT_20261021.json') -Raw | ConvertFrom-Json
if($taskRtl.state -ne 'PASS_OFFLINE_INTEGRATED_SELECTOR_RTL'){throw 'Integrated RTL qualification not PASS'}
$taskCurrent=Get-Content -LiteralPath $taskStatePath -Raw | ConvertFrom-Json
if($taskCurrent.stage -ne 'PASS_RTL_QUALIFICATION_PS_NOT_STARTED' -and
   -not($ResumePlatform -and $taskCurrent.stage -eq 'STOPPED_OFFLINE_BUILD_FAILED')){throw 'Inspect current workflow before building'}
$taskBuildLog=Join-Path $taskReports ('ps_software_sequence_20261022_'+$BuildAttempt+'.log')
$taskPackageLog=Join-Path $taskReports 'private_package_20261022.log'
foreach($taskLog in @($taskBuildLog,$taskPackageLog)){
    if(Test-Path -LiteralPath $taskLog){throw 'Preserve previous software/package attempt'}
}
try {
    Save-BuildState 'BUILDING_MATCHING_PS_SOFTWARE' 'Full RTL qualification PASS; generating matching BSP and two ELFs sequentially'
    & (Join-Path $taskModule 'experiments/board_v4_20261021/build_ps_software.ps1') -ResumePlatform:$ResumePlatform -PlatformAttempt $PlatformAttempt *> $taskBuildLog
    $taskManifest=Join-Path $taskReports 'ps_software_20261022_r1/BUILD_SOURCES.json'
    $taskSoftware=Get-Content -LiteralPath $taskManifest -Raw | ConvertFrom-Json
    if($taskSoftware.state -ne 'PASS_MATCHING_V4_BSP_ELF_BUILD_ONLY'){throw 'Actual matching BSP/ELF manifest not PASS'}
    Save-BuildState 'PREPARING_PRIVATE_OFFLINE_PACKAGE' 'Matching BSP and two ELFs built; binding hardware/init/software/profiles'
    & 'C:/Users/ben/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 (Join-Path $PSScriptRoot 'prepare_private_board_package.py') *> $taskPackageLog
    if($LASTEXITCODE -ne 0){throw 'Private offline package validation failed'}
    $taskProgressPath=Join-Path $taskModule 'PROGRESS.json'
    $taskProgress=Get-Content -LiteralPath $taskProgressPath -Raw | ConvertFrom-Json
    $taskProgress.updated=Get-Date -Format o
    $taskProgress.stage='P4_OFFLINE_RTL_SYSTEM_PS_PACKAGE_READY_BOARD_NOT_RUN'
    $taskProgress.active_work='Offline sequence finished; no automatic board or quality jobs'
    $taskProgress.runtime_processes='No further jobs launched by this direct offline sequence'
    $taskProgress.next='Review private package; independent revised-arithmetic quality and newly authorized exclusive board acceptance remain pending'
    $taskProgress.ps_preparation.state='MATCHING_BSP_ELFS_AND_PRIVATE_OFFLINE_PACKAGE_READY'
    $taskProgress.ps_preparation.actual_matching_bsp='PASS_BUILD_ONLY'
    $taskProgress.ps_preparation.elf='PASS_BUILD_AND_LAYOUT_ONLY'
    $taskProgress.dependencies=@('Actual target loading/numerics/timing/stability NOT_RUN; new exclusive board arrangement required',
      'New arithmetic independent quality not certified; opened holdouts not reusable','Upstream direct weights deferred')
    $taskProgress | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $taskProgressPath -Encoding utf8
    Save-BuildState 'PASS_OFFLINE_READY_NOT_BOARD_ACCEPTED' 'RTL/system/BSP/ELFs/internal package qualified offline; no board access or release acceptance'
    'M14_V4_OFFLINE_SEQUENCE=PASS_OFFLINE_READY; BOARD_NOT_RUN'
} catch {
    Save-BuildState 'STOPPED_OFFLINE_BUILD_FAILED' $_.Exception.Message
    throw
}
