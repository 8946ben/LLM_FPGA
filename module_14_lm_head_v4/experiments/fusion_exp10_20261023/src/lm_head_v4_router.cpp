#include "lm_head_v4_router.hpp"
#include "accepted_numeric_core.hpp"
using namespace lmh4_detail;
namespace {
const unsigned V=151936,WORDS=V/128;
float dot896(const float h[8][112],const ap_uint<128>* matrix,unsigned row,bool self){
#pragma HLS INLINE off
    float p[8][16];
#pragma HLS ARRAY_PARTITION variable=p complete dim=1
    for(unsigned lane=0;lane<8;++lane){
#pragma HLS UNROLL
        for(unsigned slot=0;slot<16;++slot){
#pragma HLS UNROLL
            p[lane][slot]=0.0f;
        }
    }
router_dot_word:
    for(unsigned word=0;word<112;++word){
#pragma HLS PIPELINE II=1
#pragma HLS DEPENDENCE variable=p inter RAW distance=16 true
        const ap_uint<128> packed=self?ap_uint<128>(0):matrix[row*112+word];
        for(unsigned lane=0;lane<8;++lane){
#pragma HLS UNROLL
            const float coefficient=self?h[lane][word]:bf16_to_float(packed.range(16*lane+15,16*lane));
            const float product=h[lane][word]*coefficient;p[lane][word&15]=p[lane][word&15]+product;
        }
    }
    return reduce_partials(p);
}
unsigned emit(const ap_uint<128> bitmap[WORDS],bool full,ap_uint<128>* out,unsigned& writes){
    unsigned count=0;ap_uint<128> packed=0;
router_emit_word:
    for(unsigned word=0;word<WORDS;++word){
        const ap_uint<128> mask=full?~ap_uint<128>(0):bitmap[word];
router_emit_bit:
        for(unsigned bit=0;bit<128;++bit){
#pragma HLS PIPELINE II=1
            if(mask[bit]){
                packed.range(32*(count&3)+31,32*(count&3))=word*128+bit;++count;
                if((count&3)==0){out[count>>2]=packed;packed=0;++writes;}
            }
        }
    }
    if(count&3){out[1+(count>>2)]=packed;++writes;}
    ap_uint<128> header=0;header.range(31,0)=0x4449344du;header.range(47,32)=1;header.range(63,48)=4;
    header.range(95,64)=count;header.range(127,96)=V;out[0]=header;++writes;return count;
}
}
extern "C" void lm_head_v4_router(
    const ap_uint<128>* hidden,const ap_uint<128>* centers,const ap_uint<128>* norms,
    const ap_uint<128>* ranked_ids,const ap_uint<128>* counts,ap_uint<128>* routed_table,
    ap_uint<32> hidden_capacity,ap_uint<32> center_capacity,ap_uint<32> norm_capacity,
    ap_uint<32> ranked_capacity,ap_uint<32> count_capacity,ap_uint<32> output_capacity,
    ap_uint<32>* status,ap_uint<128>* selected_routes,ap_uint<32>* candidate_count,
    ap_uint<32>* dense_fallback,ap_uint<32>* matrix_read_beats,ap_uint<32>* list_read_beats,
    ap_uint<32>* output_write_beats){
#pragma HLS INTERFACE m_axi port=hidden offset=slave bundle=hidden depth=112
#pragma HLS INTERFACE m_axi port=centers offset=slave bundle=centers depth=14336 max_read_burst_length=64 num_read_outstanding=8
#pragma HLS INTERFACE m_axi port=norms offset=slave bundle=meta depth=32
#pragma HLS INTERFACE m_axi port=counts offset=slave bundle=meta depth=32
#pragma HLS INTERFACE m_axi port=ranked_ids offset=slave bundle=lists depth=524288 max_read_burst_length=64 num_read_outstanding=8
#pragma HLS INTERFACE m_axi port=routed_table offset=slave bundle=output depth=37985 max_write_burst_length=64 num_write_outstanding=4
#pragma HLS INTERFACE s_axilite port=hidden bundle=control
#pragma HLS INTERFACE s_axilite port=centers bundle=control
#pragma HLS INTERFACE s_axilite port=norms bundle=control
#pragma HLS INTERFACE s_axilite port=ranked_ids bundle=control
#pragma HLS INTERFACE s_axilite port=counts bundle=control
#pragma HLS INTERFACE s_axilite port=routed_table bundle=control
#pragma HLS INTERFACE s_axilite port=hidden_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=center_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=norm_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=ranked_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=count_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=output_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=status bundle=control
#pragma HLS INTERFACE s_axilite port=selected_routes bundle=control
#pragma HLS INTERFACE s_axilite port=candidate_count bundle=control
#pragma HLS INTERFACE s_axilite port=dense_fallback bundle=control
#pragma HLS INTERFACE s_axilite port=matrix_read_beats bundle=control
#pragma HLS INTERFACE s_axilite port=list_read_beats bundle=control
#pragma HLS INTERFACE s_axilite port=output_write_beats bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
    *status=LMH4_ROUTE_BAD_CONFIG;*selected_routes=0;*candidate_count=0;*dense_fallback=0;
    *matrix_read_beats=0;*list_read_beats=0;*output_write_beats=0;
    if(hidden_capacity<112 || center_capacity<28672 || norm_capacity<64 || ranked_capacity<524288 || count_capacity<64 || output_capacity<1)return;
    float h[8][112],norm[256];unsigned lengths[256];
#pragma HLS ARRAY_PARTITION variable=h complete dim=1
    load_hidden(hidden,h);bool bad_h=false,bad_meta=false;
router_check_hidden:
    for(unsigned w=0;w<112;++w){
#pragma HLS PIPELINE II=1
        bool bad=false;
        for(unsigned lane=0;lane<8;++lane){
#pragma HLS UNROLL
            bad|=!finite_float(h[lane][w]);
        }
        bad_h|=bad;
    }
    if(bad_h){*status=LMH4_ROUTE_NUMERIC;return;}
router_load_meta:
    for(unsigned word=0;word<64;++word){
#pragma HLS PIPELINE II=2
        const ap_uint<128> n=norms[word],c=counts[word];
        for(unsigned lane=0;lane<4;++lane){
#pragma HLS UNROLL
            const unsigned i=word*4+lane;norm[i]=bits_to_float(n.range(32*lane+31,32*lane).to_uint());
            lengths[i]=c.range(32*lane+31,32*lane).to_uint();
            bad_meta|=!finite_float(norm[i]) || norm[i]<0 || lengths[i]>8192;
        }
    }
    *list_read_beats=64;if(bad_meta){*status=LMH4_ROUTE_BAD_TABLE;return;}
    const float hn=dot896(h,centers,0,true);
    float best[4];unsigned ids[4];
#pragma HLS ARRAY_PARTITION variable=best complete
#pragma HLS ARRAY_PARTITION variable=ids complete
    for(unsigned i=0;i<4;++i){
#pragma HLS UNROLL
        best[i]=bits_to_float(0x7f800000u);ids[i]=0xffffffffu;
    }
    bool bad=!finite_float(hn);
router_center_row:
    for(unsigned row=0;row<256;++row){
        const float dot=dot896(h,centers,row,false);
        const float sums=hn+norm[row];const float twice=2.0f*dot;const float distance=sums-twice;
        bad|=!finite_float(distance);float value=distance;unsigned id=row;
router_insert_four:
        for(unsigned slot=0;slot<4;++slot){
#pragma HLS PIPELINE off
            if(value<best[slot] || (value==best[slot] && id<ids[slot])){
                const float old=best[slot];const unsigned old_id=ids[slot];best[slot]=value;ids[slot]=id;value=old;id=old_id;
            }
        }
    }
    *matrix_read_beats=28672;if(bad){*status=LMH4_ROUTE_NUMERIC;return;}
    bool full=false;unsigned bound=14;
    for(unsigned i=0;i<4;++i){
#pragma HLS UNROLL
        full|=lengths[ids[i]]==0;bound+=lengths[ids[i]];
    }
    if(full)bound=V;else if(bound>V)bound=V;
    if(output_capacity<1+(bound+3)/4){*status=LMH4_ROUTE_BAD_CONFIG;return;}
    ap_uint<128> bitmap[WORDS];
#pragma HLS BIND_STORAGE variable=bitmap type=ram_2p impl=bram
router_clear_bitmap:
    for(unsigned w=0;w<WORDS;++w){
#pragma HLS PIPELINE II=1
        bitmap[w]=0;
    }
    unsigned reads=64;
    if(!full){
        // Avoid ap_uint memory bit-reference stores: 2021.1 lowered them to
        // byte-enable writes that replaced other bits in that byte in RTL.
        // Keep the entire word in a register, OR whole-word one-hot masks,
        // and flush/load complete words when the (unsorted) list changes block.
        unsigned cached=0xffffffffu;ap_uint<128> mask=0;
router_list:
        for(unsigned route=0;route<4;++route){
#pragma HLS PIPELINE off
            const unsigned cluster=ids[route],count=lengths[cluster];ap_uint<128> packed=0;
router_ranked_id:
            for(unsigned row=0;row<count;++row){
#pragma HLS PIPELINE off
#pragma HLS LOOP_TRIPCOUNT min=1 max=16384
                if((row&3)==0){packed=ranked_ids[cluster*2048+(row>>2)];++reads;}
                const unsigned id=packed.range(32*(row&3)+31,32*(row&3)).to_uint();
                if(id>=V){*list_read_beats=reads;*status=LMH4_ROUTE_BAD_TABLE;return;}
                const unsigned block=id>>7;
                if(block!=cached){if(cached!=0xffffffffu)bitmap[cached]=mask;mask=bitmap[block];cached=block;}
                mask|=ap_uint<128>(1)<<(id&127);
            }
        }
router_mandatory:
        for(unsigned id=151643;id<=151656;++id){
#pragma HLS PIPELINE off
            const unsigned block=id>>7;
            if(block!=cached){if(cached!=0xffffffffu)bitmap[cached]=mask;mask=bitmap[block];cached=block;}
            mask|=ap_uint<128>(1)<<(id&127);
        }
        bitmap[cached]=mask;
    }
    unsigned writes=0;const unsigned count=emit(bitmap,full,routed_table,writes);
    ap_uint<128> selected=0;
    for(unsigned i=0;i<4;++i){
#pragma HLS UNROLL
        selected.range(32*i+31,32*i)=ids[i];
    }
    *selected_routes=selected;*candidate_count=count;*dense_fallback=full?1:0;
    *list_read_beats=reads;*output_write_beats=writes;*status=LMH4_ROUTE_OK;
}
