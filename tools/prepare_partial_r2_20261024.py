"""Freeze one interface-only repair; preserve all r1 sources and failures."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';E=M/'experiments/partial_hw_20261024';R=M/'reports/partial_hw_20261024_r1';R2=R/'r2';E2=E/'r2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not (R2/'PLAN.json').exists();R2.mkdir(exist_ok=True);(E2/'derived').mkdir(parents=True,exist_ok=True)
    source=(E/'derived/lm_head_v4_candidate.cpp').read_text(encoding='utf-8');original=source
    start=source.index('    ap_uint<128> packed=0;\ngather_row_loop:');end=source.index('        const ap_uint<64> base=',start)
    source=source[:start]+'''gather_row_loop:
    for(ap_uint<32> row=0;row<count;++row) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=4110
        const ap_uint<32> id=table[row];
        ids.write(id);
'''+source[end:]
    source=source.replace('void gather_rows(const ap_uint<128>* weight,const ap_uint<128>* table,','void gather_rows(const ap_uint<128>* weight,const ap_uint<32> table[4110],')
    source=source.replace('void candidate_dataflow(const ap_uint<128>* weight,const ap_uint<128>* table,','void candidate_dataflow(const ap_uint<128>* weight,const ap_uint<32> table[4110],')
    needle='    load_hidden(hidden,cache);\n'
    assert source.count(needle)==1
    source=source.replace(needle,needle+'''    // r2: all shared-meta AXI reads precede the bounded-stream DATAFLOW.
    ap_uint<32> table_cache[4110];ap_uint<128> history_cache[1187];
    ap_uint<128> table_word=0;
preload_candidate_ids:
    for(unsigned i=0;i<count.to_uint();++i) {
#pragma HLS PIPELINE II=1
#pragma HLS LOOP_TRIPCOUNT min=4096 max=4110
        if((i&3)==0)table_word=candidate_table[1+(i>>2)];
        table_cache[i]=table_word.range((i&3)*32+31,(i&3)*32);
    }
preload_history:
    for(unsigned i=0;i<1187;++i) {
#pragma HLS PIPELINE II=1
        history_cache[i]=enable_penalty?history[i]:ap_uint<128>(0);
    }
''')
    source=source.replace('candidate_dataflow(weight,candidate_table,cache,history,candidate_scores,','candidate_dataflow(weight,table_cache,cache,history_cache,candidate_scores,')
    source=source.replace('*history_read_beats=hreads;','*history_read_beats=enable_penalty?1187:0;')
    assert source!=original and 'candidate_dataflow(weight,candidate_table' not in source
    (E2/'derived/lm_head_v4_candidate.cpp').write_text(source,encoding='utf-8')
    for name in ['accepted_numeric_core.hpp','lm_head_v4_candidate.hpp']:(E2/'derived'/name).write_bytes((E/'derived'/name).read_bytes())
    tcl=(E/'proto.tcl').read_text(encoding='utf-8').replace('set root [file normalize [file join [file dirname [info script]] .. .. ..]]','set root [file normalize [file join [file dirname [info script]] .. .. .. ..]]')
    tcl=tcl.replace('.cache p64 $mode','.cache p64_r2 $mode').replace('file join $src derived','file join $src r2 derived')
    (E2/'proto.tcl').write_text(tcl,encoding='utf-8')
    remote=(E/'remote_run.py').read_text(encoding='utf-8')
    remote=remote.replace('E=Path(__file__).resolve().parent;ROOT=E.parents[2];R=ROOT/\'module_14_lm_head_v4/reports/partial_hw_20261024_r1\'','E=Path(__file__).resolve().parents[1];ROOT=E.parents[2];R=ROOT/\'module_14_lm_head_v4/reports/partial_hw_20261024_r1/r2\'')
    remote=remote.replace("str(E/'proto.tcl')","str(E/'r2/proto.tcl')")
    # r2 prepare reuses the already bit-verified model and existingLinux path binding.
    begin=remote.index('def prepare():');finish=remote.index('def run(phase):')
    remote=remote[:begin]+'''def prepare():
    lockpath=R/'REMOTE_ENV_LOCK.json';assert not lockpath.exists()
    parent=read(R.parent/'REMOTE_ENV_LOCK.json');plan=read(R/'PLAN.json')
    for name,h in plan['source_sha256'].items():
        if name==parent['only_path_rebind']['path']:h=parent['only_path_rebind']['after_sha256']
        assert sha(ROOT/name)==h,name
    parent['source_plan_sha256']=sha(R/'PLAN.json');parent['remote_script_sha256']=sha(Path(__file__))
    parent['r2']='candidate/history preloaded before DATAFLOW; no arithmetic/parameter change'
    parent['created']=now();write(lockpath,parent);print('R2_REMOTE_PREPARE_SHA_PASS')
'''+remote[finish:]
    (E2/'remote_run.py').write_text(remote,encoding='utf-8')
    plan=json.loads((R/'PLAN.json').read_text(encoding='utf-8'));plan['state']='FROZEN_R2_INTERFACE_REPAIR'
    plan['parent_plan_sha256']=sha(R/'PLAN.json');plan['r1_failure']='HLS200-1013/984 shared meta bus read by gather_rows and candidate_policy inside DATAFLOW'
    plan['repair']='Preload IDs and history into separate local RAM before accepted exact DATAFLOW. No global parameter/order/FP32 arithmetic changes. Two AXI masters retained; external history read counter now reports preload1187.'
    plan['extra_local_ram_payload_bytes']=4110*4+1187*16
    plan['source_sha256'].update({str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in [Path(__file__),*sorted(E2.glob('*.py')),*sorted(E2.glob('*.tcl')),*sorted((E2/'derived').iterdir())]})
    (R2/'PLAN.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    import tarfile
    with tarfile.open(R/'r2_interface_repair.tar.gz','w:gz') as tar:
        for p in [R2/'PLAN.json',Path(__file__),*sorted(E2.glob('*.py')),*sorted(E2.glob('*.tcl')),*sorted((E2/'derived').iterdir())]:tar.add(p,arcname=p.relative_to(ROOT).as_posix(),recursive=False)
    print(json.dumps(dict(state=plan['state'],extra_ram_bytes=plan['extra_local_ram_payload_bytes'],archive_sha256=sha(R/'r2_interface_repair.tar.gz'))))
if __name__=='__main__':main()
