"""Independent binary readback for native C++ or official remote HLS Csim."""
from pathlib import Path
import argparse,hashlib,json,shutil,struct,zlib,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/partial_hw_20261024_r1';E=M/'experiments/partial_hw_20261024';sys.path.insert(0,str(M))
from reference.numeric_contract import bf16_bits_to_float32 as fp,compute_raw_logits
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    global R
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['native','csim'],required=True);parser.add_argument('--actual-dir',type=Path);parser.add_argument('--revision',choices=['r1','r2','r3'],default='r1');args=parser.parse_args()
    if args.revision!='r1':R=R/args.revision
    plan=read(R/'PLAN.json');source=args.actual_dir or E/'fixtures';log=R/('native_run.log' if args.mode=='native' else 'remote_csim.log');text=log.read_text(encoding='utf-8',errors='replace')
    assert 'PARTIAL_PROTO_CSIM_ALL_PASS valid=11 unique=9 negative=6' in text
    if args.mode=='csim':assert 'PARTIAL_PROTO_csim=PASS' in text
    for p,h in plan['source_sha256'].items():assert sha(ROOT/p)==h,p
    for deriv in plan['derivation']:
        original=(ROOT/deriv['original']).read_text(encoding='utf-8');derived=(ROOT/deriv['derived']).read_text(encoding='utf-8')
        assert original.replace('max=151936','max=4110')==derived
        assert sha(ROOT/deriv['baseline'])==deriv['original_sha256']
    dest=R/(args.mode+'_actual');dest.mkdir(exist_ok=True);records=[]
    weights=np.memmap(ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin',dtype='<u2',mode='r',shape=(151936,896))
    for case,label,debug in plan['expected_cases']:
        assert f'CSIM_CASE_PASS {label} debug={debug}' in text
        actual=source/('actual_'+label+'.bin');arr=np.fromfile(actual,'<u4');assert len(arr)>=4
        if args.revision!='r1':assert actual.read_bytes()==(R.parent/'remote_csim/csim_actual'/actual.name).read_bytes(),'Revision changed complete numerical output'
        token,scorebits,crc,k=map(int,arr[:4]);assert 4096<=k<=4110
        assert len(arr)==4+64+2*151936+k*(2 if debug else 1)
        cursor=4;dims=arr[cursor:cursor+64];cursor+=64;preview=arr[cursor:cursor+151936];cursor+=151936;keys=arr[cursor:cursor+151936];cursor+=151936;ids=arr[cursor:cursor+k];cursor+=k
        base=E/'fixtures';meta=(base/(case+'.meta.bin')).read_bytes();hidden=np.frombuffer(meta[:1792],'<u2');rms=np.frombuffer(meta[1792:5376],'<f4');history=np.frombuffer(meta[5376:],'<u4')
        channel_order=np.lexsort((np.arange(896),-np.multiply(np.abs(fp(hidden)),rms,dtype=np.float32)))[:64]
        np.testing.assert_array_equal(dims,channel_order)
        np.testing.assert_array_equal(preview,np.fromfile(base/(case+'.preview.bin'),'<u4'))
        policy=preview.view('f4').copy();vid=np.arange(151936);seen=((history[vid>>5]>>(vid&31))&1)!=0
        policy[seen & (policy<0)]=np.multiply(policy[seen & (policy<0)],np.float32(1.1),dtype=np.float32)
        # Compute positive mask from original raw to avoid using mutated signs.
        positive=seen & ~(preview.view('f4')<0)
        policy[positive]=np.divide(policy[positive],np.float32(1.1),dtype=np.float32)
        rawbits=policy.view('u4').copy();rawbits[policy==0]=0
        expectedkeys=np.where(rawbits&0x80000000,~rawbits,rawbits^np.uint32(0x80000000)).astype('u4')
        np.testing.assert_array_equal(keys,expectedkeys)
        top=np.lexsort((vid,-policy))[:4096];expectedids=np.unique(np.r_[top,np.arange(151643,151657)]).astype('u4');np.testing.assert_array_equal(ids,expectedids)
        exact=compute_raw_logits(hidden,weights[ids]);old=exact.copy();used=((history[ids>>5]>>(ids&31))&1)!=0
        exact_policy=np.where(used,np.where(old<0,np.multiply(old,np.float32(1.1),dtype=np.float32),np.divide(old,np.float32(1.1),dtype=np.float32)),old)
        winner=int(np.min(ids[exact_policy==exact_policy.max()]));winbits=int(exact_policy[np.flatnonzero(ids==winner)[0]].view('u4'))
        assert token==winner and scorebits==winbits and crc==zlib.crc32(struct.pack('<II',token,scorebits))
        if debug:np.testing.assert_array_equal(arr[cursor:],exact.view('u4'))
        target=dest/actual.name
        if target.exists():assert sha(target)==sha(actual),'Preserve prior actual output'
        else:shutil.copy2(actual,target)
        records.append(dict(case=case,label=label,debug=debug,k=k,token=token,score_bits=scorebits,crc=crc,actual_sha256=sha(actual),
            full_dynamic_channels_preview_policy_keys_ids_exact_output=True))
    assert (dest/'actual_A0.bin').read_bytes()==(dest/'actual_A1.bin').read_bytes(),'ABA readback differs'
    result=dict(state='PASS_FULL_CSIM_ARRAYS' if args.mode=='csim' else 'PASS_NATIVE_CPP_FUNCTIONAL_ARRAYS',mode=args.mode,
        records=records,source_sha_all_unchanged=True,exact_derived_from_original_bf16=True,ABA='PASS_BIT_IDENTICAL',
        errors='6 negative guards asserted in saved C++ testbench; not external hardware access',log_sha256=sha(log),
        plan_sha256=sha(R/'PLAN.json'),review_script_sha256=sha(Path(__file__)),
        scope='Vendor C++ behavior; native mode is not official HLS Csim. Neither is RTL or hardware proof.',RTL='NOT_RUN',board='NOT_RUN')
    output=R/('CSIM_QUALIFICATION.json' if args.mode=='csim' else 'NATIVE_QUALIFICATION.json');assert not output.exists(),'Preserve previous qualification'
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(state=result['state'],cases=len(records))))
if __name__=='__main__':main()
