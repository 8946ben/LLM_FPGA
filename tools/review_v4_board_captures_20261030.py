"""Independent direct raw record audit; no target operations or shared parser."""
from pathlib import Path
import json,struct,hashlib,statistics,math,zlib
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/dual_board_20261030_r1';rows=[]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for variant,base,signature in [('baseline_hybrid',M,0x4d345301),('exp10',M/'experiments/fusion_exp10_20261023',0x4d345a0a)]:
    for case in ['chinese','english','code','math']:
        d=base/'reports/board_acceptance_20261030_r3'/case
        if not (d/'CAPTURE_RESULT.json').exists():continue
        q=(d/'request.bin').read_bytes();h=(d/'header.bin').read_bytes();raw=(d/'records.bin').read_bytes()
        assert len(q)==len(h)==128 and h[:48]==q[:48]
        request=struct.unpack('<16I4Q8I',q);head=struct.unpack('<16I4Q8I',h)
        assert request[:8]==(0x5450344d,1,128,0,request[4],3,30,1000)
        assert head[12:16]==(0,3,1033,0xffffffff) and head[20]==signature and head[21]&1 and head[22]&0x85==4
        hz=head[16];assert hz>0 and head[19]>head[18] and head[17]>0
        assert len(raw)==1033*128
        times=[];last=None;expected=request[8:11];counts=set()
        assert zlib.crc32(struct.pack('<II',*expected[:2]))==expected[2]
        for i,x in enumerate(struct.iter_unpack('<16I8Q',raw)):
            kind=0 if i<3 else 1 if i<33 else 2
            assert x[:6]==(i,kind,0,0,6,0) and x[9:14]==(*expected,1,0)
            assert x[14:16]==(0,0) and x[19:]==(0,)*5
            assert 0<x[6]<=151936 and 0<x[7]<=151936 and x[8] in (0,1)
            start,end,wait=x[16:19];assert head[18]<=start<end<=head[19]
            assert last is None or start>=last;last=end
            assert wait*hz<=(end-start)*1000000+hz
            counts.add(x[7])
            if kind==1:times.append(end-start)
        assert len(times)==30 and len(counts)==1
        median=statistics.median(times)*1000/hz;p95=sorted(times)[math.ceil(.95*30)-1]*1000/hz
        recorded=read(d/'CAPTURE_RESULT.json')
        assert abs(recorded['token_ready_median_ms']-median)<1e-10 and abs(recorded['token_ready_p95_ms']-p95)<1e-10
        transfer=read(d/'TRANSFER.json');plan=read(d/'PLAN.json')
        assert transfer['bytes']==335544320 and transfer['target_read_checks']==34 and transfer['image_sha256']==plan['image_sha256'] and transfer['target_crc32']==plan['arena_crc32']
        log=(d/'campaign.log').read_text(errors='replace')
        assert 'M4_GEM_STOP_READBACK=PASS' in log and 'M4_PRIVATE_CAPTURE_COMPLETE_PENDING_HOST_VALIDATION' in log and 'M4_PRIVATE_BOARD_ERROR:' not in log
        row=dict(variant=variant,case=case,state='PASS_FIXED_INPUT_TARGET_TRANSFER_AND_1033_OUTPUT_CALLS',median_ms=median,p95_ms=p95,m14_equivalent_outputs_per_s=1000/median,candidate_count=next(iter(counts)),measured=30,warmup=3,stability=1000,sha256={p.name:sha(p) for p in [d/'request.bin',d/'header.bin',d/'records.bin']},timing_scope='A53 full control_call through verified scalar return; fixed preloaded hidden/history; no IP-cycle counter/full LLM/TTFT',full_array_and_multistep_qualification='PENDING_SEPARATE_TEST')
        (d/'INDEPENDENT_REVIEW.json').write_text(json.dumps(row,indent=2)+'\n');rows.append(row)
result=dict(state='REVIEW_AVAILABLE_FIXED_INPUT_CAPTURES_ONLY',completed_cases=len(rows),rows=rows,full_board_acceptance=False)
(R/'BOARD_FIXED_INPUT_SUMMARY.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
