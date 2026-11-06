#ifndef LM_HEAD_V4_CANDIDATE_EXPERIMENT_HPP
#define LM_HEAD_V4_CANDIDATE_EXPERIMENT_HPP
#include "ap_int.h"
// Private experimental top: no released public ABI or board-image identity.
#define LMH_V2_H_LANES 8
#define LMH_V2_ACC_INTERLEAVE 16
#define LMH_V2_HIDDEN_WORDS 112
#define LMH4_VOCAB 151936
enum lmh4_candidate_status { LMH4_OK=0, LMH4_BAD_CONFIG=1, LMH4_BAD_TABLE=2, LMH4_NUMERIC_ERROR=3 };
extern "C" void lm_head_v4_candidate(
    const ap_uint<128>* hidden,const ap_uint<128>* weight,const ap_uint<128>* history,
    const ap_uint<128>* candidate_table,ap_uint<128>* candidate_scores,
    ap_uint<32> candidate_capacity_beats,ap_uint<32> score_capacity_beats,
    ap_uint<32> write_scores,ap_uint<32> enable_penalty,float penalty,
    ap_uint<32>* status,ap_uint<32>* token,float* score,ap_uint<32>* processed,
    ap_uint<64>* index_read_beats,ap_uint<64>* weight_read_beats,
    ap_uint<32>* history_read_beats,ap_uint<32>* score_write_beats,ap_uint<32>* output_crc);
#endif
