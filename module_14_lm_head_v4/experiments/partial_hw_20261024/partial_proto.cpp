#include "partial_proto.hpp"
#include "lm_head_v4_candidate.hpp"
namespace {
typedef ap_uint<128> Beat;
union Fbits {float f;unsigned u;};
unsigned bits(float x) { Fbits v;v.f=x;return v.u; }
float flt(unsigned u) { Fbits v;v.u=u;return v.f; }
float bf(ap_uint<16> u) {return flt(u.to_uint()<<16);}
bool finite(float x) {return (bits(x)&0x7f800000u)!=0x7f800000u;}
unsigned sort_key(float x) {
#pragma HLS INLINE
    unsigned u=bits(x);if(x==0.0f)u=0;
    return (u&0x80000000u)?~u:(u^0x80000000u);
}

bool select_channels(const Beat* meta,float h[P_H],unsigned history[4748],unsigned dims[P_D]) {
#pragma HLS INLINE off
    unsigned keys[P_D];bool bad=false;
init_channels:
    for(int j=0;j<P_D;++j) {
#pragma HLS PIPELINE II=1
        keys[j]=0;dims[j]=0xffffffffu;
    }
load_hidden:
    for(int word=0;word<112;++word) {
#pragma HLS PIPELINE II=1
        Beat b=meta[word];
        for(int lane=0;lane<8;++lane) {
#pragma HLS UNROLL
            float value=bf(b.range(16*lane+15,16*lane));h[word*8+lane]=value;bad|=!finite(value);
        }
    }
load_history:
    for(int word=0;word<1187;++word) {
#pragma HLS PIPELINE II=1
        Beat b=meta[P_META_HISTORY+word];
        for(int lane=0;lane<4;++lane) {
#pragma HLS UNROLL
            history[word*4+lane]=b.range(32*lane+31,32*lane).to_uint();
        }
    }
    Beat rms_word=0;
channel_loop:
    for(unsigned channel=0;channel<P_H;++channel) {
        if((channel&3)==0)rms_word=meta[112+(channel>>2)];
        float rms=flt(rms_word.range(32*(channel&3)+31,32*(channel&3)).to_uint());
        float absolute=flt(bits(h[channel])&0x7fffffffu);float value=absolute*rms;
        bad|=!finite(rms)||rms<0.0f||!finite(value);
        unsigned carry_key=sort_key(value),carry_id=channel;
channel_insert:
        for(int j=0;j<P_D;++j) {
#pragma HLS PIPELINE II=1
            unsigned old_key=keys[j],old_id=dims[j];
            if(carry_key>old_key || (carry_key==old_key && carry_id<old_id)) {
                keys[j]=carry_key;dims[j]=carry_id;carry_key=old_key;carry_id=old_id;
            }
        }
    }
    return bad;
}

bool partial_preview(const Beat* weight,const float h[P_H],const unsigned history[4748],
                     const unsigned dims[P_D],Beat* workspace) {
#pragma HLS INLINE off
    float stack[7][128][8];
#pragma HLS ARRAY_PARTITION variable=stack complete dim=1
#pragma HLS ARRAY_PARTITION variable=stack complete dim=3
    bool bad=false;
preview_tile_loop:
    for(unsigned tile=0;tile<P_TILES;++tile) {
preview_channel_loop:
        for(unsigned rank=0;rank<P_D;++rank) {
            unsigned channel=dims[rank];float hidden=h[channel];
            unsigned base=(tile*P_H+channel)*128;
preview_beat_loop:
            for(int word=0;word<128;++word) {
#pragma HLS PIPELINE II=1
                Beat packed=weight[base+word];
preview_lanes:
                for(int lane=0;lane<8;++lane) {
#pragma HLS UNROLL
                    float value=bf(packed.range(16*lane+15,16*lane))*hidden;
carry_levels:
                    for(int level=0;level<7;++level) {
#pragma HLS UNROLL
                        // Same adjacent FP32 tree, with left subtree + right.
                        unsigned count=rank+1;
                        if((count&((1u<<level)-1u))==0) {
                            if(count&(1u<<level))stack[level][word][lane]=value;
                            else value=stack[level][word][lane]+value;
                        }
                    }
                }
            }
        }
emit_preview_words:
        for(unsigned word=0;word<256;++word) {
#pragma HLS PIPELINE II=2
            Beat raw_word=0,key_word=0;
            unsigned first=tile*P_B+word*4;
            if(first<P_V) {
                unsigned seen=history[first>>5];
emit_preview_lanes:
                for(int lane=0;lane<4;++lane) {
#pragma HLS UNROLL
                    unsigned id=first+lane;
                    float raw=stack[6][word>>1][(word&1)*4+lane];
                    bool used=((seen>>(id&31))&1u)!=0;
                    float policy=used?(raw<0.0f?raw*1.1f:raw/1.1f):raw;
                    bad|=!finite(raw)||!finite(policy);
                    raw_word.range(32*lane+31,32*lane)=bits(raw);
                    key_word.range(32*lane+31,32*lane)=sort_key(policy);
                }
                workspace[P_PREVIEW+(first>>2)]=raw_word;
                workspace[P_KEY+(first>>2)]=key_word;
            }
        }
    }
    return bad;
}

unsigned radix_candidates(Beat* workspace) {
#pragma HLS INLINE off
    unsigned hist[256];
#pragma HLS BIND_STORAGE variable=hist type=ram_2p impl=bram
    unsigned prefix=0,mask=0,remaining=P_T;
radix_pass_loop:
    for(int pass=0;pass<4;++pass) {
clear_histogram:
        for(unsigned b=0;b<256;++b) {
#pragma HLS PIPELINE II=1
            hist[b]=0;
        }
        unsigned shift=24-pass*8;
radix_word_loop:
        for(unsigned word=0;word<P_V/4;++word) {
            Beat packed=workspace[P_KEY+word];
radix_key_loop:
            for(int lane=0;lane<4;++lane) {
#pragma HLS PIPELINE II=1
                unsigned key=packed.range(lane*32+31,lane*32).to_uint();
                if((key&mask)==prefix) {unsigned digit=(key>>shift)&255;hist[digit]=hist[digit]+1;}
            }
        }
        bool found=false;unsigned bucket=0;
find_threshold_bucket:
        for(int b=255;b>=0;--b) {
#pragma HLS PIPELINE II=1
            unsigned n=hist[b];
            if(!found) {
                if(remaining<=n) {bucket=b;found=true;}
                else remaining-=n;
            }
        }
        prefix|=bucket<<shift;mask|=255u<<shift;
    }
    unsigned count=0;Beat packed_ids=~Beat(0);
candidate_word_loop:
    for(unsigned word=0;word<P_V/4;++word) {
        Beat packed=workspace[P_KEY+word];
candidate_lane_loop:
        for(unsigned lane=0;lane<4;++lane) {
#pragma HLS PIPELINE II=1
            unsigned id=word*4+lane,key=packed.range(lane*32+31,lane*32).to_uint();
            bool tied=key==prefix && remaining!=0;
            bool selected=key>prefix || tied;
            if(tied)--remaining;
            if(selected || (id>=151643 && id<151657)) {
                packed_ids.range((count&3)*32+31,(count&3)*32)=id;
                if((count&3)==3) {workspace[P_TABLE+1+(count>>2)]=packed_ids;packed_ids=~Beat(0);}
                ++count;
            }
        }
    }
    if(count&3)workspace[P_TABLE+1+(count>>2)]=packed_ids;
    Beat header=0;header.range(31,0)=0x4449344du;header.range(47,32)=1;
    header.range(63,48)=4;header.range(95,64)=count;header.range(127,96)=P_V;
    workspace[P_TABLE]=header;return count;
}
}

