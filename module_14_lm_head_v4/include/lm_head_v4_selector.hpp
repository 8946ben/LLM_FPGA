#ifndef LMH4_SELECTOR_HPP
#define LMH4_SELECTOR_HPP
#include "ap_int.h"
// Private integrated experiment, NOT the released M14 public ABI.
// Descriptor: 16B header,16B config,13*(uint64 offset,uint64 capacity).
// All offsets/capacities are bytes relative to the single PL DDR arena.
enum lmh4_selector_region {
    SEL_WEIGHT=0,SEL_HIDDEN=1,SEL_HISTORY=2,SEL_A=3,SEL_BT=4,
    SEL_CENTERS=5,SEL_NORMS=6,SEL_RANKED=7,SEL_COUNTS=8,
    SEL_PREVIEW=9,SEL_ROUTED=10,SEL_MERGED=11,SEL_SPARSE=12,SEL_REGIONS=13
};
enum lmh4_selector_status {
    SEL_OK=0,SEL_BAD_DESCRIPTOR=1,SEL_BAD_REGION=2,SEL_OVERLAP=3,
    SEL_BAD_CONFIG=4,SEL_CHILD_FAILED=5,SEL_FALLBACK_FORBIDDEN=6
};
enum lmh4_selector_stage {SEL_PREFLIGHT=1,SEL_ROUTE_STAGE=2,SEL_LOWRANK_STAGE=3,SEL_TOPK_STAGE=4,SEL_EXACT_STAGE=5,SEL_DONE=6};
enum lmh4_selector_command {SEL_RUN=0,SEL_VALIDATE_ONLY=1};
extern "C" void lm_head_v4_selector(
    ap_uint<128>* pl_ddr,const ap_uint<128>* history_bitmap,ap_uint<64> arena_bytes,ap_uint<64> descriptor_offset,ap_uint<32> command,
    ap_uint<32>* status,ap_uint<32>* stage,ap_uint<32>* child_status,
    ap_uint<32>* route_count,ap_uint<32>* candidate_count,ap_uint<32>* dense_fallback,
    ap_uint<32>* token,float* score,ap_uint<32>* output_crc);
#endif
