#include "lm_head_v4_topk.hpp"
namespace {
const unsigned V=151936, SCORE_BEATS=V/4, BITMAP_WORDS=V/128;
unsigned ordered_key(unsigned bits){
#pragma HLS INLINE
    if((bits&0x7fffffffu)==0)bits=0; // -0/+0 are numeric ties
    return (bits&0x80000000u)?~bits:(bits^0x80000000u);
}
bool load_route(const ap_uint<128>* table,unsigned capacity,unsigned top_k,unsigned output_capacity,
                ap_uint<128> selected[BITMAP_WORDS],unsigned& count,unsigned& reads){
    if(capacity<1)return false;
    const ap_uint<128> header=table[0];++reads;count=header.range(95,64).to_uint();
    if(header.range(31,0)!=0x4449344du || header.range(47,32)!=1 || header.range(63,48)!=4 ||
        header.range(127,96)!=V || count==0 || count>V || capacity<1+(count+3)/4)return false;
    const unsigned bound=(count+top_k>V)?V:count+top_k;
    if(output_capacity<1+(bound+3)/4)return false;
    ap_uint<128> packed=0,mask=0;unsigned cached=0xffffffffu,previous=0;
route_id_loop:
    for(unsigned row=0;row<count;++row){
#pragma HLS PIPELINE off
#pragma HLS LOOP_TRIPCOUNT min=1 max=151936
        if((row&3)==0){packed=table[1+(row>>2)];++reads;}
        const int lane=row&3;const unsigned id=packed.range(lane*32+31,lane*32).to_uint();
        if(id>=V || (row!=0 && id<=previous))return false;
        const unsigned block=id>>7;
        if(block!=cached){if(cached!=0xffffffffu)selected[cached]=mask;cached=block;mask=0;}
        mask[id&127]=1;previous=id;
    }
    selected[cached]=mask;return true;
}
bool histogram_pass(const ap_uint<128>* scores,unsigned prefix,unsigned mask,unsigned shift,
                    unsigned histogram[4][256]){
#pragma HLS INLINE off
#pragma HLS ARRAY_PARTITION variable=histogram complete dim=1
clear_histogram:
    for(unsigned bin=0;bin<256;++bin){
#pragma HLS PIPELINE II=1
        for(unsigned lane=0;lane<4;++lane){
#pragma HLS UNROLL
            histogram[lane][bin]=0;
        }
    }
    bool bad=false;
histogram_score_loop:
    for(unsigned beat=0;beat<SCORE_BEATS;++beat){
#pragma HLS PIPELINE II=2
        const ap_uint<128> packed=scores[beat];
histogram_lanes:
        for(unsigned lane=0;lane<4;++lane){
#pragma HLS UNROLL
            const unsigned bits=packed.range(lane*32+31,lane*32).to_uint();
            bad|=(bits&0x7f800000u)==0x7f800000u;
            const unsigned key=ordered_key(bits);
            if((key&mask)==prefix){const unsigned bin=(key>>shift)&255u;histogram[lane][bin]=histogram[lane][bin]+1;}
        }
    }
    return !bad;
}
bool pick_bucket(unsigned histogram[4][256],unsigned& rank,unsigned& chosen){
#pragma HLS INLINE off
#pragma HLS ARRAY_PARTITION variable=histogram complete dim=1
    bool found=false;
select_descending_bucket:
    for(int bin=255;bin>=0;--bin){
#pragma HLS PIPELINE II=1
        const unsigned n01=histogram[0][bin]+histogram[1][bin];
        const unsigned n23=histogram[2][bin]+histogram[3][bin];
        const unsigned n=n01+n23;
        if(!found){if(n>=rank){chosen=bin;found=true;}else rank-=n;}
    }
    return found;
}
void mark_topk(const ap_uint<128>* scores,unsigned cutoff,unsigned tie_budget,ap_uint<128> selected[BITMAP_WORDS]){
    unsigned ties_seen=0;
mark_bitmap_word:
    for(unsigned word=0;word<BITMAP_WORDS;++word){
        ap_uint<128> mask=selected[word];
mark_score_loop:
        for(unsigned beat=0;beat<32;++beat){
#pragma HLS PIPELINE II=2
            const ap_uint<128> packed=scores[word*32+beat];
            ap_uint<4> flags=0;
mark_lanes:
            for(unsigned lane=0;lane<4;++lane){
#pragma HLS UNROLL
                const unsigned key=ordered_key(packed.range(lane*32+31,lane*32).to_uint());
                const bool tie=key==cutoff;
                flags[lane]=key>cutoff || (tie && ties_seen<tie_budget);
                if(tie)++ties_seen;
            }
            mask|=ap_uint<128>(flags)<<(beat*4);
        }
        selected[word]=mask;
    }
}
unsigned emit_table(const ap_uint<128> selected[BITMAP_WORDS],ap_uint<128>* output,unsigned& writes){
    unsigned count=0;ap_uint<128> packed=0;
emit_bitmap_word:
    for(unsigned word=0;word<BITMAP_WORDS;++word){
        const ap_uint<128> mask=selected[word];
emit_bitmap_bit:
        for(unsigned bit=0;bit<128;++bit){
#pragma HLS PIPELINE II=1
            if(mask[bit]){
                const int lane=count&3;packed.range(lane*32+31,lane*32)=word*128+bit;++count;
                if((count&3)==0){output[count>>2]=packed;packed=0;++writes;}
            }
        }
    }
    if(count&3){output[1+(count>>2)]=packed;++writes;}
    ap_uint<128> header=0;header.range(31,0)=0x4449344du;header.range(47,32)=1;header.range(63,48)=4;
    header.range(95,64)=count;header.range(127,96)=V;output[0]=header;++writes;return count;
}
}
extern "C" void lm_head_v4_topk_union(
    const ap_uint<128>* policy_preview,const ap_uint<128>* routed_table,ap_uint<128>* output_table,
    ap_uint<32> score_capacity_beats,ap_uint<32> route_capacity_beats,ap_uint<32> output_capacity_beats,
    ap_uint<32> top_k,ap_uint<32>* status,ap_uint<32>* union_count,
    ap_uint<64>* score_read_beats,ap_uint<32>* route_read_beats,ap_uint<32>* output_write_beats){
#pragma HLS INTERFACE m_axi port=policy_preview offset=slave bundle=preview depth=37984 max_read_burst_length=64 num_read_outstanding=8
#pragma HLS INTERFACE m_axi port=routed_table offset=slave bundle=route depth=37985 max_read_burst_length=64 num_read_outstanding=4
#pragma HLS INTERFACE m_axi port=output_table offset=slave bundle=output depth=37985 max_write_burst_length=64 num_write_outstanding=4
#pragma HLS INTERFACE s_axilite port=policy_preview bundle=control
#pragma HLS INTERFACE s_axilite port=routed_table bundle=control
#pragma HLS INTERFACE s_axilite port=output_table bundle=control
#pragma HLS INTERFACE s_axilite port=score_capacity_beats bundle=control
#pragma HLS INTERFACE s_axilite port=route_capacity_beats bundle=control
#pragma HLS INTERFACE s_axilite port=output_capacity_beats bundle=control
#pragma HLS INTERFACE s_axilite port=top_k bundle=control
#pragma HLS INTERFACE s_axilite port=status bundle=control
#pragma HLS INTERFACE s_axilite port=union_count bundle=control
#pragma HLS INTERFACE s_axilite port=score_read_beats bundle=control
#pragma HLS INTERFACE s_axilite port=route_read_beats bundle=control
#pragma HLS INTERFACE s_axilite port=output_write_beats bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
    *status=LMH4_TOPK_BAD_CONFIG;*union_count=0;*score_read_beats=0;*route_read_beats=0;*output_write_beats=0;
    const unsigned k=top_k.to_uint();if(k==0 || k>V || score_capacity_beats<SCORE_BEATS)return;
    ap_uint<128> selected[BITMAP_WORDS];unsigned histogram[4][256];
#pragma HLS BIND_STORAGE variable=selected type=ram_2p impl=bram
#pragma HLS ARRAY_PARTITION variable=histogram complete dim=1
#pragma HLS BIND_STORAGE variable=histogram type=ram_2p impl=bram
clear_bitmap:
    for(unsigned i=0;i<BITMAP_WORDS;++i){
#pragma HLS PIPELINE II=1
        selected[i]=0;
    }
    unsigned route_count=0,route_reads=0;
    if(!load_route(routed_table,route_capacity_beats.to_uint(),k,output_capacity_beats.to_uint(),selected,route_count,route_reads)){
        *route_read_beats=route_reads;*status=LMH4_TOPK_BAD_ROUTE;return;
    }
    *route_read_beats=route_reads;
    unsigned prefix=0,prefix_mask=0,rank=k;
radix_pass:
    for(unsigned pass=0;pass<4;++pass){
        const unsigned shift=24-pass*8;
        const bool finite=histogram_pass(policy_preview,prefix,prefix_mask,shift,histogram);
        *score_read_beats=ap_uint<64>((pass+1)*SCORE_BEATS);
        if(!finite){*status=LMH4_TOPK_NUMERIC;return;}
        unsigned bucket=0;if(!pick_bucket(histogram,rank,bucket)){*status=LMH4_TOPK_INTERNAL;return;}
        prefix|=bucket<<shift;prefix_mask|=255u<<shift;
    }
    mark_topk(policy_preview,prefix,rank,selected);*score_read_beats=5*SCORE_BEATS;
    unsigned writes=0;const unsigned count=emit_table(selected,output_table,writes);
    *union_count=count;*output_write_beats=writes;*status=LMH4_TOPK_OK;
}
