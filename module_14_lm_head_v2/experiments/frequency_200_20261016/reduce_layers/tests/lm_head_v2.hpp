#ifndef MODULE_14_LM_HEAD_V2_HPP
#define MODULE_14_LM_HEAD_V2_HPP

#include "ap_int.h"

#if defined(LMH_V2_TEST_FULL_HIDDEN)
#define LMH_V2_MAX_HIDDEN_SIZE 896
#define LMH_V2_MAX_VOCAB_SIZE 64
#elif defined(LMH_V2_TEST_SMALL)
#define LMH_V2_MAX_HIDDEN_SIZE 32
#define LMH_V2_MAX_VOCAB_SIZE 64
#else
#define LMH_V2_MAX_HIDDEN_SIZE 896
#define LMH_V2_MAX_VOCAB_SIZE 151936
#endif

#define LMH_V2_BF16_PER_BEAT 8
#define LMH_V2_FP32_PER_BEAT 4
#define LMH_V2_HIDDEN_WORDS \
    (LMH_V2_MAX_HIDDEN_SIZE / LMH_V2_BF16_PER_BEAT)
#define LMH_V2_WEIGHT_WORDS \
    (LMH_V2_MAX_VOCAB_SIZE * LMH_V2_HIDDEN_WORDS)
#define LMH_V2_HISTORY_BEATS \
    ((LMH_V2_MAX_VOCAB_SIZE + 127) / 128)
#define LMH_V2_LOGIT_BEATS \
    ((LMH_V2_MAX_VOCAB_SIZE + LMH_V2_FP32_PER_BEAT - 1) / \
     LMH_V2_FP32_PER_BEAT)

static const unsigned int LMH_V2_ABI_VERSION = 2;
static const unsigned int LMH_V2_H_LANES = 8;
static const unsigned int LMH_V2_ACC_INTERLEAVE = 16;
static const unsigned int LMH_V2_WEIGHT_FIFO_DEPTH = 128;

enum lmh_v2_run_mode {
    LMH_V2_RUN_PREFILL = 0,
    LMH_V2_RUN_DECODE = 1
};

enum lmh_v2_status_code {
    LMH_V2_OK = 0,
    LMH_V2_BAD_ABI = 1,
    LMH_V2_BAD_DIMENSION = 2,
    LMH_V2_BAD_ALIGNMENT = 3,
    LMH_V2_BAD_ADDRESS_RANGE = 4,
    LMH_V2_BAD_LAYOUT = 5,
    LMH_V2_BAD_LAYER = 6,
    LMH_V2_BAD_TOKEN = 7,
    LMH_V2_BAD_ALIAS = 8,
    LMH_V2_NUMERIC_ERROR = 9,
    LMH_V2_DRIVER_TIMEOUT = 10,
    LMH_V2_BAD_FLAGS = 11,
    LMH_V2_INTERNAL_ERROR = 12
};

enum lmh_v2_common_flags {
    LMH_V2_FLAG_ENABLE_OUTPUT_CRC = 1u << 0,
    LMH_V2_FLAG_ENABLE_PERF = 1u << 1,
    LMH_V2_FLAG_DEBUG_SNAPSHOT = 1u << 2,
    LMH_V2_FLAG_STRICT_CHECK = 1u << 3,
    LMH_V2_VALID_FLAGS = 0x0fu
};

enum lmh_v2_capabilities {
    LMH_V2_CAP_DEBUG_CRC = 1u << 1,
    LMH_V2_CAP_WRITE_LOGITS_OPTIONAL = 1u << 7,
    LMH_V2_CAP_DUAL_RUN_MODE = 1u << 8
};

// ABI V2 build_config:
// lanes=8, row_tile=1, hidden_tile=32, numeric_impl=0,
// clock=100 MHz, module_revision=1.
static const unsigned int LMH_V2_BUILD_CONFIG = 0x10008011u;
static const unsigned int LMH_V2_CAPABILITIES =
    LMH_V2_CAP_DEBUG_CRC |
    LMH_V2_CAP_WRITE_LOGITS_OPTIONAL |
    LMH_V2_CAP_DUAL_RUN_MODE;

extern "C" void lm_head_v2(
    const ap_uint<128> *hidden,
    const ap_uint<128> *shared_vocab_weight,
    const ap_uint<128> *history_bitmap,
    ap_uint<128> *optional_logits,
    ap_uint<32> hidden_size,
    ap_uint<32> vocab_size,
    ap_uint<32> run_mode,
    ap_uint<32> valid_rows,
    ap_uint<32> write_logits,
    ap_uint<32> enable_penalty,
    float repetition_penalty,
    ap_uint<32> abi_version,
    ap_uint<32> job_id,
    ap_uint<32> flags,
    ap_uint<32> *selected_token,
    float *selected_score,
    ap_uint<32> *result_job_id,
    ap_uint<32> *status_code,
    ap_uint<32> *processed_rows,
    ap_uint<64> *perf_cycles_total,
    ap_uint<64> *perf_cycles_compute,
    ap_uint<64> *perf_read_beats,
    ap_uint<64> *perf_write_beats,
    ap_uint<32> *output_crc,
    ap_uint<32> *build_config,
    ap_uint<32> *capabilities,
    ap_uint<32> *vocab_rows_done,
    ap_uint<64> *weight_read_beats_128,
    ap_uint<32> *history_read_words,
    ap_uint<64> *logits_write_beats_128,
    ap_uint<64> *weight_wait_cycles,
    ap_uint<64> *dot_active_cycles,
    ap_uint<32> *logits_written);

#endif
