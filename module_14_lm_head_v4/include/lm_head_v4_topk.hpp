#ifndef LM_HEAD_V4_TOPK_EXPERIMENT_HPP
#define LM_HEAD_V4_TOPK_EXPERIMENT_HPP
#include "ap_int.h"
// Input: full-V FP32 preview scores AFTER global-history policy.
// Private experiment; this top does not compute the low-rank projection.
enum lmh4_topk_status { LMH4_TOPK_OK=0, LMH4_TOPK_BAD_CONFIG=1, LMH4_TOPK_BAD_ROUTE=2, LMH4_TOPK_NUMERIC=3, LMH4_TOPK_INTERNAL=4 };
extern "C" void lm_head_v4_topk_union(
    const ap_uint<128>* policy_preview,const ap_uint<128>* routed_table,ap_uint<128>* output_table,
    ap_uint<32> score_capacity_beats,ap_uint<32> route_capacity_beats,ap_uint<32> output_capacity_beats,
    ap_uint<32> top_k,ap_uint<32>* status,ap_uint<32>* union_count,
    ap_uint<64>* score_read_beats,ap_uint<32>* route_read_beats,ap_uint<32>* output_write_beats);
#endif
