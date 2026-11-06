"""Freeze one d64/T4096 Csim/HLS prototype. No EDA launch or target use."""
from pathlib import Path
import hashlib,json,sys
from datetime import datetime
import numpy as np
M=Path(__file__).resolve().parents[1];ROOT=M.parent;sys.path.insert(0,str(M))
from reference.numeric_contract import bf16_bits_to_float32 as fp,compute_raw_logits,output_crc32
from reference.hyperparameter_study import tree_numpy,SPECIAL
from reference.candidate_head import select_candidate
E=M/'experiments/partial_hw_20261024';R=M/'reports/partial_hw_20261024_r1';B=M/'reports/layout_topk_20261024_r1'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def keys(x):
    bits=x.view('u4').copy();bits[x==0]=0
    return np.where(bits>>31,~bits,bits^np.uint32(0x80000000)).astype('u4')
def main():
    assert not (R/'PLAN.json').exists(),'Preserve prior run'
    assert read(B/'RESULT.json')['state']=='STAGE_B_COMPLETE_PASS_TO_MINIMAL_PROTOTYPE'
    assert not (B/'ACTIVE.lock').exists()
    for p,h in read(B/'PLAN.json')['source_sha256'].items():assert sha(ROOT/p)==h
    derived=[]
    for name in ['lm_head_v4_candidate.cpp','accepted_numeric_core.hpp','lm_head_v4_candidate.hpp']:
        original=M/('include' if name=='lm_head_v4_candidate.hpp' else 'src')/name
        baseline=E/'baseline'/name;baseline.parent.mkdir(exist_ok=True);baseline.write_bytes(original.read_bytes())
        text=original.read_text(encoding='utf-8');new=text.replace('max=151936','max=4110')
        target=E/'derived'/name;target.parent.mkdir(exist_ok=True);target.write_text(new,encoding='utf-8')
        derived.append(dict(original=original.relative_to(ROOT).as_posix(),original_sha256=sha(original),baseline=baseline.relative_to(ROOT).as_posix(),
            derived=target.relative_to(ROOT).as_posix(),derived_sha256=sha(target),change='Only LOOP_TRIPCOUNT max151936 -> max4110; arithmetic/interfaces unchanged',replacements=text.count('max=151936')))
    fixture=E/'fixtures';fixture.mkdir(exist_ok=True);records=read(B/'NUMERIC_PROOF.json')['records'];sources=[Path(__file__)]
    for name in ['partial_proto.hpp','partial_proto.cpp','proto_tb.cpp','proto.tcl']:sources.append(E/name)
    for item in derived:sources += [ROOT/item['baseline'],ROOT/item['derived'],ROOT/item['original']]
    for name in ['PLAN.json','RESULT.json','NUMERIC_PROOF.json','LAYOUT_PROOF.json','INDEPENDENT_REVIEW.json']:sources.append(B/name)
    for name in ['numeric_contract.py','candidate_head.py','hyperparameter_study.py']:sources.append(M/'reference'/name)
    canonical=ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin';tiled=B/'assets/tiled_W_B1024.bin';sources += [canonical,tiled]
    assert sha(canonical)=='4e96b0df6d274768cbb7e72404011853d23349999b658dc2f4dfb3c431ea223f'
    (fixture/'weight_paths.txt').write_text(tiled.as_posix()+'\n'+canonical.as_posix()+'\n',encoding='ascii')
    sources.append(fixture/'weight_paths.txt')
    with np.load(M/'reports/sparse_methods_20261024_r1/parameters/channels.npz') as z:rms=z['rms'].copy()
    sources.append(M/'reports/sparse_methods_20261024_r1/parameters/channels.npz')
    inputs={}
    for cat in ['chinese','english','code','math']:
        hp=M/f'reports/lowrank_fixture_20261021/{cat}.hidden.bin';bp=hp.with_name(cat+'.history.bin');sources += [hp,bp]
        inputs['old_'+cat]=(np.fromfile(hp,'<u2'),np.fromfile(bp,'<u4'))
    data=M/'data/hidden_sparse_quality_20261024/holdout';sources.append(data/'MANIFEST.json');used=set()
    for row in read(data/'MANIFEST.json')['records']:
        c=row['category']
        if c in used or row['steps']<2:continue
        p=data/row['npz'];assert sha(p)==row['npz_sha256'];sources.append(p)
        with np.load(p) as z:
            seen=set(map(int,z['input_ids']));seen.add(int(z['dense_token'][0]));history=np.zeros(4748,'u4')
            for token in seen:history[token>>5]|=np.uint32(1<<(token&31))
            inputs['new_'+c]=(z['hidden_bf16'][1].copy(),history)
        used.add(c)
    inputs['zero_hidden']=(np.zeros(896,'u2'),np.zeros(4748,'u4'))
    weights=np.memmap(canonical,mode='r',dtype='<u2',shape=(151936,896));fixture_records=[]
    for case,(hidden,history) in inputs.items():
        if case=='zero_hidden':
            dims=np.arange(64,dtype='u4');preview=np.empty(151936,'f4')
            for start in range(0,151936,4096):preview[start:start+4096]=tree_numpy(fp(weights[start:start+4096,:64])*np.float32(0))
            policy=preview.copy();top=np.argsort(-policy,kind='stable')[:4096];ids=np.union1d(top,SPECIAL).astype('u4');raw=compute_raw_logits(hidden,weights[ids])
        else:
            item=next(x for x in records if x['id']=='partial_dynamic_d64_T4096' and x['case']==case);p=B/item['array'];assert sha(p)==item['array_sha256'];sources.append(p)
            with np.load(p) as z:dims=z['dims'].copy();preview=z['preview'].copy();policy=z['policy_preview'].copy();ids=z['ids'].copy();raw=z['raw'].copy()
        _,token,score=select_candidate(raw,ids,151936,history,penalty=1.1)
        expected=np.array([token,int(score.view('u4')),output_crc32(token,score),len(ids)],'<u4')
        meta=hidden.astype('<u2').tobytes()+rms.astype('<f4').tobytes()+history.astype('<u4').tobytes();assert len(meta)==1523*16
        (fixture/(case+'.meta.bin')).write_bytes(meta);items={'dims':dims,'preview':preview.view('u4'),'keys':keys(policy),'ids':ids,'raw':raw.view('u4'),'expected':expected}
        files=[fixture/(case+'.meta.bin')]
        for key,array in items.items():p=fixture/(case+'.'+key+'.bin');array.astype('<u4').tofile(p);files.append(p)
        fixture_records.append(dict(case=case,k=len(ids),token=token,score_bits=int(score.view('u4')),crc=int(expected[2]),
            files={p.name:sha(p) for p in files}));sources+=files
    expected_cases=[('old_chinese','A0',1),('old_english','B0',1),('old_chinese','A1',1)]+[(x,x,1) for x in ['old_code','old_math','new_chinese','new_english','new_code','new_math']]+[('zero_hidden','all_ties',1),('old_chinese','production',0)]
    write(R/'PLAN.json',dict(created=datetime.now().astimezone().isoformat(),state='FROZEN_FINITE_CSIM_HLS_ONLY',config=dict(d=64,T=4096,tile=1024),
        tool='G:/Xilinx/Vitis_HLS/2021.1/bin/vitis_hls.bat',part='xczu9eg-ffvb1156-2-i',period_ns=5,uncertainty_ns=1.35,
        source_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sources},derivation=derived,fixtures=fixture_records,expected_cases=expected_cases,
        arithmetic='Dynamic abs(h)*RMS stable descending lower channel ID ties; FP32 binary carry same adjacent preview tree; penalty1.1;4x8bit radix, signed0 equal; global-ID candidate scan union14 special; accepted H8/interleave16 exact head',
        prototype_scope='Sequential integrated minimum, always writes full preview debug workspace; debug flag controls exact raw writes. Not final production bus budget. No bitmap because final global-ID scan emits unique sorted IDs.',
        validation='All dims/151936 preview bits/keys/IDs/candidate raw/token/score/CRC;8 real+zero+ABA+production;6negative',
        synthesis_tripcounts='Accepted exact leaf copy changes only report max151936->4110 for new K cap',
        stages=['manual csim then independent array review','manual csynth after csim PASS'],
        stop='Stop owning process tree after current PID/creation check; no automatic next stage',
        board='NOT_RUN',RTL='NOT_RUN',implementation='NOT_RUN',BSP_ELF='NOT_RUN',no_new_quality=True))
    write(R/'PROGRESS.json',dict(stage='PREPARED_NOT_LAUNCHED',board='NOT_RUN',EDA='NOT_RUN'))
    print(json.dumps(dict(state='PREPARED_FROZEN',fixtures=len(fixture_records),cases=len(expected_cases),sources=len(set(sources)))))
if __name__=='__main__':main()
