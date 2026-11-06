#ifndef LM_HEAD_V2_DRIVER_H
#define LM_HEAD_V2_DRIVER_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define LMH_V2_ABI_VERSION 2u
#define LMH_V2_HIDDEN_SIZE 896u
#define LMH_V2_VOCAB_SIZE 151936u
#define LMH_V2_HIDDEN_BYTES 1792u
#define LMH_V2_WEIGHT_BYTES 272269312u
#define LMH_V2_HISTORY_BYTES 18992u
#define LMH_V2_LOGITS_BYTES 607744u
#define LMH_V2_BUFFER_ALIGNMENT 64u
#define LMH_V2_BUILD_CONFIG 0x20c08011u

enum lmh_v2_driver_status {
    LMH_DRV_OK = 0,
    LMH_DRV_BAD_ABI = 1,
    LMH_DRV_BAD_DIMENSION = 2,
    LMH_DRV_BAD_ALIGNMENT = 3,
    LMH_DRV_BAD_ADDRESS_RANGE = 4,
    LMH_DRV_BAD_LAYOUT = 5,
    LMH_DRV_BAD_LAYER = 6,
    LMH_DRV_BAD_TOKEN = 7,
    LMH_DRV_BAD_ALIAS = 8,
    LMH_DRV_NUMERIC_ERROR = 9,
    LMH_DRV_TIMEOUT = 10,
    LMH_DRV_BAD_FLAGS = 11,
    LMH_DRV_INTERNAL_ERROR = 12,
    LMH_DRV_NOT_READY = 13
};

struct lmh_v2_job {
    uint64_t hidden_phys_addr;
    uint64_t weight_phys_addr;
    uint64_t history_phys_addr;
    uint64_t logits_phys_addr;
    uint32_t hidden_size;
    uint32_t vocab_size;
    uint32_t run_mode;
    uint32_t valid_rows;
    uint32_t write_logits;
    uint32_t enable_penalty;
    float repetition_penalty;
    uint32_t abi_version;
    uint32_t job_id;
    uint32_t flags;
};

struct lmh_v2_result {
    uint32_t selected_token;
    float selected_score;
    uint32_t result_job_id;
    uint32_t status_code;
    uint32_t processed_rows;
    uint64_t perf_cycles_total;
    uint64_t perf_cycles_compute;
    uint64_t perf_read_beats;
    uint64_t perf_write_beats;
    uint32_t output_crc;
    uint32_t build_config;
    uint32_t capabilities;
    uint32_t vocab_rows_done;
    uint64_t weight_read_beats_128;
    uint32_t history_read_words;
    uint64_t logits_write_beats_128;
    uint64_t weight_wait_cycles;
    uint64_t dot_active_cycles;
    uint32_t logits_written;
};

/*
 * Register offsets are deliberately not duplicated here.  After HLS export,
 * the generated xlm_head_v2_hw.h is the register-offset source of truth.
 * The integration wrapper maps that generated header into these logical job
 * and result structures.
 */
int lmh_v2_validate_job(const struct lmh_v2_job *job);

#ifdef __cplusplus
}
#endif

#endif
