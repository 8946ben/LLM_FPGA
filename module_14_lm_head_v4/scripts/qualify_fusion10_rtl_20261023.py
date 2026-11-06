"""Official Exp10 CoSim and full memory/scalar trace review; no rerun."""
from pathlib import Path
import hashlib,itertools,json,re,xml.etree.ElementTree as ET
M=Path(__file__).resolve().parents[1];X=M/'experiments/fusion_exp10_20261023';R=M/'reports/fusion_exp10_20261023_r1';S=M.parent/'.cache/e10/hls/solution1/sim'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def compare(c,r):
    count=0;transactions=[];hc=hashlib.sha256();hr=hashlib.sha256()
    with c.open('rb') as a,r.open('rb') as b:
        for i,(x,y) in enumerate(itertools.zip_longest(a,b)):
            assert x is not None and y is not None,('length',c.name,i);hc.update(x);hr.update(y);x=x.strip();y=y.strip()
            if x.startswith(b'0x'):
                assert re.fullmatch(b'0x[0-9a-fA-F]+',y) and int(x,16)==int(y,16),(c.name,i,x,y);count+=1
            else:
                cm=re.fullmatch(rb'\[\[transaction\]\]\s+([0-9]+)',x);rm=re.fullmatch(rb'\[\[transaction\]\]\s+([0-9]+)',y)
                if cm:assert rm and cm[1]==rm[1];transactions.append(int(cm[1]))
                else:assert x==y,(c.name,i,x,y)
    assert transactions==[0,1];return dict(values=count,c_sha256=hc.hexdigest(),rtl_sha256=hr.hexdigest())
def main():
    log=R/'hls_exp10_cosim_r2_short.log';text=log.read_text(encoding='utf-8-sig');assert 'C/RTL co-simulation finished: PASS' in text and 'EXP10_SHORT_COSIM=PASS' in text
    assert not re.search(r'^(?:ERROR:|Fatal:)',text,re.M),'Tool/simulation errors must not be hidden by bat exit0'
    assert 'M14_V4_SELECTOR_CSIM=PASS valid=1 preflight_invalid=1 stage_errors=0 rtl_subset=1' in text
    rpt=S/'report/lm_head_v4_selector_cosim.rpt';assert re.search(r'\|\s*Verilog\|\s*Pass\|',rpt.read_text())
    tr=S/'verilog/lm_head_v4_selector.performance.result.transaction.xml';rows=re.findall(r'^transaction\s+(\d+):\s+(\d+)\s+(\d+|x)\s*$',tr.read_text(),re.M);assert [int(r[0]) for r in rows]==[0,1]
    manifest=json.loads((X/'MANIFEST.json').read_text())
    for n,h in manifest['source_sha256'].items():assert sha(X/n)==h,n
    clone=json.loads((R/'SHORT_PATH_REUSE.json').read_text())
    for n,h in clone['files'].items():assert sha(S.parent/n)==h,n
    outputs={}
    for name in ['plmem','status','stage','child_status','route_count','candidate_count','dense_fallback','selected_token_out','score','output_crc']:
        outputs[name]=compare(S/f'tv/cdatafile/c.lm_head_v4_selector.autotvout_{name}.dat',S/f'tv/rtldatafile/rtl.lm_head_v4_selector.autotvout_{name}.dat');assert outputs[name]['values']==(41943040 if name=='plmem' else 2);print('TRACE_FULL_MATCH',name,outputs[name]['values'],flush=True)
    result=dict(state='PASS_OFFICIAL_COSIM_FULL_RTL_TRACE_AND_ORIGINAL_C_POSTCHECK',outputs=outputs,whole_memory_values=41943040,scalar_outputs=18,transactions=[dict(index=int(i),cycles=int(c),model_ms_at200MHz=int(c)/200000) for i,c,_ in rows],official_log_sha256=sha(log),report_sha256=sha(rpt),transaction_report_sha256=sha(tr),source_manifest_sha256=sha(X/'MANIFEST.json'),scope='One real Chinese debug full-vocabulary preview, all17764 IDs/raw logits/token/score/CRC and one overlap rejection; AXI memory model, not MIG production or new-quality-population RTL replay',quality='QUALITY_FAIL_NO_RELEASE_NO_RETUNE',board='NOT_RUN')
    (R/'RTL_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['state'])
if __name__=='__main__':main()
