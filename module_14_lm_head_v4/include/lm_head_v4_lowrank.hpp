#ifndef LMH4_LOWRANK_HPP
#define LMH4_LOWRANK_HPP
#include "ap_int.h"
enum lmh4_lowrank_status { LMH4_LR_OK=0, LMH4_LR_BAD_CONFIG=1, LMH4_LR_NUMERIC=2 };
// Private experiment. B is losslessly transposed to [128][896] BF16;
// A stays [151936][128] BF16. Output is already penalty-adjusted FP32.
extern "C" void lm_head_v4_lowrank(
    const ap_uint<128>* hidden,const ap_uint<128>* b_transposed,
    const ap_uint<128>* a_factor,const ap_uint<128>* history,
    ap_uint<128>* policy_preview,
    ap_uint<32> rows,ap_uint<32> hidden_capacity,ap_uint<32> b_capacity,
    ap_uint<32> a_capacity,ap_uint<32> history_capacity,ap_uint<32> output_capacity,
    ap_uint<32> enable_penalty,float penalty,ap_uint<32>* status,
    ap_uint<64>* factor_read_beats,ap_uint<32>* output_write_beats);
#endif