extern "C" void lm_head_v4_partial_proto(const ap_uint<128>* meta,
    const ap_uint<128>* tiled_weight,const ap_uint<128>* canonical_weight,
    ap_uint<128>* workspace,unsigned capacity_beats,unsigned debug,
    ap_uint<32>* status,ap_uint<32>* token,ap_uint<32>* score_bits,
    ap_uint<32>* candidate_count,ap_uint<32>* output_crc,ap_uint<64>* preview_read_beats) {
#pragma HLS INTERFACE m_axi port=meta offset=slave bundle=meta depth=1523 max_read_burst_length=128
#pragma HLS INTERFACE m_axi port=tiled_weight offset=slave bundle=weights depth=17088512 max_read_burst_length=128
#pragma HLS INTERFACE m_axi port=canonical_weight offset=slave bundle=weights depth=17016832 max_read_burst_length=128
#pragma HLS INTERFACE m_axi port=workspace offset=slave bundle=meta depth=79068 max_read_burst_length=128 max_write_burst_length=128
#pragma HLS INTERFACE s_axilite port=meta bundle=control
#pragma HLS INTERFACE s_axilite port=tiled_weight bundle=control
#pragma HLS INTERFACE s_axilite port=canonical_weight bundle=control
#pragma HLS INTERFACE s_axilite port=workspace bundle=control
#pragma HLS INTERFACE s_axilite port=capacity_beats bundle=control
#pragma HLS INTERFACE s_axilite port=debug bundle=control
#pragma HLS INTERFACE s_axilite port=status bundle=control
#pragma HLS INTERFACE s_axilite port=token bundle=control
#pragma HLS INTERFACE s_axilite port=score_bits bundle=control
#pragma HLS INTERFACE s_axilite port=candidate_count bundle=control
#pragma HLS INTERFACE s_axilite port=output_crc bundle=control
#pragma HLS INTERFACE s_axilite port=preview_read_beats bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
    *status=0;*token=0;*score_bits=0;*candidate_count=0;*output_crc=0;*preview_read_beats=0;
    if(capacity_beats<P_WS_BEATS || debug>1) {*status=1;return;}
    float hidden[P_H];unsigned history[4748],dims[P_D];
#pragma HLS ARRAY_PARTITION variable=hidden cyclic factor=8 dim=1
#pragma HLS ARRAY_PARTITION variable=history cyclic factor=4 dim=1
    if(select_channels(meta,hidden,history,dims)) {*status=2;return;}
write_dims:
    for(unsigned word=0;word<16;++word) {
#pragma HLS PIPELINE II=1
        Beat packed=0;
        for(unsigned lane=0;lane<4;++lane) {
#pragma HLS UNROLL
            packed.range(lane*32+31,lane*32)=dims[word*4+lane];
        }
        workspace[P_DIMS+word]=packed;
    }
    if(partial_preview(tiled_weight,hidden,history,dims,workspace)) {*status=2;return;}
    *preview_read_beats=149ull*64*128;
    unsigned count=radix_candidates(workspace);
    if(count<P_T || count>P_T+14) {*status=3;return;}
    ap_uint<32> leaf_status,leaf_count,history_reads,output_writes,crc,best;
    ap_uint<64> index_reads,weight_reads;float score;
    lm_head_v4_candidate(meta,canonical_weight,meta+P_META_HISTORY,workspace+P_TABLE,
        workspace+P_SCORES,1+(count+3)/4,debug?(count+1)/2:0,debug,1,1.1f,
        &leaf_status,&best,&score,&leaf_count,&index_reads,&weight_reads,&history_reads,&output_writes,&crc);
    if(leaf_status!=0) {*status=10+leaf_status;return;}
    *token=best;*score_bits=bits(score);*candidate_count=leaf_count;*output_crc=crc;
}
