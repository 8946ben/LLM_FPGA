#include "lm_head_v2_mmio.h"

#include <stddef.h>
#include <string.h>

static uint32_t float_to_bits(float value) {
    uint32_t bits;
    memcpy(&bits, &value, sizeof(bits));
    return bits;
}

static float bits_to_float(uint32_t bits) {
    float value;
    memcpy(&value, &bits, sizeof(value));
    return value;
}

static int submit_impl(XLm_head_v2 *instance,
                       const struct lmh_v2_job *job,
                       int validate) {
    int status;
    if (job == NULL) {
        return LMH_DRV_INTERNAL_ERROR;
    }
    if (validate != 0) {
        status = lmh_v2_validate_job(job);
        if (status != LMH_DRV_OK) {
            return status;
        }
    }
    if (instance == NULL || instance->IsReady != XIL_COMPONENT_IS_READY) {
        return LMH_DRV_INTERNAL_ERROR;
    }
    if (!XLm_head_v2_IsReady(instance)) {
        return LMH_DRV_NOT_READY;
    }

    /* Program all 64-bit addresses before scalar controls and ap_start. */
    XLm_head_v2_Set_hidden_offset(instance, job->hidden_phys_addr);
    XLm_head_v2_Set_shared_vocab_weight(instance, job->weight_phys_addr);
    XLm_head_v2_Set_history_bitmap(instance, job->history_phys_addr);
    XLm_head_v2_Set_optional_logits(instance, job->logits_phys_addr);
    XLm_head_v2_Set_hidden_size_r(instance, job->hidden_size);
    XLm_head_v2_Set_vocab_size(instance, job->vocab_size);
    XLm_head_v2_Set_run_mode(instance, job->run_mode);
    XLm_head_v2_Set_valid_rows(instance, job->valid_rows);
    XLm_head_v2_Set_write_logits(instance, job->write_logits);
    XLm_head_v2_Set_enable_penalty(instance, job->enable_penalty);
    XLm_head_v2_Set_repetition_penalty(
        instance, float_to_bits(job->repetition_penalty));
    XLm_head_v2_Set_abi_version(instance, job->abi_version);
    XLm_head_v2_Set_job_id(instance, job->job_id);
    XLm_head_v2_Set_flags(instance, job->flags);

    XLm_head_v2_Start(instance);
    return LMH_DRV_OK;
}

int lmh_v2_submit(XLm_head_v2 *instance, const struct lmh_v2_job *job) {
    return submit_impl(instance, job, 1);
}

int lmh_v2_submit_unchecked(XLm_head_v2 *instance,
                            const struct lmh_v2_job *job) {
    return submit_impl(instance, job, 0);
}

int lmh_v2_wait(XLm_head_v2 *instance, uint64_t poll_budget) {
    if (instance == NULL || instance->IsReady != XIL_COMPONENT_IS_READY) {
        return LMH_DRV_INTERNAL_ERROR;
    }
    while (poll_budget != 0u) {
        if (XLm_head_v2_IsDone(instance)) {
            return LMH_DRV_OK;
        }
        --poll_budget;
    }
    return LMH_DRV_TIMEOUT;
}

int lmh_v2_read_result(XLm_head_v2 *instance, struct lmh_v2_result *result) {
    if (instance == NULL || result == NULL ||
        instance->IsReady != XIL_COMPONENT_IS_READY) {
        return LMH_DRV_INTERNAL_ERROR;
    }

    result->selected_token = XLm_head_v2_Get_selected_token(instance);
    result->selected_score =
        bits_to_float(XLm_head_v2_Get_selected_score(instance));
    result->result_job_id = XLm_head_v2_Get_result_job_id(instance);
    result->status_code = XLm_head_v2_Get_status_code(instance);
    result->processed_rows = XLm_head_v2_Get_processed_rows(instance);
    result->perf_cycles_total = XLm_head_v2_Get_perf_cycles_total(instance);
    result->perf_cycles_compute =
        XLm_head_v2_Get_perf_cycles_compute(instance);
    result->perf_read_beats = XLm_head_v2_Get_perf_read_beats(instance);
    result->perf_write_beats = XLm_head_v2_Get_perf_write_beats(instance);
    result->output_crc = XLm_head_v2_Get_output_crc(instance);
    result->build_config = XLm_head_v2_Get_build_config(instance);
    result->capabilities = XLm_head_v2_Get_capabilities(instance);
    result->vocab_rows_done = XLm_head_v2_Get_vocab_rows_done(instance);
    result->weight_read_beats_128 =
        XLm_head_v2_Get_weight_read_beats_128(instance);
    result->history_read_words =
        XLm_head_v2_Get_history_read_words(instance);
    result->logits_write_beats_128 =
        XLm_head_v2_Get_logits_write_beats_128(instance);
    result->weight_wait_cycles =
        XLm_head_v2_Get_weight_wait_cycles(instance);
    result->dot_active_cycles = XLm_head_v2_Get_dot_active_cycles(instance);
    result->logits_written = XLm_head_v2_Get_logits_written(instance);
    return LMH_DRV_OK;
}

int lmh_v2_verify_result(const struct lmh_v2_job *job,
                         const struct lmh_v2_result *result) {
    if (job == NULL || result == NULL) {
        return LMH_DRV_INTERNAL_ERROR;
    }
    if (result->status_code != LMH_DRV_OK) {
        return (int)result->status_code;
    }
    if (result->result_job_id != job->job_id) {
        return LMH_DRV_BAD_LAYOUT;
    }
    if (result->build_config != LMH_V2_BUILD_CONFIG ||
        result->capabilities != LMH_V2_CAPABILITIES) {
        return LMH_DRV_BAD_ABI;
    }
    if (result->processed_rows != 1u ||
        result->vocab_rows_done != LMH_V2_VOCAB_SIZE ||
        result->weight_read_beats_128 != 17016832u) {
        return LMH_DRV_BAD_DIMENSION;
    }
    if (job->write_logits == 0u &&
        (result->logits_written != 0u ||
         result->logits_write_beats_128 != 0u)) {
        return LMH_DRV_BAD_FLAGS;
    }
    return LMH_DRV_OK;
}
