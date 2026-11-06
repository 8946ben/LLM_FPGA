"""Actual GPU packed-buffer pipelines with same-round BF16 control.

GPU reference only, no FPGA or whole-transformer performance inference.
"""
from pathlib import Path
import json,os,statistics,struct,time,zlib
import run_quantization as R
import numpy as np
import torch
P=R.local('packed_cuda')

@torch.inference_mode()
def main():
    torch.set_num_threads(4);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    R.checked();R.stop();assert (R.OUT/'METHODS_CALIBRATION.json').exists()
    screen=json.loads((R.OUT/'REFINE_CALIBRATION.json').read_text())
    entries=[dict(id='DENSE_BF16',kind='dense')]
    for b in [4,8]:
        entries.append(dict(id=f'DIRECT_W{b}',kind='direct',source=f'RTN_W{b}_G128_S'))
        eligible=[p for p in screen['configurations'] if p['preview']==f'RTN_W{b}_G128_S' and p['conservative_calibration_gate'] and p['K']<151936]
        if eligible:
            k=min(p['K'] for p in eligible);entries.append(dict(id=f'REFINE_W{b}_K{k}',kind='refine',source=f'RTN_W{b}_G128_S',K=k))
    direct=[]
    for path in (R.OUT/'points').glob('*/RESULT.json'):
        p=json.loads(path.read_text())
        if p['conservative_calibration_gate'] and p['method']=='RTN':direct.append(p)
    if direct:
        best=min(direct,key=lambda p:(p['packed_bytes'],p['id']))
        if best['id'] not in [e.get('source') for e in entries]:entries.append(dict(id='CALIBRATION_QUALIFIED_DIRECT',kind='direct',source=best['id']))
    protocol=dict(source_sha256=R.sha(Path(__file__)),packed_source_sha256=R.sha(R.M/'reference/packed_cuda.py'),
      core_entry_sha256=R.sha(R.OUT/'ENTRY_LOCK.json'),methods_entry_sha256=R.sha(R.OUT/'METHODS_ENTRY_LOCK.json'),
      entries=entries,cases=R.CASES,warmup=3,measurements=30,
      schedule='30 rounds, input and method order cyclically rotated; batch1',
      boundary='resident packed W/BF16 W and h/history -> actual unpack/dot/policy/(TopK/gather/refine) -> CPU token/score/CRC; pre-call sync',
      excluded='initialization, compilation, model forward, upload and corpus collection',
      baseline='same-round BF16-buffer read with identical H8 arithmetic; not previous Eager benchmark')
    entrypath=R.OUT/'BENCHMARK_ENTRY_LOCK.json'
    assert not (R.OUT/'GPU_BENCHMARK.json').exists(),'Completed benchmark cannot be silently overwritten'
    if entrypath.exists():assert json.loads(entrypath.read_text())==protocol
    else:R.write(entrypath,protocol)
    handle=None
    try:
        handle=(R.OUT/'ACTIVE.lock').open('x');handle.write(json.dumps(dict(pid=os.getpid(),phase='packed_benchmark',started=R.now())));handle.flush()
        weights=torch.from_numpy(np.fromfile(R.WEIGHT,dtype='<u2').reshape(151936,896)).view(torch.bfloat16).to('cuda')
        dense_engine=P.PackedCuda(R.OUT/'cuda/packed_dense');fixtures=R.fixtures();payload={}
        penalty=torch.tensor(1.1,device='cuda',dtype=torch.float32)
        for cat,(h,seen) in fixtures.items():
            mask=np.zeros(151936,dtype=bool);mask[seen]=True
            payload[cat]=dict(h=R.gpu(h[None,:]),mask=torch.from_numpy(mask).to('cuda'),seen=torch.from_numpy(seen.astype('i8')).to('cuda'))
        sources={}
        for key in sorted(set(e['source'] for e in entries if 'source' in e)):
            point=json.loads((R.OUT/'points'/key/'RESULT.json').read_text())
            buffer=torch.from_numpy(np.fromfile(R.OUT/'points'/key/'weights.bin',dtype='u1')).to('cuda')
            sources[key]=dict(engine=P.PackedCuda(R.OUT/'cuda'/('packed_'+key),point['packing']),buffer=buffer,point=point)
        def apply(raw,mask):
            return torch.where(mask,torch.where(raw<0,raw*penalty,raw/penalty),raw)
        def call(entry,cat,debug=False):
            p=payload[cat];ids=None;preview=None
            if entry['kind']=='dense':
                raw=dense_engine(weights,p['h'],151936)[0];score=apply(raw,p['mask'])
            else:
                s=sources[entry['source']];preview=s['engine'](s['buffer'],p['h'],151936)[0]
                approximate=apply(preview,p['mask'])
                if entry['kind']=='direct':raw=preview;score=approximate
                else:
                    top=torch.argsort(approximate,descending=True,stable=True)[:entry['K']]
                    ids=torch.sort(top).values;chosen=weights[ids].contiguous()
                    raw=dense_engine(chosen,p['h'],len(ids))[0];score=apply(raw,p['mask'][ids])
            slot=torch.argmax(score);token=int((slot if ids is None else ids[slot]).item());bits=int(score[slot].view(torch.int32).item())&0xffffffff
            result=dict(token=token,score_bits=bits,crc=zlib.crc32(struct.pack('<II',token,bits)))
            if debug:
                result.update(raw=raw.cpu().numpy(),ids=None if ids is None else ids.cpu().numpy(),preview=None if preview is None else preview.cpu().numpy())
            return result
        dense_cache=np.memmap(R.OUT/'dense_calibration.raw.f32',dtype='<f4',mode='r',shape=(5095,151936))
        indices=dict(chinese=1,english=1281,code=2536,math=3816);proof=[];gold={}
        for e in entries:
          for cat,(h,seen) in fixtures.items():
            R.stop();actual=call(e,cat,True)
            if e['kind']=='dense':expected_raw=np.array(dense_cache[indices[cat]])
            else:
                with np.load(R.OUT/'points'/e['source']/f'{cat}.npz',allow_pickle=False) as a:preview=a['raw'].copy()
                np.testing.assert_array_equal(actual['preview'].view('u4'),preview.view('u4'))
                if e['kind']=='direct':expected_raw=preview
                else:
                    scores=R.policy(preview[None,:],[seen])[0];expected_ids=np.sort(np.argsort(-scores,kind='stable')[:e['K']])
                    np.testing.assert_array_equal(actual['ids'],expected_ids)
                    bits=np.memmap(R.WEIGHT,dtype='<u2',mode='r',shape=(151936,896));expected_raw=R.Q.raw_fp32(h,R.fp(bits[expected_ids]))
            np.testing.assert_array_equal(actual['raw'].view('u4'),expected_raw.view('u4'))
            if actual['ids'] is None:score=R.policy(expected_raw[None,:],[seen])[0];slot=int(score.argmax());token=slot
            else:
                ids=actual['ids'];score=expected_raw.copy();mask=np.isin(ids,seen);old=score[mask]
                score[mask]=np.where(old<0,old*np.float32(1.1),old/np.float32(1.1));slot=int(score.argmax());token=int(ids[slot])
            bit=int(score[slot].view('u4'));assert actual['token']==token and actual['score_bits']==bit
            gold[(e['id'],cat)]={k:actual[k] for k in ['token','score_bits','crc']}
            proof.append(dict(method=e['id'],case=cat,full_packed_preview_bits=e['kind']!='dense',full_final_raw_bits=True,
              candidates=None if actual['ids'] is None else len(actual['ids']),**gold[(e['id'],cat)]))
        R.write(R.OUT/'BENCHMARK_NUMERIC_PROOF.json',dict(state='PASS_ACTUAL_PACKED_FULL_ARRAYS_AND_PIPELINES',records=proof,
          scope='4 original calibration fixtures per method, not independent quality or all5095 pipeline replay'))
        records=[]
        for e in entries:
          for cat in R.CASES:
            for _ in range(3):assert call(e,cat)==gold[(e['id'],cat)]
        for round_index in range(30):
          R.stop()
          for ci in range(4):
            cat=R.CASES[(ci+round_index)%4]
            for mi in range(len(entries)):
                e=entries[(mi+round_index+ci)%len(entries)];torch.cuda.synchronize();start=time.perf_counter_ns()
                actual=call(e,cat);elapsed=(time.perf_counter_ns()-start)/1e6
                assert actual==gold[(e['id'],cat)]
                records.append(dict(round=round_index,case=cat,method=e['id'],wall_ms=elapsed,**actual))
          if round_index%5==0:R.progress('PACKED_GPU_TIMING',rounds=round_index+1,total=30,methods=len(entries))
        methods=[]
        for e in entries:
            values=[r['wall_ms'] for r in records if r['method']==e['id']]
            methods.append(dict(**e,samples=len(values),mean_ms=statistics.mean(values),median_ms=statistics.median(values),
              p95_ms=sorted(values)[math_ceil95(len(values))-1],equivalent_outputs_per_second=1000/statistics.mean(values),
              by_case={cat:dict(median_ms=statistics.median([r['wall_ms'] for r in records if r['method']==e['id'] and r['case']==cat])) for cat in R.CASES}))
        R.write(R.OUT/'GPU_TIMING_RAW.json',dict(records=records))
        R.write(R.OUT/'GPU_BENCHMARK.json',dict(state='PASS_PACKED_GPU_REFERENCE_NOT_FPGA',methods=methods,protocol=protocol,
          numeric_proof_sha256=R.sha(R.OUT/'BENCHMARK_NUMERIC_PROOF.json'),raw_timing_sha256=R.sha(R.OUT/'GPU_TIMING_RAW.json'),
          gpu=torch.cuda.get_device_name(),torch=torch.__version__,scope='Independent M14 GPU reference; no Transformer/FPGA/TTFT claim'))
        R.progress('PACKED_GPU_BENCHMARK_COMPLETE',methods=len(entries),measurements=len(records))
    except Exception as exc:R.progress('STOPPED_ON_ERROR_OR_PAUSE',phase='packed_benchmark',error=repr(exc));raise
    finally:
        if handle:handle.close();(R.OUT/'ACTIVE.lock').unlink(missing_ok=True)

def math_ceil95(n):return (95*n+99)//100
if __name__=='__main__':main()
