"""Independent saved-array / address model review plus streamed tree proof.

No torch/target/EDA. Does not import producer feasibility implementation for
reviewed Top-T, layout reconstruction, region or traffic counts.
"""
from pathlib import Path
import hashlib,json,math,sys,time,zlib,struct
import numpy as np
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/layout_topk_20261024_r1'
sys.path.insert(0,str(M));sys.path.insert(0,str(M/'experiments/layout_topk_20261024'))
import streamed_preview
from reference.numeric_contract import bf16_bits_to_float32 as fp
from reference.candidate_head import select_candidate
V,H=151936,896

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as handle:return hashlib.file_digest(handle,'sha256').hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def stop():
    if (R/'STOP_REQUESTED').exists():raise InterruptedError('Stop at review case boundary')
def simple_bursts(start,length):
    count=0
    while length:
        size=min(length,4096-start%4096,256*16);assert size>0
        start+=size;length-=size;count+=1
    return count

def main():
    assert not (R/'INDEPENDENT_REVIEW.json').exists(),'Preserve previous review'
    plan=read(R/'PLAN.json');proof=read(R/'NUMERIC_PROOF.json');access=read(R/'ACCESS_MODEL.json')
    assert not (R/'ACTIVE.lock').exists()
    for path,h in plan['source_sha256'].items():assert sha(ROOT/path)==h,path
    lock=dict(stage='STREAMED_PREVIEW_FUNCTIONAL_REVIEW',script_sha256=sha(Path(__file__)),
        source_sha256=sha(Path(streamed_preview.__file__)),base_plan_sha256=sha(R/'PLAN.json'),
        no_parameter_changes=True,board='NOT_RUN',EDA='NOT_RUN')
    write(R/'REVIEW_ENTRY.json',lock)
    source=np.memmap(ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin',mode='r',dtype='<u2',shape=(V,H))
    tiles={};layout_checks=[]
    for item in read(R/'LAYOUT_PROOF.json')['layouts']:
        p=R/item['path'];assert sha(p)==item['sha256'];b=item['tile'];a=np.memmap(p,dtype='<u2',mode='r',shape=((V+b-1)//b,H,b));tiles[b]=a
        digest=hashlib.sha256()
        # Independent index mapping over1024 global row IDs, not producer tile loop.
        for start in range(0,V,1024):
            ids=np.arange(start,min(start+1024,V));rows=a[ids//b,:,ids%b].copy()
            np.testing.assert_array_equal(rows,source[ids]);digest.update(rows.tobytes())
        assert digest.hexdigest()==plan['source_sha256']['artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin']
        layout_checks.append(dict(tile=b,full_inverse_sha256=digest.hexdigest()))
    # Bound all proposed regions and ensure explicit prefix guard and no overlap.
    for label,profile in read(R/'PL_DDR_LAYOUTS.json').items():
        previous=profile['prefix_guard_bytes'];assert profile['arena_bytes']<=profile['aperture_bytes']
        for region in profile['regions']:
            assert region['offset']>=previous and region['end_exclusive']==region['offset']+region['bytes']
            assert int(region['address'],0)==int(profile['base'],0)+region['offset']
            assert region['end_exclusive']<=profile['arena_bytes'];previous=region['end_exclusive']
    # Build the exact historical8 fixed-input identities without importing runner.
    inputs={}
    for cat in ['chinese','english','code','math']:
        base=M/'reports/lowrank_fixture_20261021'
        inputs['old_'+cat]=(np.fromfile(base/(cat+'.hidden.bin'),'<u2'),np.fromfile(base/(cat+'.history.bin'),'<u4'))
    data=M/'data/hidden_sparse_quality_20261024/holdout';used=set()
    for row in read(data/'MANIFEST.json')['records']:
        c=row['category']
        if c in used or row['steps']<2:continue
        with np.load(data/row['npz']) as z:
            history=np.zeros((V+31)//32,'u4')
            for i in set(map(int,z['input_ids']))|{int(z['dense_token'][0])}:history[i>>5]|=np.uint32(1<<(i&31))
            inputs['new_'+c]=(z['hidden_bf16'][1].copy(),history)
        used.add(c)
    oldproof={(x['id'],x['case']):x for x in read(M/'reports/sparse_quality_all557_20261024_r1/benchmark/GPU_NUMERIC_PROOF.json')['records']}
    arrays={};streamed=[];top_checks=[]
    for item in proof['records']:
        stop();p=R/item['array'];assert sha(p)==item['array_sha256']
        with np.load(p) as z:values={k:z[k].copy() for k in z.files}
        arrays[item['case'],item['id']]=values;ids=values['ids'];raw=values['raw']
        _,token,score=select_candidate(raw,ids,V,inputs[item['case']][1],penalty=1.1)
        prior=oldproof[item['id'],item['case']]
        assert len(ids)==prior['k'] and hashlib.sha256(ids.tobytes()).hexdigest()==prior['ids_sha256']
        assert hashlib.sha256(raw.tobytes()).hexdigest()==prior['raw_sha256'] and token==prior['token'] and int(score.view('u4'))==prior['score_bits']
        assert zlib.crc32(struct.pack('<II',token,int(score.view('u4'))))==prior['crc']
        if item['id'].startswith('partial'):
            top=values['top'];reference=np.lexsort((np.arange(V),-values['policy_preview']))[:len(top)]
            np.testing.assert_array_equal(top,reference)
            expected=np.unique(np.r_[reference,np.arange(151643,151657)]).astype('u4');np.testing.assert_array_equal(ids,expected)
            top_checks.append(dict(case=item['case'],id=item['id'],top=len(top)))
            for tile,a in tiles.items():
                stop();start=time.perf_counter();actual=streamed_preview.preview(a,tile,inputs[item['case']][0],values['dims'],fp)
                np.testing.assert_array_equal(actual.view('u4'),values['preview'].view('u4'))
                streamed.append(dict(case=item['case'],id=item['id'],tile=tile,full_preview_bits=True,cpu_elapsed_s=time.perf_counter()-start,
                    stack_bytes=(len(values['dims']).bit_length())*tile*4,
                    eager_product_bytes=len(values['dims'])*tile*4))
    # Independent128bit-address grouping. Candidate ID8-way group is the same
    # physical beat for each of896 channels in [tile,channel,token] layout.
    address_checks=[]
    for row in access['records']:
        stop();ids=arrays[row['case'],row['id']]['ids'].astype('i8')
        starts=np.r_[0,np.where(np.diff(ids)>1)[0]+1];ends=np.r_[starts[1:],len(ids)]
        bursts=sum(simple_bursts(int(ids[a])*H*2,int(ids[b-1]-ids[a]+1)*H*2) for a,b in zip(starts,ends))
        target=row.get('dual_exact',row.get('cluster_exact'))
        assert target['bursts']==bursts and target['payload_bytes']==len(ids)*H*2
        if 'tile_tokens' in row:
            tile=row['tile_tokens'];groups=np.unique(ids//8)
            # Count runs within each tile explicitly rather than producer run split formula.
            rr=0
            for tile_id in np.unique((groups*8)//tile):
                local=groups[(groups*8)//tile==tile_id]%(tile//8)
                rr+=1+int((np.diff(local)>1).sum())
            assert row['shared_exact']['bursts']==rr*H
            assert row['shared_exact']['payload_bytes']==len(groups)*H*16
            assert row['preview']['payload_bytes']==math.ceil(V/tile)*tile*len(arrays[row['case'],row['id']]['dims'])*2
            # Exhaustive per-channel beat-address sets for small representative
            # tile: verify actual indexed words map to the predicted16B groups.
            rng=np.random.default_rng(20261024);sample=ids[rng.choice(len(ids),min(256,len(ids)),replace=False)]
            addresses=((sample[:,None]//tile*H+np.arange(H)[None,:])*tile+sample[:,None]%tile)*2
            actual_groups=np.unique(addresses//16)
            predicted=((sample[:,None]//tile*H+np.arange(H)[None,:])*(tile//8)+sample[:,None]%tile//8)
            np.testing.assert_array_equal(actual_groups,np.unique(predicted))
        address_checks.append(dict(case=row['case'],id=row['id'],tile=row.get('tile_tokens'),bursts_reconstructed=True))
    review=dict(state='PASS_INDEPENDENT_ARRAY_LAYOUT_TOP_ADDRESS_REVIEW',records=len(proof['records']),
        layout_checks=layout_checks,top_checks=top_checks,streamed_preview=streamed,address_checks=address_checks,
        producer_source_sha_all_unchanged=True,review_source_sha256=sha(Path(__file__)),streamed_source_sha256=sha(Path(streamed_preview.__file__)),
        scope='Independent implementation in same agent, not external review; no FPGA performance measurement',
        full_rtl='NOT_RUN',HLS='NOT_RUN',board='NOT_RUN')
    write(R/'INDEPENDENT_REVIEW.json',review);print(json.dumps(dict(state=review['state'],records=review['records'],streamed=len(streamed),addresses=len(address_checks))))

if __name__=='__main__':main()
