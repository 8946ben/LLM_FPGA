"""Derive an isolated compile-time selector for the locked experiment10 point.

Original qualified sources/IP/private package remain untouched. Generates
four full numeric fixtures, v2 descriptor/layout, and the genuine HLS testbench.
"""
from pathlib import Path
import hashlib,json,re,shutil,struct,sys
import numpy as np
import fusion_experiment10_20261023 as e
M=e.M;R=e.R;X=M/'experiments/fusion_exp10_20261023';b=e.b
def replace(text,old,new,count=None):
    found=text.count(old);assert found and (count is None or found==count),(old,found,count)
    return text.replace(old,new)
def tree_function(words):
    declarations=[];operations=[];current='p0';n=words;level=0
    declarations+= [f'        float p0[{words}];','#pragma HLS ARRAY_PARTITION variable=p0 complete']
    operations += [f'        for(unsigned i=0;i<{words};++i){{','#pragma HLS UNROLL','            p0[i]=bits_to_float(context.range(32*i+31,32*i).to_uint());','        }']
    while n>1:
        level+=1;next_name=f'p{level}';n//=2;declarations += [f'        float {next_name}[{n}];',f'#pragma HLS ARRAY_PARTITION variable={next_name} complete'];operations += [f'        for(unsigned i=0;i<{n};++i){{','#pragma HLS UNROLL',f'            {next_name}[i]={current}[2*i]+{current}[2*i+1];','        }'];current=next_name
    return '\n'.join(['void tree_context(hls::stream<ap_uint<512> >& contexts,unsigned rows,hls::stream<float>& raw){','tree_row:','    for(unsigned row=0;row<rows;++row){','#pragma HLS PIPELINE II=1','#pragma HLS LOOP_TRIPCOUNT min=1 max=151936','        const ap_uint<512> context=contexts.read();']+declarations+operations+[f'        raw.write({current}[0]);','    }','}',''])
