"""Independent saved-array recount and bounded quantized-screen study."""
from pathlib import Path
import json,struct,zlib
import run_quantization as R
import numpy as np

def main():
    R.checked();_,cal=R.data();points=[]
    assert (R.OUT/'RTN_CALIBRATION.json').exists()
    fixture_indices={'chinese':1,'english':1281,'code':2536,'math':3816};fixtures=R.fixtures()
    for path in sorted((R.OUT/'points').glob('*/RESULT.json')):
        result=json.loads(path.read_text());folder=path.parent
        assert R.sha(folder/'weights.bin')==result['packed_sha256']
        assert R.sha(folder/'outcomes.npz')==result['outcomes_sha256']
        with np.load(folder/'outcomes.npz',allow_pickle=False) as saved:
            token=saved['token'];bits=saved['score_bits'];hits=saved['hits'];ranks=saved['policy_dense_winner_rank']
            np.testing.assert_array_equal(hits,token==cal['winner']);np.testing.assert_array_equal(hits,ranks==0)
            quality=R.statistics(hits,cal);assert quality==result['quality']
            for cat,(hidden,seen) in fixtures.items():
                index=fixture_indices[cat];np.testing.assert_array_equal(hidden.view('u4'),R.fp(cal['hidden'][index]).view('u4'))
                with np.load(folder/f'{cat}.npz',allow_pickle=False) as proof:
                    raw=proof['raw'];score=R.policy(raw[None,:],[seen])[0];winner=int(score.argmax())
                    assert winner==int(token[index])==int(proof['token'])
                    assert int(score[winner].view('u4'))==int(bits[index])==int(proof['score_bits'])
                    target=score[cal['winner'][index]];rank=int((score>target).sum()+((score==target)&(np.arange(151936)<cal['winner'][index])).sum())
                    assert rank==int(ranks[index])
                item=next(x for x in result['cpu_gpu_proof'] if x['case']==cat)
                assert item['crc']==zlib.crc32(struct.pack('<II',winner,int(bits[index])))
        points.append(dict(id=result['id'],packed_sha256=True,arrays_sha256=True,quality_recount=True,four_full_preview_policy_rank_recounts=True))
    R.write(R.OUT/'INDEPENDENT_REVIEW.json',dict(state='PASS_SAVED_ARRAYS_AND_PACKED_IDENTITIES',points=points,
      sources_unchanged=True,calibration_groups=320,scope='Independent counts/ranks from saved arrays, not a new final quality group or RTL'))
    configurations=[]
    for b in [4,8]:
        name=f'RTN_W{b}_G128_S';folder=R.OUT/'points'/name;point=json.loads((folder/'RESULT.json').read_text())
        with np.load(folder/'outcomes.npz',allow_pickle=False) as a:ranks=a['policy_dense_winner_rank'].copy()
        for k in [512,2048,8192,16384,32768,151936]:
            quality=R.statistics(ranks<k,cal)
            configurations.append(dict(preview=name,K=k,quality=quality,conservative_calibration_gate=R.qualified(quality),
              main_read_bytes=point['packed_bytes']-256+1792*k,
              all_max_dense_winner_rank=int(ranks.max()),arrays_sha256=point['outcomes_sha256']))
    R.write(R.OUT/'REFINE_CALIBRATION.json',dict(state='COMPLETE_12_SCREEN_POINTS_CALIBRATION_ONLY',configurations=configurations,
      controls=['BF16_DENSE','RTN_W4_G128_S_DIRECT','RTN_W8_G128_S_DIRECT'],
      selection='After full-global-history penalty, stable low-ID top-K; no mandatory-ID union, clustering or lowrank',
      numeric_condition='If the global dense policy winner is in candidate subset, original canonical arithmetic and low-ID argmax preserve token and score bits.',
      scope='Recall from complete actual preview rankings; not online Top-K timing, not all5095 complete candidate-pipeline replay, no final labels'))
    print('INDEPENDENT_REVIEW_AND_REFINE=PASS')

if __name__=='__main__':main()
