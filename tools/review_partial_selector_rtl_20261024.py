from pathlib import Path
import hashlib,json,re
import numpy as np
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';E=M/'experiments/partial_rtl_20261024';R=M/'reports/partial_rtl_20261024_r1/r4'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def readhex(p):
    words=[]
    for line in p.read_text().splitlines():
        line=line.split('//')[0].strip()
        if not line:continue
        for s in line.split():
            assert not s.startswith('@') and not re.search('[xz]',s,re.I),p
            v=int(s,16);words.append([(v>>(32*i))&0xffffffff for i in range(4)])
    return np.asarray(words,dtype='<u4')
def main():
    workflow=json.loads((R/'SELECTOR_WORKFLOW.json').read_text());assert workflow['state']=='SELECTOR_RTL_COMPLETE_AWAITING_REVIEW'
    plan=json.loads((R/'PLAN.json').read_text());log=(R/'simulate.log').read_text();assert 'Fatal:' not in log and 'RADIX_RTL_ALL_PASS cases=13' in log
    pattern=r'RADIX_CASE_PASS index=(\d+) K=(\d+) cycles=(\d+) read=(\d+) write=(\d+) ARstall=(\d+) Rgap=(\d+) AWstall=(\d+) Wstall=(\d+) Bdelay=(\d+) boundary=(\d+)'
    metrics=[list(map(int,m)) for m in re.findall(pattern,log)];assert len(metrics)==13
    for name,h in plan['source_sha256'].items():assert sha(ROOT/name)==h,name
    checked=[];last_read=last_write=0
    for case,row in zip(plan['cases'],metrics):
        i=case['index'];assert row[0]==i and row[1]==case['K'] and 1500000<row[2]<2100000
        inp=readhex(ROOT/case['input']);expected=readhex(ROOT/case['expected']);actual_path=R/'actual'/f'actual_{i:02d}.hex';actual=readhex(actual_path)
        assert actual.shape==(79331,4) and np.array_equal(actual,expected),(i,'whole memory')
        keys=inp[255:255+151936//4].reshape(-1)
        selected=np.lexsort((np.arange(151936),-keys.astype(np.int64)))[:4096]
        ids=np.union1d(selected,np.arange(151643,151657)).astype('<u4')
        offset=255+75968;assert np.array_equal(actual[offset],[0x4449344d,0x00040001,len(ids),151936])
        assert np.array_equal(actual[offset+1:offset+1+(len(ids)+3)//4].reshape(-1)[:len(ids)],ids)
        reference=inp.copy();reference[offset]=[0x4449344d,0x00040001,len(ids),151936]
        packed=np.full(((len(ids)+3)//4)*4,0xffffffff,dtype='<u4');packed[:len(ids)]=ids;reference[offset+1:offset+1+len(packed)//4]=packed.reshape(-1,4)
        assert np.array_equal(actual,reference),(i,'independent keys,stable IDs,padding and all guards')
        assert row[3]-last_read==37984 and row[4]-last_write==1+(len(ids)+3)//4
        last_read,last_write=row[3:5]
        checked.append(dict(index=i,name=case['name'],K=len(ids),cycles=row[2],memory_values=actual.size,actual_sha256=sha(actual_path)))
    assert all(x>0 for x in metrics[-1][5:])
    assert checked[0]['actual_sha256']==checked[2]['actual_sha256'],'A-B-A full-state equality'
    result=dict(state='PASS_SELECTOR_RTL_FULL_ARRAYS_AND_AXI_STALLS',cases=checked,total_u32_values=sum(c['memory_values'] for c in checked),
                final_cumulative_axi=dict(zip(['read_beats','write_beats','AR_stall_cycles','R_gap_cycles','AW_stall_cycles','W_stall_cycles','B_delay_cycles','read_boundary_start_count'],metrics[-1][3:])),
                source_sha_verified=len(plan['source_sha256']),plan_sha256=sha(R/'PLAN.json'),simulation_log_sha256=sha(R/'simulate.log'),reviewer_sha256=sha(Path(__file__)),
                limitations=['Selector segment only, not complete configured M14 RTL','Behavioral single-outstanding stalled AXI memory; not physical DDR performance','No new quality certification or FPGA operation'])
    (R/'INDEPENDENT_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(state=result['state'],cases=len(checked),u32_values=result['total_u32_values'])))
if __name__=='__main__':main()
