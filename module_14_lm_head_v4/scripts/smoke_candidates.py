"""Real canonical 8-step candidate arithmetic regression; never selector quality."""
from pathlib import Path
import hashlib,json,sys,time
import numpy as np
M=Path(__file__).resolve().parents[1];ROOT=M.parent
sys.path.insert(0,str(M))
from reference.candidate_head import run_candidate_head,encode_candidate_table,decode_candidate_table

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assets=ROOT/'artifacts/module14_v2_assets';manifest=json.loads((assets/'manifest.json').read_text(encoding='utf-8'))
    out=M/'reports/candidate_smoke_20261021';out.mkdir(parents=True,exist_ok=True)
    weight_file=assets/'shared_vocab_weight.bf16.bin'
    assert sha(weight_file)==manifest['weight_sha256']=='4e96b0df6d274768cbb7e72404011853d23349999b658dc2f4dfb3c431ea223f'
    baseline_ref=ROOT/'deliverables/20261020_M14_V3_1_r1/M14_V3_1_20261020_r1/module_14_lm_head_v3_1/reference/lm_head_v2_ref.py'
    assert sha(M/'reference/numeric_contract.py')==sha(baseline_ref)
    weights=np.memmap(weight_file,dtype='<u2',mode='r',shape=(151936,896))
    rows=[]
    for step_index,gold in enumerate(manifest['trace']):
        d=assets/'trace'/gold['step'];print('SMOKE_BEGIN '+gold['step'],flush=True)
        for filename,key in [('hidden.bf16.bin','hidden_sha256'),('history_bitmap.u32.bin','history_sha256'),('raw_logits.fp32.bin','raw_logits_sha256'),('processed_scores.fp32.bin','processed_scores_sha256')]:
            assert sha(d/filename)==gold[key]
        hidden=np.fromfile(d/'hidden.bf16.bin',dtype='<u2');history=np.fromfile(d/'history_bitmap.u32.bin',dtype='<u4')
        raw=np.fromfile(d/'raw_logits.fp32.bin',dtype='<f4');scores=np.fromfile(d/'processed_scores.fp32.bin',dtype='<f4')
        sets=[('all_vocab_identity',np.arange(151936,dtype='u4'))]
        rng=np.random.default_rng(20261021+step_index)
        sets += [('seeded_random_'+str(k),np.sort(rng.choice(151936,size=k,replace=False)).astype('u4')) for k in (2048,4096,8192,16384)]
        sets += [('boundary_ids',np.array([0,1,31,32,127,128,255,256,65535,65536,151934,151935],dtype='u4'))]
        for kind,ids in sets:
            encoded=encode_candidate_table(ids,151936);ids=decode_candidate_table(encoded,151936)
            started=time.perf_counter();got=run_candidate_head(hidden,weights,ids,history,penalty=1.1);seconds=time.perf_counter()-started
            np.testing.assert_array_equal(got['raw_scores'].view('u4'),raw[ids].view('u4'))
            np.testing.assert_array_equal(got['policy_scores'].view('u4'),scores[ids].view('u4'))
            if len(ids)==151936:
                assert got['selected_token']==gold['selected_token'] and got['selected_score_bits']==gold['selected_score_bits'] and got['output_crc']==gold['output_crc']
                assert hashlib.sha256(got['raw_scores'].astype('<f4').tobytes()).hexdigest()==gold['raw_logits_sha256']
                assert hashlib.sha256(got['policy_scores'].astype('<f4').tobytes()).hexdigest()==gold['processed_scores_sha256']
            if kind=='seeded_random_4096':
                (out/(gold['step']+'.candidate_table.bin')).write_bytes(encoded)
                got['records'].tofile(out/(gold['step']+'.candidate_scores.bin'))
            rows.append(dict(step=gold['step'],case=kind,k=len(ids),raw_bits_exact=True,policy_bits_exact=True,
                selected_global_id=got['selected_token'],dense_winner_present=bool(np.any(ids==gold['selected_token'])),
                winner_matches_dense=got['selected_token']==gold['selected_token'],cpu_reference_seconds=seconds,
                logical_weight_bytes=got['logical_weight_bytes'],logical_candidate_id_bytes=got['logical_candidate_id_bytes'],
                output_coverage=got['output_coverage']))
            print(f"SMOKE_PASS {gold['step']} {kind} K={len(ids)}",flush=True)
        (out/'partial.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
    result=dict(state='PASS',scope='CPU candidate arithmetic and format only',steps=8,cases=len(rows),
        canonical_weight_sha256=manifest['weight_sha256'],numeric_reference_sha256=sha(M/'reference/numeric_contract.py'),
        candidate_source_sha256=sha(M/'reference/candidate_head.py'),rows=rows,
        selector_quality='NOT_EVALUATED: seeded random ID lists are test fixtures, not an online selector',
        fpga_performance='NOT_RUN: CPU seconds are not FPGA latency or decode throughput',
        hardware_access='NONE',full_generation='NOT_RUN',hidden_size=896,vocab_size=151936)
    (out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('V4_CANDIDATE_SMOKE=PASS cases='+str(len(rows)),flush=True)

if __name__=='__main__':main()
