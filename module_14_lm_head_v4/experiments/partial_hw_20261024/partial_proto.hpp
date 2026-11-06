#ifndef LMH4_PARTIAL_PROTO_20261024_HPP
#define LMH4_PARTIAL_PROTO_20261024_HPP
#include "ap_int.h"
enum { P_V=151936,P_H=896,P_D=64,P_T=4096,P_B=1024,P_TILES=149,P_META_HISTORY=336,
       P_META_BEATS=1523,P_KEY=0,P_PREVIEW=37984,P_TABLE=75968,P_SCORES=76997,P_DIMS=79052,P_WS_BEATS=79068 };
// Experimental Csim/HLS only. No descriptor, deployed IP identity or board ABI.
extern "C" void lm_head_v4_partial_proto(const ap_uint<128>* meta,
    const ap_uint<128>* tiled_weight,const ap_uint<128>* canonical_weight,
    ap_uint<128>* workspace,unsigned capacity_beats,unsigned debug,
    ap_uint<32>* status,ap_uint<32>* token,ap_uint<32>* score_bits,
    ap_uint<32>* candidate_count,ap_uint<32>* output_crc,ap_uint<64>* preview_read_beats);
#endif
