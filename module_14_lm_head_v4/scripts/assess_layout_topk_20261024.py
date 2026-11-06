"""One manually invoked finite stage-B study. Pure CPU; no target or EDA."""
from pathlib import Path
import argparse,hashlib,json,os,sys,time,zlib
from datetime import datetime
os.environ.setdefault('OPENBLAS_NUM_THREADS','4')
os.environ.setdefault('OMP_NUM_THREADS','4')
import numpy as np
M=Path(__file__).resolve().parents[1];ROOT=M.parent
sys.path.insert(0,str(M));sys.path.insert(0,str(M/'experiments/layout_topk_20261024'))
import feasibility as f
from reference.numeric_contract import bf16_bits_to_float32 as fp,compute_raw_logits
from reference.candidate_head import select_candidate
from reference.hyperparameter_study import SPECIAL,tree_numpy,route_numpy,pure_route_candidates
R=M/'reports/layout_topk_20261024_r1'
S=M/'reports/sparse_methods_20261024_r1'
A=M/'reports/sparse_quality_all557_20261024_r1'
F=M/'reports/hyperparameters_20261023_r1'
W=ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin'
IDS=['partial_dynamic_d64_T4096','partial_dynamic_d128_T1024','cluster_C128_R4_L16384']

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def write(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    temp=p.with_suffix(p.suffix+'.tmp');temp.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8');temp.replace(p)
def stop():
    if (R/'STOP_REQUESTED').exists():raise InterruptedError('Safe finite study stop requested')
def progress(stage,**kw):
    data=dict(stage=stage,pid=os.getpid(),updated=datetime.now().astimezone().isoformat(),**kw)
    write(R/'PROGRESS.json',data);print(json.dumps(data,ensure_ascii=False),flush=True)

def fixtures():
    values={};sources=[]
    for cat in ['chinese','english','code','math']:
        hp=M/f'reports/lowrank_fixture_20261021/{cat}.hidden.bin';bp=hp.with_name(cat+'.history.bin')
        values['old_'+cat]=(np.fromfile(hp,'<u2'),np.fromfile(bp,'<u4'));sources += [hp,bp]
    data=M/'data/hidden_sparse_quality_20261024/holdout';manifest=read(data/'MANIFEST.json');sources.append(data/'MANIFEST.json');used=set()
    for row in manifest['records']:
        cat=row['category']
        if cat in used or row['steps']<2:continue
        p=data/row['npz'];assert sha(p)==row['npz_sha256'];sources.append(p)
        with np.load(p) as z:
            history=np.zeros((f.V+31)//32,'u4');seen=set(map(int,z['input_ids']));seen.add(int(z['dense_token'][0]))
            for token in seen:history[token>>5]|=np.uint32(1<<(token&31))
            values['new_'+cat]=(z['hidden_bf16'][1].copy(),history)
        used.add(cat)
    assert len(values)==8
    return values,sources

def verify_top(scores,t,tag):
    expected=np.argsort(-scores,kind='stable')[:t].astype('u4');records={}
    for name,func in [('heap',f.top_heap),('radix',f.top_radix)]:
        start=time.perf_counter();actual,stats=func(scores,t);elapsed=time.perf_counter()-start
        np.testing.assert_array_equal(actual,expected)
        records[name]=dict(**stats,cpu_elapsed_s=elapsed,ordered_ids_sha256=hashlib.sha256(actual.tobytes()).hexdigest())
    return expected,dict(tag=tag,t=t,n=len(scores),methods=records,pass_order_and_membership=True)

def boundary_tests():
    rng=np.random.default_rng(20261024);tests=[]
    arrays=[np.zeros(1025,'f4'),np.resize(np.array([-0.,0.,1.,1.,-1.,np.finfo('f4').max,-np.finfo('f4').max,np.finfo('f4').smallest_subnormal],'f4'),1025),
        rng.integers(-8,9,size=4099).astype('f4'),rng.normal(size=4099).astype('f4')]
    for i,scores in enumerate(arrays):
        for t in [1,17,min(1024,len(scores)),len(scores)]:
            _,record=verify_top(scores,t,f'boundary_{i}');tests.append(record)
    rejected=[]
    for bad in [np.nan,np.inf,-np.inf]:
        for name,func in [('heap',f.top_heap),('radix',f.top_radix)]:
            try:func(np.array([0,bad],'f4'),1)
            except ValueError:rejected.append(name+':'+str(bad))
            else:raise AssertionError('nonfinite score accepted')
    for t in [0,-1,4,True,1.2]:
        for name,func in [('heap',f.top_heap),('radix',f.top_radix)]:
            try:func(np.ones(3,'f4'),t)
            except ValueError:rejected.append(name+':t='+str(t))
            else:raise AssertionError('invalid T accepted')
    # Independent scalar page/burst simulation, including aligned cross-page spans.
    for start in [0,16,1792,2048,4080,4096]:
        for size in [16,1792,4096,8192]:
            addr=start;remaining=size;count=0
            while remaining:
                n=min(remaining,4096-addr%4096,4096);addr+=n;remaining-=n;count+=1
            assert f.interval_bursts([start],[size])['bursts']==count
    return dict(state='PASS',cases=tests,rejected=rejected,burst_scalar_crosscheck=24)

def main():
    assert not (R/'PLAN.json').exists(),'Do not overwrite completed or partial studies'
    R.mkdir(parents=True,exist_ok=True);stop();inputs,sources=fixtures()
    channels=S/'parameters/channels.npz';modelpath=F/'parameters/cluster_C128.npz';normpath=F/'parameters/norms_C128.npy'
    sources += [Path(__file__),Path(f.__file__),W,channels,modelpath,normpath,
        M/'reference/numeric_contract.py',M/'reference/candidate_head.py',M/'reference/hyperparameter_study.py',
        M/'experiments/sparse_methods_20261024/sparse_methods.py',A/'benchmark/GPU_NUMERIC_PROOF.json',A/'benchmark/PLAN.json',
        A/'cohorts/old/SUMMARY_DATA.json',A/'cohorts/new/SUMMARY_DATA.json',
        S/'PARAMETERS.json',F/'PARAMETERS.json',M/'experiments/board_v4_20261021/create_bd.tcl',
        M/'reports/board_v4_20261021/HARDWARE_RESULT_R2.md',ROOT/'module_14_lm_head_v3_1/standalone/src/pl_ddr_layout.h']
    hashes={p.relative_to(ROOT).as_posix():sha(p) for p in sources}
    assert hashes[W.relative_to(ROOT).as_posix()]=='4e96b0df6d274768cbb7e72404011853d23349999b658dc2f4dfb3c431ea223f'
    assert sha(channels)==read(S/'PARAMETERS.json')['files']['channels']['sha256']
    assert sha(modelpath)==read(F/'PARAMETERS.json')['files']['C128']['sha256']
    assert sha(normpath)==read(F/'PARAMETERS.json')['files']['C128']['norms_sha256']
    bd=(M/'experiments/board_v4_20261021/create_bd.tcl').read_text()
    assert 'CONFIG.C0.DDR4_AxiDataWidth {128}' in bd and '0x400000000 -range 0x80000000' in bd
    assert '128 位数据' in (M/'reports/board_v4_20261021/HARDWARE_RESULT_R2.md').read_text(encoding='utf-8')
    old=read(A/'cohorts/old/SUMMARY_DATA.json');new=read(A/'cohorts/new/SUMMARY_DATA.json')
    selected={}
    for key in IDS:
        selected[key]={cohort:next(p for p in dataset['points'] if p['id']==key) for cohort,dataset in [('old',old),('new',new)]}
        for cohort in ['old','new']:
            q=selected[key][cohort]['quality'];assert q['recall']>=.99 and min(x['recall'] for x in q['by_category'].values())>=.99
    plan=dict(created=datetime.now().astimezone().isoformat(),state='FROZEN_FINITE_STAGE_B',configurations=IDS,
        selection='Previously declared engineering shortlist; no parameter tuning or new quality certification',tiles=[128,1024],
        fixtures=list(inputs),source_sha256=hashes,top_methods=['bounded_streaming_heap','4x8bit_radix_threshold'],
        bus_model=dict(data_bits=128,address_bits=64,beat_bytes=16,max_burst_beats=256,boundary_bytes=4096,
            scope='Existing v4 source; proposed schedule on that interface, not generated RTL or physical traffic'),
        stop='STOP_REQUESTED checked at case/layout boundaries; no automatic next stage',
        EDA='NOT_RUN',FPGA='NOT_RUN',GPU='NOT_RUN_THIS_STUDY')
    write(R/'PLAN.json',plan);write(R/'ACTIVE.lock',dict(pid=os.getpid(),created=plan['created']))
    try:
        progress('BOUNDARY_TESTS');write(R/'BOUNDARY_TESTS.json',boundary_tests())
        bits=np.memmap(W,mode='r',dtype='<u2',shape=(f.V,f.H))
        with np.load(channels) as z:rms=z['rms'].copy()
        with np.load(modelpath) as z:model={k:z[k].copy() for k in z.files}
        norms=np.load(normpath);gold={(x['id'],x['case']):x for x in read(A/'benchmark/GPU_NUMERIC_PROOF.json')['records']}
        layouts={};layoutproof=[]
        for tile in plan['tiles']:
            stop();progress('PACK_LAYOUT',tile=tile);p=R/f'assets/tiled_W_B{tile}.bin';p.parent.mkdir(exist_ok=True)
            tiled=f.make_tiled(bits,p,tile);inverse=hashlib.sha256()
            for n in range(len(tiled)):
                size=min(tile,f.V-n*tile);block=tiled[n,:,:size].T.copy();np.testing.assert_array_equal(block,bits[n*tile:n*tile+size]);inverse.update(block.tobytes())
                assert np.all(tiled[n,:,size:]==0)
            assert inverse.hexdigest()==sha(W)
            layouts[tile]=tiled;layoutproof.append(dict(tile=tile,path=p.relative_to(R).as_posix(),sha256=sha(p),bytes=p.stat().st_size,
                inverse_canonical_sha256=inverse.hexdigest(),all_weight_bits_equal=True,padding_zero=True))
        write(R/'LAYOUT_PROOF.json',dict(state='PASS_FULL_CANONICAL_INVERSE',layouts=layoutproof))
        regions={}
        for item in layoutproof:
            for dual in [True,False]:regions[f'{"dual" if dual else "shared"}_B{item["tile"]}']=f.layout_regions(item['bytes'],dual)
        write(R/'PL_DDR_LAYOUTS.json',regions)
        records=[];toprecords=[];traces=[]
        for case,(hidden,history) in inputs.items():
            stop();progress('FIXTURE_PROOFS',case=case);h=fp(hidden);seen=np.flatnonzero(((history[np.arange(f.V)>>5]>>(np.arange(f.V)&31))&1)!=0)
            for d,t in [(64,4096),(128,1024)]:
                dims=np.argsort(-np.multiply(np.abs(h),rms,dtype=np.float32),kind='stable')[:d].astype('u4')
                reference=np.empty(f.V,'f4')
                for start in range(0,f.V,4096):
                    rows=fp(bits[start:start+4096][:,dims]);reference[start:start+len(rows)]=tree_numpy(np.multiply(rows,h[dims],dtype=np.float32))
                scores=reference.copy();penalty=np.float32(1.1);oldseen=scores[seen]
                scores[seen]=np.where(oldseen<0,np.multiply(oldseen,penalty,dtype=np.float32),np.divide(oldseen,penalty,dtype=np.float32))
                top,toprec=verify_top(scores,t,case+f'_d{d}_T{t}');toprecords.append(toprec)
                ids=np.union1d(top,SPECIAL).astype('u4');key=f'partial_dynamic_d{d}_T{t}'
                raw=compute_raw_logits(hidden,bits[ids]);policy,token,score=select_candidate(raw,ids,f.V,history,penalty=1.1)
                proof=gold[key,case]
                actual=dict(ids_sha256=hashlib.sha256(ids.tobytes()).hexdigest(),raw_sha256=hashlib.sha256(raw.tobytes()).hexdigest(),token=token,score_bits=int(score.view('u4')),k=len(ids))
                for name,value in actual.items():assert proof[name]==value,(key,case,name)
                crc=zlib.crc32(__import__('struct').pack('<II',token,int(score.view('u4'))));assert crc==proof['crc']
                ap=R/f'arrays/{case}_d{d}_T{t}.npz';ap.parent.mkdir(exist_ok=True)
                np.savez_compressed(ap,dims=dims,preview=reference,policy_preview=scores,top=top,ids=ids,raw=raw,policy_raw=policy)
                for tile,tiled in layouts.items():
                    stop();preview=f.preview_tiled(tiled,tile,hidden,dims,fp,tree_numpy)
                    np.testing.assert_array_equal(preview.view('u4'),reference.view('u4'))
                    gathered=f.gather_tiled(tiled,ids,tile);np.testing.assert_array_equal(gathered,bits[ids])
                    raw2=compute_raw_logits(hidden,gathered);np.testing.assert_array_equal(raw2.view('u4'),raw.view('u4'))
                    tr=f.traffic(ids,d,tile);traces.append(dict(case=case,id=key,k=len(ids),**tr))
                records.append(dict(case=case,id=key,**actual,crc=crc,array=ap.relative_to(R).as_posix(),array_sha256=sha(ap),
                    full_preview_both_layouts=True,full_exact_raw_both_layouts=True,prior_paired557_proof_match=True))
            order,dist=route_numpy(hidden,model['centers_bf16'],norms);ids,fallback=pure_route_candidates(model,order[:4],16384)
            assert not fallback
            key=IDS[2];proof=gold[key,case];raw=compute_raw_logits(hidden,bits[ids]);_,token,score=select_candidate(raw,ids,f.V,history,penalty=1.1)
            actual=dict(ids_sha256=hashlib.sha256(ids.tobytes()).hexdigest(),raw_sha256=hashlib.sha256(raw.tobytes()).hexdigest(),token=token,score_bits=int(score.view('u4')),k=len(ids))
            for name,value in actual.items():assert proof[name]==value
            ap=R/f'arrays/{case}_cluster.npz';np.savez_compressed(ap,ids=ids,raw=raw,distances=dist,routes=order[:4])
            records.append(dict(case=case,id=key,**actual,array=ap.relative_to(R).as_posix(),array_sha256=sha(ap),prior_paired557_proof_match=True))
            a,b=f.runs(ids);exact=f.interval_bursts(a*f.H*2,(b-a)*f.H*2)
            traces.append(dict(case=case,id=key,k=len(ids),cluster_exact=exact,
                router_weight_bytes=128*f.H*2,list_id_bytes=int(np.minimum(model['counts'][order[:4]],16384).sum())*4))
            write(R/'NUMERIC_PROOF.partial.json',records);write(R/'ACCESS_MODEL.partial.json',traces)
        write(R/'NUMERIC_PROOF.json',dict(state='PASS_24_FIXTURES_32_LAYOUT_PREVIEWS_AND_EXACT',records=records))
        write(R/'TOP_T_PROOF.json',dict(state='PASS_16_REAL_PLUS_BOUNDARIES',records=toprecords,
            scope='CPU functional proof and elapsed observations only; no GPU benchmark or HLS estimate'))
        write(R/'ACCESS_MODEL.json',dict(state='OFFLINE_SCHEDULED_MASTER_PAYLOAD_NOT_MEASURED_AXI',records=traces,
            shared='Gather each128bit group once per tile/channel, coalesce adjacent groups, no intercall cache. Actual HLS must realize this schedule.',
            dual='Canonical row runs coalesced, payload/AR bursts split4KiB; tiled preview includes zero padding.',
            excluded='Control, refresh, arbitration, DRAM commands, loader, writebacks and controller internal overfetch. Shared preview->exact reuse not assumed.'))
        assert all(sha(ROOT/p)==h for p,h in hashes.items()),'Source changed during study'
        write(R/'RESULT.json',dict(state='FUNCTIONAL_STAGE_B_COMPLETE_REVIEW_PENDING',configurations=IDS,
            cases=8,real_top_proofs=16,layout_preview_and_exact_proofs=32,prior_reference_fixtures=24,
            plan_sha256=sha(R/'PLAN.json'),board='NOT_RUN',EDA='NOT_RUN',HLS='NOT_RUN',new_quality='NOT_RUN_NOT_NEEDED_FOR_BIT_IDENTICAL_LAYOUT',
            next='Independent review and feasibility decision, no automatic EDA'))
        progress('FUNCTIONAL_COMPLETE_REVIEW_PENDING',records=len(records))
    finally:(R/'ACTIVE.lock').unlink(missing_ok=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',action='store_true');args=parser.parse_args()
    if not args.run:parser.error('Explicit --run required; no automatic workflow')
    main()
