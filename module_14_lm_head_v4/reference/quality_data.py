from pathlib import Path
import hashlib,json
import numpy as np


def load_split(folder):
    folder=Path(folder);manifest=json.loads((folder/'MANIFEST.json').read_text(encoding='utf-8'))
    if manifest['state']!='PASS':raise ValueError('Collection must finish before quality evaluation')
    hidden=[];top=[];winner=[];category=[];groups=[];decode=[];seen=[];prompt_ids=[]
    for row in manifest['records']:
        if 'excluded' in row:continue
        p=folder/row['npz']
        if hashlib.sha256(p.read_bytes()).hexdigest()!=row['npz_sha256']:raise ValueError('Collected tensor SHA mismatch')
        with np.load(p,allow_pickle=False) as a:
            h=a['hidden_bf16'];t=a['raw_top_ids'];w=a['dense_token'];inputs=a['input_ids']
            if h.dtype!=np.uint16 or h.shape!=(row['steps'],896) or t.shape!=(row['steps'],256) or w.shape!=(row['steps'],):raise ValueError('Invalid collected shape')
            if np.any(t>=151936) or np.any(w>=151936) or np.any(inputs>=151936):raise ValueError('Collected ID out of bounds')
            hidden.append(h.copy());top.append(t.copy());winner.append(w.copy())
            current=set(map(int,inputs))
            for step in range(len(h)):
                seen.append(np.array(sorted(current),dtype='u4'));current.add(int(w[step]))
            category.extend([row['category']]*len(h));groups.extend([row['group_sha256']]*len(h));prompt_ids.extend([row['id']]*len(h));decode.extend([False]+[True]*(len(h)-1))
    if not hidden:raise ValueError('No valid hidden records')
    return dict(hidden=np.concatenate(hidden),raw_top_ids=np.concatenate(top),winner=np.concatenate(winner),
        category=np.array(category),groups=np.array(groups),prompt_ids=np.array(prompt_ids),decode=np.array(decode),seen=seen,
        manifest=manifest,manifest_sha256=hashlib.sha256((folder/'MANIFEST.json').read_bytes()).hexdigest())


def assert_group_disjoint(*splits):
    owner={}
    for index,data in enumerate(splits):
        for group in set(data['groups']):
            if group in owner:raise ValueError('Prompt-group leakage between quality splits')
            owner[group]=index


def assert_compatible_collections(*splits):
    keys=('model_lock_sha256','canonical_weight_sha256','collector_sha256','gpu_head_sha256',
        'torch','transformer_dtype','head_dtype','penalty','system_prompt','max_input_tokens','max_new_tokens','raw_top_k')
    if not splits:raise ValueError('No collection settings')
    expected={k:splits[0]['manifest']['settings'][k] for k in keys}
    if expected['penalty']!=1.1 or expected['raw_top_k']!=256 or expected['head_dtype']!='FP32_H8_INTERLEAVE16_SEPARATE_MULTIPLY_ADD':
        raise ValueError('Unsupported label precision/policy for evaluator')
    for data in splits[1:]:
        if {k:data['manifest']['settings'][k] for k in keys}!=expected:raise ValueError('Mixed model/policy/source collection settings')


def recall_report(hits,data):
    hits=np.asarray(hits,dtype=bool)
    if hits.shape!=data['winner'].shape:raise ValueError('Recall count mismatch')
    result={}
    for phase,mask in [('all',np.ones(len(hits),dtype=bool)),('decode',data['decode']),('prefill',~data['decode'])]:
        by_category={}
        for category in sorted(set(data['category'])):
            selected=mask & (data['category']==category)
            by_category[str(category)]=dict(steps=int(selected.sum()),misses=int((~hits[selected]).sum()),recall=float(hits[selected].mean()) if selected.any() else None)
        result[phase]=dict(steps=int(mask.sum()),misses=int((~hits[mask]).sum()),recall=float(hits[mask].mean()) if mask.any() else None,by_category=by_category)
    # Prompt bootstrap, rather than pretending neighboring tokens independent.
    totals=[];success=[]
    for group in sorted(set(data['groups'])):
        mask=(data['groups']==group)&data['decode']
        if mask.any():totals.append(int(mask.sum()));success.append(int(hits[mask].sum()))
    if totals:
        totals=np.array(totals);success=np.array(success);rng=np.random.default_rng(20261021)
        samples=rng.integers(len(totals),size=(300,len(totals)))
        estimates=success[samples].sum(axis=1)/totals[samples].sum(axis=1)
        result['decode_prompt_bootstrap_interval95']=np.quantile(estimates,[.025,.975]).tolist()
        n=len(totals);rate=float(np.mean(success==totals));z=1.959963984540054
        center=(rate+z*z/(2*n))/(1+z*z/n)
        half=z*np.sqrt(rate*(1-rate)/n+z*z/(4*n*n))/(1+z*z/n)
        result['complete_prompt_decode_match']=dict(prompts=n,all_steps_match_prompts=int(np.sum(success==totals)),
            rate=rate,wilson_interval95=[max(0,center-half),min(1,center+half)])
        result['uncertainty_note']='Prompt bootstrap describes this sample; with zero misses it degenerates to [1,1] and is not a zero-risk certificate. Wilson interval is for whole-prompt exact-match events assuming independent prompt groups; semantic/template correlation and pretraining contamination remain unmeasured.'
    result['prompt_groups']=len(set(data['groups']))
    return result


def penalty_aware_target_ranks(preview,winners,seen_ids,mandatory=(),penalty=1.1):
    """Offline membership evaluator for stable global-ID top-K preview.

The dense label is used only to evaluate its rank; this is not an online
selector or a top-K latency measurement. Mandatory-ID union is accounted for.
"""
    scores=np.asarray(preview,dtype=np.float32).copy();winners=np.asarray(winners)
    if scores.ndim!=2 or winners.shape!=(len(scores),) or len(seen_ids)!=len(scores):raise ValueError('Preview/target/history shape mismatch')
    if winners.dtype.kind not in 'iu' or np.any(winners<0) or np.any(winners>=scores.shape[1]):raise ValueError('Global target out of bounds')
    if not np.all(np.isfinite(scores)) or not np.isfinite(penalty) or penalty<1:raise ValueError('Nonfinite preview/invalid penalty')
    global_ids=np.arange(scores.shape[1],dtype='u4');required=set(map(int,mandatory));ranks=[]
    if any(i<0 or i>=scores.shape[1] for i in required):raise ValueError('Required token out of bounds')
    for row,(winner,seen) in enumerate(zip(winners,seen_ids)):
        seen=np.asarray(seen)
        if seen.dtype.kind not in 'iu' or seen.ndim!=1 or np.any(seen<0) or np.any(seen>=scores.shape[1]):raise ValueError('History ID out of bounds')
        values=scores[row,seen]
        scores[row,seen]=np.where(values<0,values*np.float32(penalty),values/np.float32(penalty))
        target=scores[row,winner]
        rank=int(np.count_nonzero(scores[row]>target)+np.count_nonzero((scores[row]==target)&(global_ids<winner)))
        ranks.append(-1 if int(winner) in required else rank)
    return np.array(ranks,dtype=np.int64)
