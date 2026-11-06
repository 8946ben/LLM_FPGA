"""Audit the frozen build, preserve interrupted evidence, clone an isolated CoSim run."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, shutil
M=Path(__file__).resolve().parents[1]
R=M/'reports';out=R/'resume_20261021_r2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    out.mkdir(exist_ok=False)
    manifest=json.loads((R/'SELECTOR_PRIVATE_IP_MANIFEST.json').read_text(encoding='utf-8'))
    for name,digest in manifest['files'].items():
        assert sha(M/manifest['path']/name)==digest,name
    for name,digest in manifest['source_sha256'].items():assert sha(M/name)==digest,name
    assert sha(M/'interface/PL_DDR_LAYOUT_V4.json')==manifest['layout_sha256']
    fixture=json.loads((R/'selector_integration_fixture_20261021/MANIFEST.json').read_text(encoding='utf-8'))
    for name,digest in fixture['files'].items():assert sha(R/'selector_integration_fixture_20261021'/name)==digest,name
    for data in fixture['binding'].values():assert sha(M.parent/data['path'])==data['sha256'],data['path']
    src=M/'build/selector_csynth_r2/hls';dst=M/'build/selector_full_cosim_r2/hls'
    assert not dst.exists(),'Preserve previous runs'
    shutil.copytree(src,dst,ignore=shutil.ignore_patterns('sim','csim','impl'))
    old=M/'experiments/board_v4_20261021/build.tcl'
    text=old.read_text(encoding='utf-8')
    preamble='''
# Resume only incomplete synthesis runs. Completed IP DCPs remain untouched.
set run_report [open [file join $module reports resume_20261021_r2 vivado_run_states.txt] w]
foreach run [get_runs -filter {IS_SYNTHESIS == 1}] {
    set name [get_property NAME $run]
    set status [get_property STATUS $run]
    puts $run_report "$name\\t$status"
    if {$name ne "synth_1" && ![string match "*Complete*" $status]} {
        puts "M14_V4_RESUME_RESET_INCOMPLETE=$name status=$status"
        reset_run $run
    }
}
close $run_report
'''
    text=text.replace('hardware]','hardware_r2]')
    anchor='open_project [file join $project_dir m14_v4.xpr]'
    assert text.count(anchor)==1
    text=text.replace(anchor,anchor+preamble)
    new=M/'experiments/board_v4_20261021/build_resume_r2.tcl'
    assert not new.exists();new.write_text(text,encoding='utf-8')
    result=dict(state='FROZEN_IP_AND_ASSETS_MATCH_RESUME_PREPARED',
      updated=datetime.now(timezone(timedelta(hours=8))).isoformat(),hardware_access='NONE',
      frozen_ip_files=len(manifest['files']),source_files=len(manifest['source_sha256']),
      canonical_weight_sha256=fixture['binding']['weight']['sha256'],
      hls_clone='build/selector_full_cosim_r2/hls',copied_synthesis_only=True,
      synth_xml_sha256=sha(dst/'solution1/syn/report/lm_head_v4_selector_csynth.xml'),
      original_build_script_sha256=sha(old),resume_build_script_sha256=sha(new),
      previous_pause='reports/pause_20261021/CHECKPOINT.json')
    (out/'PREFLIGHT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    p=M/'PROGRESS.json';d=json.loads(p.read_text(encoding='utf-8'))
    d.update(updated=result['updated'],stage='P4_RESUMED_FROZEN_INTEGRATION_RTL_AND_SYSTEM',
      active_work='User resumed v4; frozen IP/assets audited, isolated CoSim r2 and incomplete Vivado run resume prepared',
      runtime_processes='Offline only; no FPGA operations',next='Verify official fullV RTL PASS and complete system 200MHz STA/CDC')
    d['integrated_selector']['state']='CSIM_CSYNTH_IP_BD_PASS_RESUMED_RTL_SYSTEM_PENDING'
    d['evidence'].append('reports/resume_20261021_r2/PREFLIGHT.json')
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('RESUME_PREFLIGHT=PASS frozenIP301 source8 layout/assets; isolated CoSim ready; no hardware')
if __name__=='__main__':main()
