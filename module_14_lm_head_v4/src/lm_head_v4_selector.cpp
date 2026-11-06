#include "lm_head_v4_selector.hpp"
// Import unchanged component implementations once; the shared accepted core
// consequently has one definition. Local constant rename only, no arithmetic
// replacement and no edits to the already audited component source files.
#include "lm_head_v4_lowrank.cpp"
#define V ROUTER_V_IN_SELECTOR
#include "lm_head_v4_router.cpp"
#undef V
#include "lm_head_v4_topk.cpp"
#include "lm_head_v4_candidate.cpp"

namespace {
const unsigned long long ARENA_MAX=335544320ull; // private standalone320MiB
const unsigned DESC_BYTES=240;
struct Region {ap_uint<64> off,size;};
bool overlaps(ap_uint<64> a,ap_uint<64> n,ap_uint<64> b,ap_uint<64> m){
#pragma HLS INLINE
    // Called only after off+size has been proven within the bounded arena.
    return a<b+m && b<a+n;
}
unsigned read_descriptor(ap_uint<128>* arena,ap_uint<64> arena_size,ap_uint<64> offset,
                         Region regions[SEL_REGIONS],unsigned& flags,float& penalty){
#pragma HLS INLINE off
    if(arena_size==0 || arena_size>ARENA_MAX || (arena_size&15)!=0 || (offset&15)!=0 ||
       offset>arena_size || arena_size-offset<DESC_BYTES)return SEL_BAD_DESCRIPTOR;
    const unsigned long long base=offset.to_uint64()>>4;
    const ap_uint<128> h=arena[base],config=arena[base+1];
    if(h.range(31,0)!=0x4353344du || h.range(47,32)!=1 || h.range(63,48)!=SEL_REGIONS ||
       h.range(95,64)!=DESC_BYTES || h.range(127,96)!=0)return SEL_BAD_DESCRIPTOR;
    flags=config.range(31,0).to_uint();penalty=lmh4_detail::bits_to_float(config.range(63,32).to_uint());
    if((flags&~7u)!=0 || config.range(95,64)!=16384 || config.range(127,96)!=0 ||
       ((flags&2u) && (!lmh4_detail::finite_float(penalty) || penalty<1.0f)))return SEL_BAD_CONFIG;
    const unsigned minimum[SEL_REGIONS]={272269312,1792,18992,38895616,229376,229376,512,8388608,512,607744,607760,607760,1215488};
read_regions:
    for(unsigned i=0;i<SEL_REGIONS;++i){
#pragma HLS PIPELINE off
        const ap_uint<128> record=arena[base+2+i];
        regions[i].off=record.range(63,0);regions[i].size=record.range(127,64);
        const ap_uint<64> start=regions[i].off,size=regions[i].size;
        const bool optional=i==SEL_SPARSE && !(flags&1u);
        if(optional){if(start!=0 || size!=0)return SEL_BAD_REGION;continue;}
        if((start&15)!=0 || (size&15)!=0 || size<minimum[i] || start>arena_size || size>arena_size-start)return SEL_BAD_REGION;
        if(overlaps(start,size,offset,DESC_BYTES))return SEL_OVERLAP;
    }
check_region_pairs:
    for(unsigned i=0;i<SEL_REGIONS;++i){
#pragma HLS PIPELINE off
        if(regions[i].size==0)continue;
        for(unsigned j=0;j<i;++j){
#pragma HLS PIPELINE off
            if(regions[j].size!=0 && overlaps(regions[i].off,regions[i].size,regions[j].off,regions[j].size))return SEL_OVERLAP;
        }
    }
    return SEL_OK;
}
}
extern "C" void lm_head_v4_selector(
    ap_uint<128>* pl_ddr,const ap_uint<128>* history_bitmap,ap_uint<64> arena_bytes,ap_uint<64> descriptor_offset,ap_uint<32> command,
    ap_uint<32>* status,ap_uint<32>* stage,ap_uint<32>* child_status,
    ap_uint<32>* route_count,ap_uint<32>* candidate_count,ap_uint<32>* dense_fallback,
    ap_uint<32>* token,float* score,ap_uint<32>* output_crc){
#pragma HLS INTERFACE m_axi port=pl_ddr offset=slave bundle=plmem depth=20971520 max_read_burst_length=64 num_read_outstanding=16 max_write_burst_length=64 num_write_outstanding=8
#pragma HLS INTERFACE m_axi port=history_bitmap offset=slave bundle=histmem depth=1187 max_read_burst_length=16 num_read_outstanding=4
#pragma HLS INTERFACE s_axilite port=pl_ddr bundle=control
#pragma HLS INTERFACE s_axilite port=history_bitmap bundle=control
#pragma HLS INTERFACE s_axilite port=arena_bytes bundle=control
#pragma HLS INTERFACE s_axilite port=descriptor_offset bundle=control
#pragma HLS INTERFACE s_axilite port=command bundle=control
#pragma HLS INTERFACE s_axilite port=status bundle=control
#pragma HLS INTERFACE s_axilite port=stage bundle=control
#pragma HLS INTERFACE s_axilite port=child_status bundle=control
#pragma HLS INTERFACE s_axilite port=route_count bundle=control
#pragma HLS INTERFACE s_axilite port=candidate_count bundle=control
#pragma HLS INTERFACE s_axilite port=dense_fallback bundle=control
#pragma HLS INTERFACE s_axilite port=token bundle=control
#pragma HLS INTERFACE s_axilite port=score bundle=control
#pragma HLS INTERFACE s_axilite port=output_crc bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
    *status=SEL_BAD_DESCRIPTOR;*stage=SEL_PREFLIGHT;*child_status=0;*route_count=0;*candidate_count=0;
    *dense_fallback=0;*token=0;*score=0.0f;*output_crc=0;
    if(command>SEL_VALIDATE_ONLY){*status=SEL_BAD_CONFIG;return;}
    Region regions[SEL_REGIONS];unsigned flags=0;float penalty=1.0f;
    const unsigned checked=read_descriptor(pl_ddr,arena_bytes,descriptor_offset,regions,flags,penalty);
    if(checked!=SEL_OK){*status=checked;return;}
    if(command==SEL_VALIDATE_ONLY){*status=SEL_OK;return;}
    // The whole descriptor and all reserved intervals have now been checked.
    // Invalidate previous published scratch headers before the first producer.
    ap_uint<128>* weights=pl_ddr+(regions[SEL_WEIGHT].off.to_uint64()>>4);
    ap_uint<128>* hidden=pl_ddr+(regions[SEL_HIDDEN].off.to_uint64()>>4);
    // Separate PL DDR read master required by nested DATAFLOW in2021.1.
    // Driver must set its pointer to arena_base+validated HISTORY offset.
    // The BD maps BOTH masters exclusively to MIG, never to PS DDR.
    const ap_uint<128>* history=history_bitmap;
    ap_uint<128>* a=pl_ddr+(regions[SEL_A].off.to_uint64()>>4);
    ap_uint<128>* bt=pl_ddr+(regions[SEL_BT].off.to_uint64()>>4);
    ap_uint<128>* centers=pl_ddr+(regions[SEL_CENTERS].off.to_uint64()>>4);
    ap_uint<128>* norms=pl_ddr+(regions[SEL_NORMS].off.to_uint64()>>4);
    ap_uint<128>* ranked=pl_ddr+(regions[SEL_RANKED].off.to_uint64()>>4);
    ap_uint<128>* counts=pl_ddr+(regions[SEL_COUNTS].off.to_uint64()>>4);
    ap_uint<128>* preview=pl_ddr+(regions[SEL_PREVIEW].off.to_uint64()>>4);
    ap_uint<128>* routed=pl_ddr+(regions[SEL_ROUTED].off.to_uint64()>>4);
    ap_uint<128>* merged=pl_ddr+(regions[SEL_MERGED].off.to_uint64()>>4);
    ap_uint<128>* sparse=pl_ddr+(regions[SEL_SPARSE].off.to_uint64()>>4);
    routed[0]=0;merged[0]=0;
    ap_uint<32> code=0,rk=0,k=0,fallback=0,matrix_reads=0,list_reads=0,writes=0;
    ap_uint<128> routes=0;*stage=SEL_ROUTE_STAGE;
    lm_head_v4_router(hidden,centers,norms,ranked,counts,routed,112,14336,32,524288,32,37985,
        &code,&routes,&rk,&fallback,&matrix_reads,&list_reads,&writes);
    *route_count=rk;*dense_fallback=fallback;
    if(code!=0){*child_status=code;*status=SEL_CHILD_FAILED;return;}
    if(fallback && !(flags&4u)){*status=SEL_FALLBACK_FORBIDDEN;return;}
    ap_uint<64> factor_reads=0;*stage=SEL_LOWRANK_STAGE;
    lm_head_v4_lowrank(hidden,bt,a,history,preview,151936,112,14336,2430976,1187,37984,
        (flags>>1)&1u,penalty,&code,&factor_reads,&writes);
    if(code!=0){*child_status=code;*status=SEL_CHILD_FAILED;return;}
    ap_uint<64> score_reads=0;*stage=SEL_TOPK_STAGE;
    lm_head_v4_topk_union(preview,routed,merged,37984,37985,37985,16384,&code,&k,&score_reads,&list_reads,&writes);
    *candidate_count=k;
    if(code!=0){*child_status=code;*status=SEL_CHILD_FAILED;return;}
    ap_uint<32> final_token=0,processed=0,history_reads=0,score_writes=0,crc=0;
    ap_uint<64> index_reads=0,weight_reads=0;float final_score=0.0f;*stage=SEL_EXACT_STAGE;
    lm_head_v4_candidate(hidden,weights,history,merged,sparse,37985,75968,flags&1u,(flags>>1)&1u,penalty,
        &code,&final_token,&final_score,&processed,&index_reads,&weight_reads,&history_reads,&score_writes,&crc);
    if(code!=0){*child_status=code;*status=SEL_CHILD_FAILED;return;}
    *token=final_token;*score=final_score;*output_crc=crc;*stage=SEL_DONE;*status=SEL_OK;
}
