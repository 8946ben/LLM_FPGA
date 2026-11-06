"""Independently recompute new pilot GPU labels with the frozen CPU model."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
M=Path(__file__).resolve().parents[1];ROOT=M.parent;sys.path.insert(0,str(M))
from reference.numeric_contract import compute_raw_logits,apply_repetition_penalty

def main():
    folder=M/'data/hidden_pilot_v2/calibration';manifest=json.loads((folder/'MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['state']=='PASS' and manifest['prompts']==4
    weights=np.memmap(ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin',dtype='<u2',mode='r',shape=(151936,896))
    checks=[]
    for record in manifest['records']:
        path=folder/record['npz'];assert hashlib.sha256(path.read_bytes()).hexdigest()==record['npz_sha256']
        with np.load(path,allow_pickle=False) as data:
            seen=set(map(int,data['input_ids']))
            for index,hidden in enumerate(data['hidden_bf16']):
                raw=compute_raw_logits(hidden,weights);history=np.zeros(4748,dtype='u4')
                for token in seen:history[token>>5]|=np.uint32(1<<(token&31))
                scores=apply_repetition_penalty(raw,history,1.1);winner=int(np.argmax(scores))
                assert winner==data['dense_token'][index] and int(scores[winner].view('u4'))==data['dense_score_bits'][index]
                # Independent full stable sorting, rather than the collector's partition implementation.
                top=np.argsort(-raw,kind='stable')[:256].astype('u4')
                np.testing.assert_array_equal(top,data['raw_top_ids'][index])
                checks.append(dict(prompt_id=record['id'],step=index,winner=winner,score_bits=int(scores[winner].view('u4')),top256_ids_exact=True))
                seen.add(winner);print(f"PILOT_LABEL_CPU_PASS {record['category']} step={index}",flush=True)
    result=dict(state='PASS',prompts=4,steps=len(checks),checks=checks,scope='New collected BF16 hidden labels recomputed with accepted CPU FP32 arithmetic; not full transformer equivalence or quality',hardware_access='NONE')
    (M/'reports/PILOT_LABEL_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('PILOT_LABEL_AUDIT=PASS',flush=True)
if __name__=='__main__':main()
