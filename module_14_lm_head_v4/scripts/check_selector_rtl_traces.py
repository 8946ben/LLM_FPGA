"""Strict full-memory/scalar comparison after the generated XSim wrapper repair."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import argparse,hashlib,itertools,json,re
from selector_rtl_completion import REPORT, preserved_completion, transactions
M=Path(__file__).resolve().parents[1];R=M/'reports'
S=M/'build/selector_full_cosim_r2/hls/solution1/sim'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()
def compare(c,r):
    count=0;transactions=0;h1=hashlib.sha256();h2=hashlib.sha256()
    with c.open('rb') as a,r.open('rb') as b:
        for i,(x,y) in enumerate(itertools.zip_longest(a,b)):
            assert x is not None and y is not None,(c.name,'length differs',i)
            h1.update(x);h2.update(y);xs=x.strip();ys=y.strip()
            if xs.startswith(b'0x'):
                assert re.fullmatch(b'0x[0-9a-fA-F]+',ys),(r.name,'unknown or invalid RTL value',i,ys)
                assert int(xs,16)==int(ys,16),(r.name,'value mismatch',i,xs,ys)
                count+=1
            else:
                # C uses an unpadded ID; Verilog uses %d with leading spaces.
                # Only this documented formatting variation is accepted.
                cm=re.fullmatch(rb'\[\[transaction\]\]\s+([0-9]+)',xs)
                rm=re.fullmatch(rb'\[\[transaction\]\]\s+([0-9]+)',ys)
                if cm is not None:
                    assert rm is not None and int(cm[1])==int(rm[1]),(r.name,'transaction ID mismatch',i,xs,ys)
                    transactions+=1
                else:
                    assert xs==ys,(r.name,'trace structure mismatch',i,xs,ys)
    assert transactions==2,(c.name,transactions)
    return dict(values=count,transactions=transactions,c_sha256=h1.hexdigest(),rtl_sha256=h2.hexdigest())
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--recover-preserved',action='store_true')
    args=parser.parse_args()
    recovery=None
    if args.recover_preserved:
        recovery=preserved_completion()
        (R/'SELECTOR_COMPLETION_RECOVERY_20261022.json').write_text(json.dumps(recovery,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    complete=False
    with (R/'selector_repaired_xsim_r5_20261021.log').open(encoding='utf-8-sig') as f:
        for line in f:
            assert 'ERROR:' not in line and 'Fatal:' not in line,'Simulation error'
            if line.strip()=='SELECTOR_SIM_OUTPUTS_COMPLETE_PENDING_STRICT_COMPARE':complete=True
    assert complete or recovery is not None,'Observable run did not complete; explicit preserved-output recovery required'
    tr=REPORT;assert tr.exists(),'No completed transaction report'
    cases=transactions(tr)
    assert len(cases)==2 and cases[0]['cycles']>2430976 and cases[1]['cycles']>0,cases
    for name in ('.aesl_error','.exit.err','err.log'):
        p=S/'verilog'/name
        if p.exists():assert p.read_text().strip() in ('','0'),'Simulator error indicator: '+name
    repair=json.loads((R/'SELECTOR_COSIM_NAME_REPAIR.json').read_text(encoding='utf-8'))
    assert sha(M/repair['wrapper'])==repair['after_sha256']
    observable=json.loads((R/'XSIM_OBSERVABILITY_CONTROL.json').read_text(encoding='utf-8'))
    assert sha(M/'experiments/board_v4_20261021/selector_progress_r4.tcl')==observable['new_tcl_sha256']
    for name in observable['compiled_payload_unchanged']:
        assert sha(S/'verilog/xsim.dir/lm_head_v4_selector_o3'/name)==observable['snapshot_files'][name],name
    for name,digest in repair['generated_synth_rtl_sha256'].items():
        assert sha(S.parent/'syn/verilog'/name)==digest,name
        if name.endswith(('.v','.vh')):assert sha(S/'verilog'/name)==digest,'Compiled DUT differs: '+name
    outputs={}
    for name in ['plmem','status','stage','child_status','route_count','candidate_count','dense_fallback','token','score','output_crc']:
        c=S/f'tv/cdatafile/c.lm_head_v4_selector.autotvout_{name}.dat'
        r=S/f'tv/rtldatafile/rtl.lm_head_v4_selector.autotvout_{name}.dat'
        outputs[name]=compare(c,r)
        expected=20971520*2 if name=='plmem' else 2
        assert outputs[name]['values']==expected,(name,outputs[name]['values'])
        print(f'RTL_TRACE_MATCH {name} values={expected}',flush=True)
    result=dict(state='PASS_FULL_RTL_TRACE_COMPARE',updated=datetime.now(timezone(timedelta(hours=8))).isoformat(),
      scope='FullV real Chinese RUN and overlap rejection, all320MiB memory words in both transactions plus all outputs',
      whole_memory_values=20971520*2,outputs=outputs,transactions=cases,hardware_access='NONE',
      simulation_wrapper='Only generated initial-block label renamed; same synthesized DUT and C golden traces',
      official_hls_wrapper='Original HLS cosim_design remains FAIL at XSim compilation; this is repaired generated-XSim validation',
      xsim_log_sha256=sha(R/'selector_repaired_xsim_r5_20261021.log'),
      repair_sha256=sha(R/'SELECTOR_COSIM_NAME_REPAIR.json'),c_postcheck='SEE_SEPARATE_LOG',board_decode='NOT_RUN')
    result['simulator_control_sha256']=sha(R/'XSIM_OBSERVABILITY_CONTROL.json')
    if recovery is not None:
        result['preserved_completion_recovery_sha256']=sha(R/'SELECTOR_COMPLETION_RECOVERY_20261022.json')
        result['completion_route']='Preserved genuine testbench finish + all output trailers + checkpoint SHA; original Tcl path bug retained'
    (R/'SELECTOR_RTL_TRACE_AUDIT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('SELECTOR_FULL_RTL_TRACE_AUDIT=PASS words41943040 scalar_outputs18; not board')
if __name__=='__main__':main()
