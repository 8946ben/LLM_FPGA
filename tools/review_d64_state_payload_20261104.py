"""Prepared pure payload/control auditors. Tool/source/process qualification is separate.

These functions can check synthetic controls or future real dumps. A function PASS
alone cannot qualify a model, simulator run, complete suite or performance result.
"""
from pathlib import Path
import hashlib,json,re
import numpy as np
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4'
FIXTURE=M/'experiments/partial_hw_20261024/fixtures'
META_WORDS=1523*4;TOTAL_WORDS=80592*4
GUARD=np.frombuffer(bytes.fromhex('efcdab89674523011032547698badcfe'),dtype='<u4')

def read_hex_image(path):
    result=np.empty((80592,4),dtype='<u4')
    with Path(path).open() as source:
        count=0
        for count,line in enumerate(source,1):
            assert count<=80592 and re.fullmatch('[0-9a-fA-F]{32}\n?',line), (count,'unknown/invalid word')
            value=int(line,16)
            for lane in range(4):result[count-1,lane]=(value>>(lane*32))&0xffffffff
    assert count==80592
    return result.reshape(-1)

def reference_arrays(case):
    return {name:np.fromfile(FIXTURE/(case+'.'+name+'.bin'),dtype='<u4') for name in ['dims','preview','keys','ids','raw']}