def main():
    lock=e.read(R/'SELECTION_LOCK.json');p=lock['parameters'];c,rr,l,rank,t=[p[k] for k in ['C','R','L','r','T']];words=rank//8;assert rank in [32,64,128] and words&(words-1)==0
    assert not X.exists(),'Preserve selected hardware experiment';(X/'src').mkdir(parents=True);(X/'include').mkdir();(X/'tests').mkdir();(X/'fixture').mkdir();(X/'reports').mkdir();(X/'build').mkdir()
    frozen=e.read(M/'reports/SELECTOR_PRIVATE_IP_MANIFEST.json')
    for n,h in frozen['source_sha256'].items():assert b.sha(M/n)==h,n
    for name in ['lm_head_v4_selector.cpp','lm_head_v4_lowrank.cpp','lm_head_v4_router.cpp','lm_head_v4_topk.cpp','lm_head_v4_candidate.cpp','accepted_numeric_core.hpp']:shutil.copy2(M/'src'/name,X/'src'/name)
    for name in ['lm_head_v4_selector.hpp','lm_head_v4_lowrank.hpp','lm_head_v4_router.hpp','lm_head_v4_topk.hpp','lm_head_v4_candidate.hpp']:shutil.copy2(M/'include'/name,X/'include'/name)
    tag=int(hashlib.sha256(json.dumps(p,sort_keys=True).encode()).hexdigest()[:8],16)
    path=X/'src/lm_head_v4_lowrank.cpp';s=path.read_text(encoding='utf-8');s=replace(s,'row<128',f'row<{rank}',1);s=replace(s,'z[16][8]',f'z[{words}][8]');s=replace(s,'rows*16',f'rows*{words}');s=replace(s,'a_capacity<n*16',f'a_capacity<n*{words}',1);s=replace(s,'14336',str(rank*112));s=replace(s,'2430976',str(e.V*words));s=replace(s,'+n*16',f'+n*{words}')
    start=s.index('void product_context(');end=s.index('void tree_context(');piece=s[start:end];piece=replace(piece,'slots[16]',f'slots[{words}]',1);piece=replace(piece,'index&15',f'index&{words-1}',1);piece=replace(piece,'word==15',f'word=={words-1}',1);piece=replace(piece,'s<16',f's<{words}',1);piece=replace(piece,'s==15',f's=={words-1}',1);s=s[:start]+piece+s[end:];start=s.index('void tree_context(');end=s.index('void write_preview(');s=s[:start]+tree_function(words)+s[end:];path.write_text(s,encoding='utf-8')
    path=X/'src/lm_head_v4_router.cpp';s=path.read_text(encoding='utf-8');s=replace(s,'float h[8][112],norm[128];unsigned lengths[128];',f'float h[8][112],norm[{c}];unsigned lengths[{c}];',1);s=replace(s,'float best[4];unsigned ids[4];',f'float best[{rr}];unsigned ids[{rr}];',1);s=replace(s,'i<4',f'i<{rr}');s=replace(s,'slot<4',f'slot<{rr}',1);s=replace(s,'route<4',f'route<{rr}',1);s=replace(s,'row<128',f'row<{c}',1);s=replace(s,'word<32',f'word<{c//4}',1);s=replace(s,'lengths[i]>16384',f'lengths[i]>{l}',1);s=replace(s,'cluster*4096',f'cluster*{l//4}',1)
    for old,new in [('center_capacity<14336',f'center_capacity<{c*112}'),('norm_capacity<32',f'norm_capacity<{c//4}'),('ranked_capacity<524288',f'ranked_capacity<{c*l//4}'),('count_capacity<32',f'count_capacity<{c//4}'),('*list_read_beats=32',f'*list_read_beats={c//4}'),('unsigned reads=32',f'unsigned reads={c//4}'),('*matrix_read_beats=14336',f'*matrix_read_beats={c*112}')]:s=replace(s,old,new)
    s=replace(s,'ap_uint<128>* selected_routes',f'ap_uint<{rr*32}>* selected_routes',1);s=replace(s,'ap_uint<128> selected=0;',f'ap_uint<{rr*32}> selected=0;',1);path.write_text(s,encoding='utf-8')
    path=X/'include/lm_head_v4_router.hpp';s=path.read_text(encoding='utf-8').replace('ap_uint<128>* selected_routes',f'ap_uint<{rr*32}>* selected_routes');path.write_text(s,encoding='utf-8')
    sizes=[272269312,1792,18992,2*e.V*rank,2*e.H*rank,2*c*e.H,4*c,4*c*l,4*c,607744,607760,607760,1215488]
    path=X/'src/lm_head_v4_selector.cpp';s=path.read_text(encoding='utf-8');s=replace(s,'h.range(47,32)!=1','h.range(47,32)!=2',1);s=replace(s,'config.range(95,64)!=16384',f'config.range(95,64)!={t}',1);s=replace(s,'config.range(127,96)!=0',f'config.range(127,96)!=0x{tag:08x}u',1);s,n=re.subn(r'const unsigned minimum\[SEL_REGIONS\]=\{[^}]+\}', 'const unsigned minimum[SEL_REGIONS]={'+','.join(map(str,sizes))+'}',s);assert n==1
    s=replace(s,'ap_uint<128> routes=0;',f'ap_uint<{rr*32}> routes=0;',1);s=replace(s,'112,14336,32,524288,32,37985',f'112,{c*112},{c//4},{c*l//4},{c//4},37985',1);s=replace(s,'151936,112,14336,2430976',f'151936,112,{rank*112},{e.V*words}',1);s=replace(s,'37985,16384,&code',f'37985,{t},&code',1)
    # Avoid2021.1 generated read_token block vs read_token task naming conflict.
    s=s.replace('ap_uint<32>* token,','ap_uint<32>* selected_token_out,').replace('port=token bundle=control','port=selected_token_out bundle=control').replace('*token=','*selected_token_out=');path.write_text(s,encoding='utf-8')
    path=X/'include/lm_head_v4_selector.hpp';s=path.read_text(encoding='utf-8').replace('ap_uint<32>* token,','ap_uint<32>* selected_token_out,');path.write_text(s,encoding='utf-8')
    pars=e.bind();router=e.model(pars,f'C{c}');factor=e.model(pars,f'r{rank}');norm=np.load(e.SOURCE/f'parameters/norms_C{c}.npy');counts=np.minimum(router['counts'],l).astype('<u4');ranked=router['ranked_ids'][:,:l].astype('<u4')
    def save(name,array):
        path=X/'fixture'/name
        if isinstance(array,bytes):path.write_bytes(array)
        else:path.write_bytes(array.tobytes())
    for name,array in [('a.bf16.bin',factor['a_bf16'].astype('<u2')),('bt.bf16.bin',factor['b_bf16'].T.copy().astype('<u2')),('router.centers.bin',router['centers_bf16'].astype('<u2')),('router.norms.bin',norm.astype('<f4')),('router.ranked.bin',ranked),('router.counts.bin',counts)]:save(name,array)
    names=['weight','hidden','history','a','bt','centers','norms','ranked','counts','preview','routed','merged','sparse'];offset=1048576+256;regions=[]
    for name,size in zip(names,sizes):
        offset=(offset+63)&~63;regions.append(dict(name=name,offset=offset,capacity=size,address=0x400000000+offset));offset+=size+64
    assert offset<=320*2**20
    desc=struct.pack('<IHHII',0x4353344d,2,13,240,0)+struct.pack('<IfII',7,1.1,t,tag)+b''.join(struct.pack('<QQ',x['offset'],x['capacity']) for x in regions);save('descriptor_debug.bin',desc);prod=bytearray(desc);struct.pack_into('<I',prod,16,6);struct.pack_into('<QQ',prod,32+12*16,0,0);save('descriptor_production.bin',bytes(prod))
    weights=np.memmap(M.parent/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin',dtype='<u2',mode='r',shape=(e.V,e.H));gold=[]
    for cat,(hidden,history) in b.fixture_inputs().items():
        routes,_=e.route_numpy(hidden,router['centers_bf16'],norm);routed,fallback=e.pure_route_candidates(router,routes[:rr],l);assert not fallback;preview,_=e.preview_numpy(hidden,factor['a_bf16'],factor['b_bf16'],b.seen_ids(history));low=np.union1d(np.argsort(-preview,kind='stable')[:t],e.SPECIAL);ids=np.union1d(routed,low).astype('<u4');result=e.run_candidate_head(hidden,weights,ids,history)
        save(cat+'.hidden.bin',hidden.astype('<u2'));save(cat+'.history.bin',history.astype('<u4'));save(cat+'.scores.bin',preview.astype('<f4'));save(cat+'.expected.bin',ids);sparse=np.empty((len(ids),2),dtype='<u4');sparse[:,0]=ids;sparse[:,1]=result['raw_scores'].view('u4');save(cat+'.sparse.bin',sparse);save(cat+'.result.bin',struct.pack('<IIII',result['selected_token'],result['selected_score_bits'],result['output_crc'],0));gold.append(dict(case=cat,k=len(ids),token=result['selected_token'],score_bits=result['selected_score_bits'],crc=result['output_crc']))
    s=(M/'tests/selector_csim.cpp').read_text(encoding='utf-8');line=next(x for x in s.splitlines() if 'std::string m=argv[1],fixture=' in x);s=replace(s,line,'    check(argc==2 || argc==3,"module path");bool rtl=argc==3;std::string m=argv[1],fixture=m+"/fixture/",lr=fixture,rt=fixture,chain=fixture;',1)
    weight_path=(M.parent/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin').as_posix();s=replace(s,'m+"/../artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin"','std::string("'+weight_path+'")',1);s=s.replace('m+"/reports/topk_fixture_20261021/"','m+"/fixture/"');s=s.replace('if(which==1)h.range(47,32)=2','if(which==1)h.range(47,32)=3').replace('cfg.range(95,64)=16383',f'cfg.range(95,64)={t-1}');s=s.replace('for(unsigned c=0;c<(rtl?1:4);++c){','const unsigned order[]={0,1,0,2,3};\n    for(unsigned turn=0;turn<(rtl?1:5);++turn){unsigned c=order[turn];');(X/'tests/selector_csim.cpp').write_text(s,encoding='utf-8')
    s=(M/'hls_selector.tcl').read_text(encoding='utf-8');s=s.replace('set module [file dirname [file normalize [info script]]]','set module [file dirname [file normalize [info script]]]').replace('-version 4.0','-version 4.10').replace('-vendor user.org','-vendor exp10.local');(X/'hls_selector.tcl').write_text(s,encoding='utf-8')
    manifest=dict(state='DERIVED_LOCKED_POINT_NOT_YET_HLS_TESTED',parameters=p,config_tag=f'0x{tag:08x}',selection_lock_sha256=b.sha(R/'SELECTION_LOCK.json'),source_generator_sha256=b.sha(Path(__file__)),source_sha256={x.relative_to(X).as_posix():b.sha(x) for folder in ['src','include','tests'] for x in (X/folder).glob('*') if x.is_file()},fixture_sha256={x.name:b.sha(x) for x in (X/'fixture').glob('*')},regions=regions,arena_bytes=320*2**20,allocated_end=offset,physical_base='0x400000000',descriptor_version=2,goldens=gold,scope='New private experiment, no changes to frozen sources/IP/packages; not board ready until all qualification gates complete')
    b.write(X/'MANIFEST.json',manifest);b.write(R/'HARDWARE_DERIVATION.json',manifest);print('EXP10_HARDWARE_DERIVED',p,'allocated',offset)
if __name__=='__main__':main()
