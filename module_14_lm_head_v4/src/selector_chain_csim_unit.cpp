// Test-only unity translation unit for the linked C-chain experiment.
// accepted_numeric_core.hpp is included once so that the identical imported
// definitions are not duplicated across translation units. No numeric edits.
// This is not an integrated hardware top or an exported IP.
#include "lm_head_v4_lowrank.cpp"
#define V ROUTER_V_FOR_UNITY
#include "lm_head_v4_router.cpp"
#undef V
#include "lm_head_v4_topk.cpp"
#include "lm_head_v4_candidate.cpp"
