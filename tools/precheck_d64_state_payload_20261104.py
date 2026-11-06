"""Synthetic controls of prepared payload/control audit functions; NEVER RTL results."""
import copy,datetime,hashlib,json
from pathlib import Path
import numpy as np
from review_d64_state_payload_20261104 import ROOT,M,META_WORDS,TOTAL_WORDS,GUARD,reference_arrays,review_case,review_control
R=M/'reports/d64_state_tb_20261104_r1'

def main():
    path=M/'reports/d64_state_fixtures_20261104_r2/MANIFEST.json';manifest=json.loads(path.read_text())
    scenarios=manifest['scenarios'];assert len(scenarios)==12
    image=np.full(TOTAL_WORDS,0xa5a5a5a5,dtype='<u4');image[-4:]=GUARD
    results=[];saved={}
    def synthesize(s,old):
        before=old.copy();before[:META_WORDS]=np.frombuffer((ROOT/s['input_path']).read_bytes(),dtype='<u4')
        after=before.copy();w=after[META_WORDS:-4];e=s['expected'];k=e['k']
        if e['expected_status']==0:
            arrays=reference_arrays(s['fixture'])
            w[:151936]=arrays['keys'];w[37984*4:37984*4+151936]=arrays['preview']
            w[79052*4:79052*4+64]=arrays['dims']
            w[75968*4:75969*4]=[0x4449344d,0x40001,k,151936]
            w[75969*4:75969*4+k]=arrays['ids'];w[75969*4+k:75969*4+((k+3)//4)*4]=0xffffffff
            if s['debug']==1:
                pairs=w[76997*4:76997*4+2*k].reshape(k,2);pairs[:,0]=arrays['ids'];pairs[:,1]=arrays['raw']
                if k&1:w[76997*4+2*k:76997*4+2*k+2]=0
        elif s['case_index']==10:
            # Only a deliberately synthetic undefined intermediate change.
            w[37984*4]=0x7fc00000
        metrics=dict(case=s['case_index'],label=s['label'],debug=s['debug'],status=e['expected_status'],
            token=e['token'],score=e['score_bits'],K=k,crc=e['crc'],ip_cycles=1000+s['case_index'],
            control_call_cycles=1100+s['case_index'],meta_reads=1523,meta_writes=80000,
            weight_reads=1220608+112*k,canonical_requests=10,raw_write_beats=(k+1)//2 if s['debug']==1 else 0,
            total_starts=s['case_index']+1)
        if e['expected_status']!=0:
            metrics.update(canonical_requests=0,raw_write_beats=0)
            if s['case_index'] in [5,6,7,8,9]:
                metrics.update(weight_reads=0,meta_writes=0,meta_reads=0 if s['case_index'] in [5,6] else 112)
            else:metrics.update(weight_reads=1220608,meta_writes=100)
        return before,after,metrics
    for s in scenarios:
        before,after,metrics=synthesize(s,image)
        results.append(review_case(s,before,after,metrics));image=after
        if s['case_index'] in [0,3,5,10]:saved[s['case_index']]=(before,after,metrics)
    assert results[0]['assembled_sha256']==results[2]['assembled_sha256']==results[11]['assembled_sha256']
    assert results[0]['assembled_sha256']!=results[1]['assembled_sha256']
    rejected=[]
    changes=[('preview_bit',0,'after',META_WORDS+37984*4),('key_bit',0,'after',META_WORDS),
             ('dimension',0,'after',META_WORDS+79052*4),('candidate_id',0,'after',META_WORDS+75969*4),
             ('raw_value',0,'after',META_WORDS+76997*4+1),('guard',0,'after',TOTAL_WORDS-1),
             ('metadata_write',0,'after',0),('production_raw_changed',3,'after',META_WORDS+76997*4),
             ('early_error_workspace_write',5,'after',META_WORDS+100),
             ('preview_error_raw_changed',10,'after',META_WORDS+76997*4)]
    for label,index,which,offset in changes:
        b,a,m=saved[index];b=b.copy();a=a.copy();m=dict(m)
        (a if which=='after' else b)[offset]^=np.uint32(1)
        try:review_case(scenarios[index],b,a,m)
        except AssertionError:rejected.append(label)
        else:raise AssertionError('Accepted '+label)
    for label,index,field,value in [('token',0,'token',0),('crc',0,'crc',0),('missing_start',0,'total_starts',0),
                                   ('missing_exact_reads',0,'weight_reads',1220608),('production_raw_request',3,'raw_write_beats',1),
                                   ('error_canonical_request',10,'canonical_requests',1),('early_error_weights',5,'weight_reads',1)]:
        b,a,m=saved[index];m=dict(m);assert m[field]!=value;m[field]=value
        try:review_case(scenarios[index],b,a,m)
        except AssertionError:rejected.append(label)
        else:raise AssertionError('Accepted '+label)
    rows=[];cycle=0
    def emit(op,frame,address,value):
        nonlocal cycle
        cycle+=1;rows.append([op,str(frame),str(cycle),'%02x'%address,'%08x'%value])
    for s in scenarios:
        i=s['case_index'];e=s['expected'];emit('R',i,0,12)
        for addr in [0x54,0x64,0x74,0x84,0x94,0xa8]:emit('R',i,addr,0);emit('R',i,addr,0)
        for addr,value in [(0x10,0),(0x14,0),(0x1c,0),(0x20,0),(0x28,273416192),(0x2c,0),(0x34,24368),(0x38,0),(0x40,s['capacity']),(0x48,s['debug'])]:
            emit('W',i,addr,value);emit('R',i,addr,value)
        emit('W',i,0,1);emit('R',i,0,0);emit('R',i,0,14)
        for addr in [0x54,0x64,0x74,0x84,0x94,0xa8]:emit('R',i,addr,1);emit('R',i,addr,0)
        for addr,value in [(0x50,e['expected_status']),(0x60,e['token']),(0x70,e['score_bits']),(0x80,e['k']),(0x90,e['crc']),(0xa0,1220608 if e['expected_status']==0 else 0),(0xa4,0)]:emit('R',i,addr,value)
        emit('R',i,0,12)
    control=review_control(scenarios,rows)
    indexes={
        'missing_fresh_valid':next(i for i,r in enumerate(rows) if r[0]=='R' and r[3]=='54' and r[4]=='00000001'),
        'pointer_high':next(i for i,r in enumerate(rows) if r[0]=='W' and r[3]=='14'),
        'wrong_start':next(i for i,r in enumerate(rows) if r[0]=='W' and r[3]=='00'),
        'wrong_output':next(i for i,r in enumerate(rows) if r[0]=='R' and r[3]=='60')}
    for label,index in indexes.items():
        bad=[*rows];bad[index]=[*rows[index]];bad[index][4]='00000000' if label in ['missing_fresh_valid','wrong_start','wrong_output'] else '00000001'
        assert bad[index]!=rows[index]
        try:review_control(scenarios,bad)
        except AssertionError:rejected.append(label)
        else:raise AssertionError('Accepted '+label)
    bad=[*rows];bad[0]=[*rows[0]];bad[0][4]='0000008c'
    try:review_control(scenarios,bad)
    except AssertionError:rejected.append('stale_autorestart')
    else:raise AssertionError('Accepted stale autorestart')
    auditor=ROOT/'tools/review_d64_state_payload_20261104.py'
    out=dict(state='PASS_SYNTHETIC_STATE_PAYLOAD_AND_CONTROL_AUDITOR_CONTROLS_ONLY',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        valid_synthetic_cases=results,synthetic_control=control,negative_controls_rejected=rejected,
        source_sha256=hashlib.sha256(auditor.read_bytes()).hexdigest(),manifest_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        evidence_scope='Images and register rows constructed from frozen Csim references; NOT RTL/model/tool outputs.',
        not_proven=['Tool/source/process origin','Actual AXI address-span bounds','New model qualification','RTL calls and state/mode correctness','Performance'],
        eda='NOT_RUN',board='NOT_RUN',automatic_next_stage=False)
    target=R/'HOST_AUDITOR_SYNTHETIC_PRECHECK.json';assert not target.exists()
    target.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='valid_synthetic_cases'},indent=2))
if __name__=='__main__':main()
