#ifndef LMH4_ROUTER_HPP
#define LMH4_ROUTER_HPP
#include "ap_int.h"
enum lmh4_router_status { LMH4_ROUTE_OK=0,LMH4_ROUTE_BAD_CONFIG=1,LMH4_ROUTE_NUMERIC=2,LMH4_ROUTE_BAD_TABLE=3 };
// Fixed 128 BF16 centers, nearest4 L2, max16384 IDs/list; full global IDs.
// Norms are frozen FP32 sum(center*center), not learned extra parameters.
extern "C" void lm_head_v4_router(
    const ap_uint<128>* hidden,const ap_uint<128>* centers,const ap_uint<128>* norms,
    const ap_uint<128>* ranked_ids,const ap_uint<128>* counts,ap_uint<128>* routed_table,
    ap_uint<32> hidden_capacity,ap_uint<32> center_capacity,ap_uint<32> norm_capacity,
    ap_uint<32> ranked_capacity,ap_uint<32> count_capacity,ap_uint<32> output_capacity,
    ap_uint<32>* status,ap_uint<128>* selected_routes,ap_uint<32>* candidate_count,
    ap_uint<32>* dense_fallback,ap_uint<32>* matrix_read_beats,ap_uint<32>* list_read_beats,
    ap_uint<32>* output_write_beats);
#endif
