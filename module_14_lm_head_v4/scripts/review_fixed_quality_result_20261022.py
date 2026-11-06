"""Independent evidence/count/gate review; does not rerun/tune the selector."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import ast,hashlib,json,math,statistics,struct
M=Path(__file__).resolve().parents[1];D=M/'data/fixed_quality_20261022';R=M/'reports/fixed_quality_20261022'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    result=read(R/'RESULT.json');freeze=read(D/'IMPLEMENTATION_FREEZE.json');entry=read(D/'EVALUATION_ENTRY_LOCK.json')
    collection=M/'data/hidden_fixed_20261022/holdout';manifest=read(collection/'MANIFEST.json')
    assert manifest['state']=='PASS' and manifest['prompts']==1000 and manifest['excluded_prompts']==0
    assert sha(collection/'MANIFEST.json')==result['collection_manifest_sha256']
    assert sha(D/'holdout.jsonl')==entry['corpus_sha256']==result['corpus_sha256']
    assert sha(D/'IMPLEMENTATION_FREEZE.json')==result['implementation_freeze_sha256']
    assert sha(D/'EVALUATION_ENTRY_LOCK.json')==result['entry_lock_sha256']
    for lock in (freeze,entry):
        for n,h in lock['source_sha256'].items():assert sha(M/n)==h,n
    raw=(R/'candidate_counts_all.npy').read_bytes();assert sha(R/'candidate_counts_all.npy')==result['counts_sha256']
    assert raw[:8]==b'\x93NUMPY\x01\x00'
    nhead=int.from_bytes(raw[8:10],'little');header=ast.literal_eval(raw[10:10+nhead].decode('latin1').strip())
    assert header['descr']=='<u4' and header['shape']==(manifest['steps'],) and not header['fortran_order']
    all_counts=struct.unpack('<'+'I'*manifest['steps'],raw[10+nhead:]);decoded=[];references=[];offset=0
    for row in manifest['records']:
        assert 'excluded' not in row
        for step in range(1,row['steps']):
            decoded.append(all_counts[offset+step]);references.append((row,step,offset+step))
        offset+=row['steps']
    assert offset==len(all_counts) and len(decoded)==manifest['decode_steps']==14958
    assert all(14<=k<=151936 for k in all_counts)
    ordered=sorted(decoded);stats=dict(mean=statistics.mean(decoded),median=statistics.median(decoded),p95=ordered[math.ceil(.95*len(ordered))-1],maximum=max(decoded),dense_fallback_calls=sum(k==151936 for k in decoded))
    assert stats==result['candidate_decode'],(stats,result['candidate_decode'])
    for name in ('route','lowrank','hybrid'):
        d=result[name]['decode'];assert d['steps']==len(decoded) and sum(v['steps'] for v in d['by_category'].values())==len(decoded)
        assert sum(v['misses'] for v in d['by_category'].values())==d['misses']
        assert d['recall']==1-d['misses']/d['steps']
    gate=freeze['gate'];h=result['hybrid']['decode']
    passed=h['recall']>=gate['overall_point_recall'] and all(v['recall']>=gate['each_category_point_recall'] for v in h['by_category'].values())
    assert (result['state']=='PASS_PROPOSED_INDEPENDENT_POINT_RECALL_GATE')==passed
    selected={}
    for label,target in [('small',min(decoded)),('median',stats['median']),('p95',stats['p95']),('max',stats['maximum'])]:
        index=min(range(len(decoded)),key=lambda i:(abs(decoded[i]-target),references[i][2]))
        row,step,flat=references[index]
        selected[label]=dict(prompt_id=row['id'],category=row['category'],step=step,flat_prediction_index=flat,candidates=decoded[index],
                             npz=str((collection/row['npz']).relative_to(M)),npz_sha256=row['npz_sha256'])
    # Selection is solely by K after quality is closed; never retrain/tune with it.
    report=dict(state='PASS_RESULT_EVIDENCE_AND_STATISTICS_REVIEW',updated=datetime.now(timezone(timedelta(hours=8))).isoformat(),
                result_sha256=sha(R/'RESULT.json'),groups=1000,decode_steps=len(decoded),candidate_decode=stats,
                quality=result['state'],board='NOT_RUN',scope='Evidence, arithmetic entry/source locks, table/gate/candidate-count statistics; no independent rerun of full GPU arithmetic or RTL',
                performance_case_selection=selected,
                next='Prepare median/P95/max-K inputs and exact candidate goldens before claiming population throughput; current four board arenas cover K20880..28165 only')
    out=R/'INDEPENDENT_REVIEW.json';assert not out.exists();out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('FIXED_QUALITY_REVIEW=PASS_EVIDENCE_STATS; BOARD_NOT_RUN')
if __name__=='__main__':main()
