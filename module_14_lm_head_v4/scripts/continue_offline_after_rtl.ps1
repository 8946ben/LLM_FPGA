# One dependent local build sequence, not a recurring monitor or board task.
$ErrorActionPreference='Stop'
$taskModule=Split-Path -Parent $PSScriptRoot
$taskStateFile=Join-Path $taskModule 'reports/OFFLINE_SEQUENCE_20261022.json'
if(Test-Path -LiteralPath $taskStateFile){throw 'Inspect existing continuation first; do not duplicate'}
$taskStarted=Get-Date
function Save-SequenceState([string]$Stage,[string]$Detail){
    @{stage=$Stage;detail=$Detail;updated=(Get-Date -Format o);started=$taskStarted.ToString('o');pid=$PID;
      board='NOT_RUN';scope='One local sequential offline workflow; no network/board calls';
      rtl_log='reports/selector_repaired_xsim_r5_20261021.log'} |
      ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $taskStateFile -Encoding utf8
}
try {
    Save-SequenceState 'WAITING_EXISTING_RTL' 'Existing r5 continues; no duplicate simulation, no parallel BSP'
    $taskResult=Join-Path $taskModule 'reports/SELECTOR_INTEGRATION_RESULT_20261021.json'
    $taskCollect=Join-Path $taskModule 'reports/selector_integration_collect_20261021.log'
    while($true){
        if((Test-Path -LiteralPath $taskResult) -and (Test-Path -LiteralPath $taskCollect) -and
           (Select-String -LiteralPath $taskCollect -Pattern '^SELECTOR_INTEGRATION=PASS ' -Quiet)){
            $taskRtl=Get-Content -LiteralPath $taskResult -Raw | ConvertFrom-Json
            if($taskRtl.state -ne 'PASS_OFFLINE_INTEGRATED_SELECTOR_RTL'){throw 'Unexpected terminal RTL result'}
            break
        }
        foreach($taskName in @('selector_rtl_trace_audit_20261021.log','selector_integration_collect_20261021.log')){
            $taskFile=Join-Path $taskModule ('reports/'+$taskName)
            if((Test-Path -LiteralPath $taskFile) -and (Select-String -LiteralPath $taskFile -Pattern '^Traceback|^AssertionError:' -Quiet)){
                throw "RTL qualification failed; preserve and inspect $taskName"
            }
        }
        $taskPc=Join-Path $taskModule 'reports/selector_repaired_postcheck_r2_20261021.log'
        if((Test-Path -LiteralPath $taskPc) -and (Select-String -LiteralPath $taskPc -Pattern '^SELECTOR_REPAIRED_POSTCHECK_EXIT=(?!0$)' -Quiet)){
            throw 'Original C postcheck failed; do not continue software workflow'
        }
        $taskTail=(Get-Content -LiteralPath (Join-Path $taskModule 'reports/selector_repaired_xsim_r5_20261021.log') -Tail 24) -join "`n"
        if($taskTail -match '(?m)^(ERROR:|Fatal:)'){throw 'XSim error; inspect original log before continuation'}
        if((Get-Date)-$taskStarted -gt [TimeSpan]::FromHours(12)){throw 'RTL wait deadline reached; does not stop existing simulation'}
        Start-Sleep -Seconds 30
    }
    Save-SequenceState 'BUILDING_MATCHING_PS_SOFTWARE' 'Whole RTL trace+C postcheck qualified; generating matching BSP and two ELFs'
    & (Join-Path $taskModule 'experiments/board_v4_20261021/build_ps_software.ps1') *> (Join-Path $taskModule 'reports/ps_software_sequence_20261022.log')
    $taskManifest=Join-Path $taskModule 'reports/ps_software_20261022_r1/BUILD_SOURCES.json'
    if(-not(Test-Path -LiteralPath $taskManifest)){throw 'Matching PS software manifest absent'}
    $taskSw=Get-Content -LiteralPath $taskManifest -Raw | ConvertFrom-Json
    if($taskSw.state -ne 'PASS_MATCHING_V4_BSP_ELF_BUILD_ONLY'){throw 'PS software build not PASS'}
    Save-SequenceState 'PREPARING_PRIVATE_OFFLINE_PACKAGE' 'Binding XSA/bit/PS init/ELFs/profiles; no target access'
    & 'C:/Users/ben/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 (Join-Path $PSScriptRoot 'prepare_private_board_package.py') *> (Join-Path $taskModule 'reports/private_package_20261022.log')
    if($LASTEXITCODE -ne 0){throw 'Private offline package validation failed'}
    $taskProgressPath=Join-Path $taskModule 'PROGRESS.json'
    $taskProgress=Get-Content -LiteralPath $taskProgressPath -Raw | ConvertFrom-Json
    $taskProgress.updated=Get-Date -Format o
    $taskProgress.stage='P4_OFFLINE_RTL_SYSTEM_PS_PACKAGE_READY_BOARD_NOT_RUN'
    $taskProgress.active_work='Offline sequence finished; no automatic board or quality jobs'
    $taskProgress.runtime_processes='No further jobs launched by this offline sequence'
    $taskProgress.next='Independently review private package; finish independent arithmetic quality and newly authorized exclusive board acceptance'
    $taskProgress.ps_preparation.state='MATCHING_BSP_ELFS_AND_PRIVATE_OFFLINE_PACKAGE_READY'
    $taskProgress.ps_preparation.actual_matching_bsp='PASS_BUILD_ONLY'
    $taskProgress.ps_preparation.elf='PASS_BUILD_AND_LAYOUT_ONLY'
    $taskProgress.dependencies=@('Actual target loading/numerics/timing/stability NOT_RUN; new exclusive board arrangement required',
      'New arithmetic independent quality not certified; opened holdouts not reusable','Upstream direct weights deferred')
    $taskProgress | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $taskProgressPath -Encoding utf8
    Save-SequenceState 'PASS_OFFLINE_READY_NOT_BOARD_ACCEPTED' 'RTL/system/BSP/ELFs/private package qualified offline; no board access or release acceptance'
    'M14_V4_OFFLINE_SEQUENCE=PASS_OFFLINE_READY; BOARD_NOT_RUN'
} catch {
    Save-SequenceState 'STOPPED_ON_ERROR_OR_WAIT_DEADLINE' $_.Exception.Message
    throw
}
