"""Synthetic positive/negative controls of the host auditor, NEVER RTL evidence."""
from pathlib import Path
import csv,hashlib,json,datetime
from review_d64_native_gate_20261104 import replay
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4'
R=M/'reports/d64_native_memory_20261103_r1'

def main():
    folder=R/'auditor_synthetic_controls';assert not folder.exists();folder.mkdir()
    base=0x100000000;rows=[];memory={};cycle=0;counts=dict(AR=0,R=0,AW=0,W=0,B=0)
    def add(kind,*fields):
        nonlocal cycle
        cycle+=1;rows.append([kind,str(cycle),*map(str,fields)])
        if kind in counts:counts[kind]+=1
    def write(addr,length,ident,seed,mask,b_response=True):
        add('AW','%016x'%addr,length-1,ident)
        for beat in range(length):
            data=[(seed*37+beat*19+lane*11)%256 for lane in range(16)]
            add('W',''.join('%02x'%x for x in reversed(data)),'%04x'%mask,int(beat==length-1))
            for lane,value in enumerate(data):
                if mask&(1<<lane):memory[addr+beat*16+lane]='%02x'%value
        if b_response:add('B',ident,0)
    def read(addr,length,ident,complete=True):
        add('AR','%016x'%addr,length-1,ident)
        if complete:
            for beat in range(length):
                data=[memory.get(addr+beat*16+lane,'xx') for lane in range(16)]
                add('R',''.join(reversed(data)),int(beat==length-1),ident,0)
    write(base,4,0,1,65535);write(base+0x20000000,4,1,9,65535)
    read(base,4,0);read(base+0x20000000,4,1)
    write(base+1048560,1,1,2,65535);write(base+1048576,2,0,3,65535)
    read(base+1048560,1,1);read(base+1048576,2,0)
    write(base+16,1,1,4,0x5aa5);read(base,4,0)
    write(base,1,0,8,0);read(base,1,1)
    write(base+8192,1,1,6,255);read(base+8192,1,1)
    write(base+8208,1,0,7,0);read(base+8208,1,0)
    read(base+536870960,1,1)
    # Serialization in this synthetic control is intentional; concurrency needs real SV.
    read(base,4,0);write(base+16384,8,1,11,65535);read(base+16384,8,1)
    read(base,4,1,False);add('RESET');read(base,4,1)
    write(base+24576,1,0,13,65535,False);add('RESET');read(base+24576,1,0)
    write(base+32768,128,0,21,65535);add('EPOCH',0)
    for epoch in range(1,5):
        for rep in range(256):read(base+32768,128,rep%2)
        add('EPOCH',epoch)
    add('DONE',*(counts[k] for k in ['AR','R','AW','W','B']))
    def save(path,data):
        with path.open('w',newline='') as f:csv.writer(f).writerows(data)
    positive=folder/'SYNTHETIC_NOT_RTL_positive.csv';save(positive,rows)
    result=replay(positive)
    first_r=next(i for i,r in enumerate(rows) if r[0]=='R')
    first_w=next(i for i,r in enumerate(rows) if r[0]=='W')
    first_ar=next(i for i,r in enumerate(rows) if r[0]=='AR')
    first_b=next(i for i,r in enumerate(rows) if r[0]=='B')
    unknown=next(i for i,r in enumerate(rows) if r[0]=='R' and 'x' in r[2])
    reset=next(i for i,r in enumerate(rows) if r[0]=='RESET')
    edits=[('read_bit',first_r,2,'0'*32),('read_id',first_r,4,'1'),('read_last',first_r,3,'1'),
           ('read_response',first_r,5,'2'),('write_mask',first_w,3,'0000'),
           ('read_range',first_ar,2,'%016x'%(base-16)),('read_4k',first_ar,2,'%016x'%(base+4080)),
           ('b_id',first_b,2,'1'),('unknown_coerced_zero',unknown,2,rows[unknown][2].replace('x','0')),
           ('wrong_reset_event',reset,0,'EPOCH'),('false_done_count',len(rows)-1,3,'0')]
    rejected=[]
    for name,index,column,value in edits:
        bad=[*rows];bad[index]=[*rows[index]];assert bad[index][column]!=value
        bad[index][column]=value;target=folder/('SYNTHETIC_NOT_RTL_'+name+'.csv');save(target,bad)
        try:replay(target)
        except (AssertionError,ValueError,IndexError):rejected.append(name)
        else:raise AssertionError('Auditor accepted '+name)
    assert len(rejected)==len(edits)
    auditor=ROOT/'tools/review_d64_native_gate_20261104.py'
    out=dict(state='PASS_SYNTHETIC_HOST_AUDITOR_CONTROLS_ONLY',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        positive=result,negative_controls_rejected=rejected,auditor_sha256=hashlib.sha256(auditor.read_bytes()).hexdigest(),
        evidence_scope='Manually generated desired-protocol trace, not tool output. Tests host replay behavior only.',
        not_proven=['SV compilation','Actual native model AXI semantics','Backpressure/concurrency timing','M14','Performance'],
        eda='NOT_RUN',board='NOT_RUN')
    (R/'AUDITOR_SYNTHETIC_PRECHECK.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
if __name__=='__main__':main()
