"""Prepared host replay of per-frame accepted AXI address requests, no tool claims."""
from pathlib import Path
import csv,hashlib

def replay_requests(path,metrics,summary_path=None):
    assert len(metrics)==12
    counts=[[0]*7 for _ in range(12)]
    previous_tick=-1;previous_frame=-1;requests=0
    for event,frame,tick,address,length in csv.reader(Path(path).open()):
        frame,tick,address,length=int(frame),int(tick),int(address,16),int(length)
        assert 0<=frame<12 and frame>=previous_frame and tick>=previous_tick
        previous_frame,previous_tick=frame,tick
        assert event in ['MR','MW','WR'] and 0<=length<128 and address%16==0
        end=address+16*(length+1)
        assert 0<=address<end<2**64 and address%4096+16*(length+1)<=4096
        c=counts[frame];requests+=1
        if event=='MR':
            assert end<=1289456 and frame not in [5,6]
            if frame in [7,8,9]:assert end<=24368
            c[0]+=1;c[1]+=length+1
        elif event=='MW':
            assert 24368<=address<end<=1289456 and frame not in [5,6,7,8,9]
            c[2]+=1;c[3]+=length+1
        else:
            assert end<=545685504 and frame not in [5,6,7,8,9]
            assert not address<273416192<end
            if frame==10:assert end<=273416192
            c[4]+=1;c[5]+=length+1
            if address>=273416192:c[6]+=1
    for i,(c,m) in enumerate(zip(counts,metrics,strict=True)):
        assert m['case']==i
        assert [c[1],c[3],c[5],c[6]]==[m['meta_reads'],m['meta_writes'],m['weight_reads'],m['canonical_requests']]
        # Native gate must first establish that accepted bursts complete faithfully.
        if i not in [5,6]:assert c[0]>0
        if i not in [5,6,7,8,9]:assert c[2]>0 and c[4]>0
    if summary_path is not None:
        summary=[[int(x) for x in row] for row in csv.reader(Path(summary_path).open())]
        assert summary==[[i,*c] for i,c in enumerate(counts)]
    return dict(scope='ACCEPTED_ADDRESS_REQUEST_REPLAY_ONLY',requests=requests,counts_by_frame=counts,
                trace_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                not_proven=['Data values','Actual simulator/source provenance','Native response model qualification','Timing'])

if __name__=='__main__':
    raise SystemExit('Prepared pure replay function only; full suite qualification requires bound actual tool/process/model/numeric artifacts.')