def review_case(scenario,before,after,metrics):
    assert before.dtype==after.dtype==np.dtype('<u4')
    assert before.shape==after.shape==(TOTAL_WORDS,)
    assert np.array_equal(before[-4:],GUARD) and np.array_equal(after[-4:],GUARD)
    data=(ROOT/scenario['input_path']).read_bytes()
    assert hashlib.sha256(data).hexdigest()==scenario['input_sha256']
    assert before[:META_WORDS].tobytes()==after[:META_WORDS].tobytes()==data
    expected=scenario['expected'];index=scenario['case_index'];debug=scenario['debug']
    assert metrics['case']==index and metrics['label']==scenario['label'] and metrics['debug']==debug
    for measured,key in [('status','expected_status'),('token','token'),('score','score_bits'),('K','k'),('crc','crc')]:
        assert metrics[measured]==expected[key],(measured,metrics[measured],expected[key])
    assert metrics['total_starts']==index+1
    assert 0<metrics['ip_cycles']<=metrics['control_call_cycles']
    for field in ['meta_reads','meta_writes','weight_reads','canonical_requests','raw_write_beats']:
        assert isinstance(metrics[field],int) and metrics[field]>=0
    b=before[META_WORDS:-4];a=after[META_WORDS:-4]
    raw_slice=slice(76997*4,79052*4)
    if expected['expected_status']!=0:
        assert metrics['canonical_requests']==0 and metrics['raw_write_beats']==0
        assert np.array_equal(b[raw_slice],a[raw_slice])
        if index in [5,6,7,8,9]:
            assert metrics['weight_reads']==metrics['meta_writes']==0
            assert np.array_equal(b,a), 'Early error changed workspace'
            if index in [5,6]:assert metrics['meta_reads']==0
            else:assert metrics['meta_reads']>0 # Error metadata loads have no fixed-count contract.
        else:
            assert index==10 and metrics['weight_reads']==1220608 and metrics['meta_writes']>0
        return dict(scope='ERROR_OUTPUTS_AND_WORKSPACE_SIDE_EFFECTS_ONLY',case=index,
                    address_span_audit='SEPARATE_ACTUAL_AXI_REQUEST_GUARD_REQUIRED')
    arrays=reference_arrays(scenario['fixture']);k=expected['k']
    dims=a[79052*4:79052*4+64];preview=a[37984*4:37984*4+151936];keys=a[:151936]
    ids=a[75969*4:75969*4+k]
    for field,value in [('dims',dims),('preview',preview),('keys',keys),('ids',ids)]:
        assert np.array_equal(value,arrays[field]),field
    assert np.array_equal(a[75968*4:75969*4],np.array([0x4449344d,0x00040001,k,151936],dtype='<u4'))
    assert np.all(a[75969*4+k:75969*4+((k+3)//4)*4]==0xffffffff)
    assert metrics['meta_reads']>=1523 and metrics['meta_writes']>0
    assert metrics['weight_reads']>=1220608+112*k and metrics['canonical_requests']>0
    if debug==0:
        assert metrics['raw_write_beats']==0 and np.array_equal(b[raw_slice],a[raw_slice])
        return dict(scope='COMMON_ARRAYS_WITH_NO_RAW_OUTPUT_AND_RAW_REGION_PRESERVED',case=index,k=k)
    pairs=a[76997*4:76997*4+2*k].reshape(k,2)
    assert np.array_equal(pairs[:,0],ids) and np.array_equal(pairs[:,1],arrays['raw'])
    if k&1:assert np.all(a[76997*4+2*k:76997*4+2*k+2]==0)
    assert metrics['raw_write_beats']>0
    assembled=np.concatenate([np.array([metrics['token'],metrics['score'],metrics['crc'],k],dtype='<u4'),
                              dims,preview,keys,ids,pairs[:,1]])
    digest=hashlib.sha256(assembled.tobytes()).hexdigest()
    assert digest==expected['debug1_assembled_sha256']
    return dict(scope='ALL_DEFINED_DEBUG_ARRAYS_AND_SCALARS_BIT_EXACT',case=index,k=k,assembled_sha256=digest)

def review_control(scenarios,rows):
    """rows are actual R/W,frame,cycle,address_hex,value_hex transactions."""
    parsed=[];previous_cycle=-1
    for row in rows:
        assert len(row)==5 and row[0] in ['R','W']
        op,frame,cycle,address,value=row[0],int(row[1]),int(row[2]),int(row[3],16),int(row[4],16)
        assert cycle>=previous_cycle and 0<=address<256 and 0<=value<=0xffffffff
        previous_cycle=cycle;parsed.append((op,frame,address,value))
    pointer=0;poll_counts=[]
    for s in scenarios:
        frame=s['case_index']
        def take(op,address,expected=None):
            nonlocal pointer
            assert pointer<len(parsed)
            actual,got_frame,got_address,value=parsed[pointer];pointer+=1
            assert (actual,got_frame,got_address)==(op,frame,address)
            if expected is not None:assert value==expected,(frame,op,address,value,expected)
            return value
        value=take('R',0);assert value&0x85==4
        validity=[0x54,0x64,0x74,0x84,0x94,0xa8]
        for address in validity:
            assert take('R',address) in [0,1];take('R',address,0)
        for address,value in [(0x10,0),(0x14,0),(0x1c,0),(0x20,0),(0x28,273416192),(0x2c,0),
                              (0x34,24368),(0x38,0),(0x40,s['capacity']),(0x48,s['debug'])]:
            take('W',address,value);take('R',address,value)
        take('W',0,1);polls=0
        while True:
            value=take('R',0);polls+=1;assert value&0x80==0
            if value&2:break
        poll_counts.append(polls)
        for address in validity:take('R',address,1);take('R',address,0)
        e=s['expected']
        for address,value in [(0x50,e['expected_status']),(0x60,e['token']),(0x70,e['score_bits']),
                              (0x80,e['k']),(0x90,e['crc']),(0xa0,1220608 if e['expected_status']==0 else 0),(0xa4,0)]:
            take('R',address,value)
        value=take('R',0);assert value&0x87==4
    assert pointer==len(parsed)
    return dict(scope='REGISTER_TRACE_REPLAY_ONLY',calls=len(scenarios),poll_counts=poll_counts)

if __name__=='__main__':
    raise SystemExit('Prepared functions only. Real suite acceptance still requires completed tool/process/source/model gates and bound actual artifacts.')
