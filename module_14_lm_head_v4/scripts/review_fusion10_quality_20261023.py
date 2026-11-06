"""Read-only independent counts/source review; no quality re-evaluation or fitting."""
from pathlib import Path
import hashlib,json
import numpy as np
M=Path(__file__).resolve().parents[1];R=M/'reports/fusion_exp10_20261023_r1';D=M/'data/fusion10_quality_20261023'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    entry=read(D/'EVALUATION_ENTRY_LOCK.json');out=read(R/'FINAL_QUALITY.json');reservation=read(D/'MANIFEST.json');collection=M/'data/hidden_fusion10_20261023/holdout';manifest=read(collection/'MANIFEST.json')
    assert sha(R/'SELECTION_LOCK.json')==entry['selection_lock_sha256']==out['selection_lock_sha256']
    assert sha(D/'EVALUATION_ENTRY_LOCK.json')==out['entry_lock_sha256'];assert sha(collection/'MANIFEST.json')==out['collection_manifest_sha256']
    for name,h in entry['source_sha256'].items():assert sha(M/name)==h,name
    for name,h in reservation['prior_prompt_files_sha256'].items():assert sha(M/name)==h,name
    corpus=[json.loads(s) for s in (D/'holdout.jsonl').read_text(encoding='utf-8').splitlines()]
    assert sha(D/'holdout.jsonl')==entry['corpus_sha256']==reservation['corpus_sha256'];assert manifest['state']=='PASS' and manifest['excluded_prompts']==0
    def groups(rows,key):return {r[key] for r in rows}
    for name in reservation['prior_prompt_files_sha256']:
        old=[json.loads(s) for s in (M/name).read_text(encoding='utf-8').splitlines()]
        for key in ['group_sha256','prompt_sha256']:assert not groups(corpus,key)&groups(old,key),name
    assert len(corpus)==len(manifest['records'])==1000
    expected={r['id']:(r['group_sha256'],r['prompt_sha256'],r['category']) for r in corpus};category=[];decode=[];ids=[]
    for row in manifest['records']:
        assert (row['group_sha256'],row['prompt_sha256'],row['category'])==expected[row['id']] and 'excluded' not in row
        p=collection/row['npz'];assert sha(p)==row['npz_sha256']
        with np.load(p,allow_pickle=False) as a:
            n=len(a['dense_token']);assert a['hidden_bf16'].shape==(n,896) and a['raw_top_ids'].shape==(n,256) and n==row['steps']
        category.extend([row['category']]*n);decode.extend([False]+[True]*(n-1));ids.extend([row['id']]*n)
    category=np.array(category);decode=np.array(decode);ids=np.array(ids);assert int(decode.sum())==out['decode_steps']==14986
    summary={}
    for label in ['selected','frozen_baseline']:
        q=out[label];p=R/q['arrays'];assert sha(p)==q['sha256']
        with np.load(p,allow_pickle=False) as a:
            hit=a['hits'];assert hit.dtype==bool and len(hit)==len(decode);np.testing.assert_array_equal(hit,a['route_hits']|a['lowrank_hits']);assert int(a['fallback'].sum())==q['fallback_calls']==0
            for key,values in [('report',hit),('route',a['route_hits']),('lowrank',a['lowrank_hits'])]:
                for phase,mask in [('all',np.ones(len(hit),bool)),('decode',decode),('prefill',~decode)]:
                    z=q[key][phase];assert z['steps']==int(mask.sum()) and z['misses']==int((~values[mask]).sum()) and abs(z['recall']-float(values[mask].mean()))<1e-14
                    for cat,zcat in z['by_category'].items():
                        cmask=mask&(category==cat);assert zcat['steps']==int(cmask.sum()) and zcat['misses']==int((~values[cmask]).sum()) and abs(zcat['recall']-float(values[cmask].mean()))<1e-14
            failed=set(ids[decode&~hit]);assert 1000-len(failed)==q['report']['complete_prompt_decode_match']['all_steps_match_prompts']
            gate=q['report']['decode']['recall']>=.999 and all(c['recall']>=.999 for c in q['report']['decode']['by_category'].values());assert gate==q['proposed_point_gate']
            summary[label]=dict(decode=q['report']['decode'],failed_prompts=len(failed),gate=gate,K_mean=float(a['k'][decode].mean()),K_max=int(a['k'][decode].max()))
    assert out['state']==('PASS_FROZEN_NEW_INDEPENDENT_POINT_GATE' if summary['selected']['gate'] else 'QUALITY_FAIL_NO_RELEASE_NO_RETUNE')
    report=dict(state='PASS_INDEPENDENT_COUNTS_UNIONS_SOURCES_AND_RESERVATION_REVIEW',quality_verdict=out['state'],summary=summary,source_sha256=sha(Path(__file__)),result_sha256=sha(R/'FINAL_QUALITY.json'),scope='Independent counts, saved union identity and source/reservation checks; not a second numerical selector implementation, new certification, full RTL population replay, or FPGA.',board='NOT_RUN')
    (R/'FINAL_QUALITY_REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(report['state'],out['state']);print(json.dumps(summary))
if __name__=='__main__':main()
