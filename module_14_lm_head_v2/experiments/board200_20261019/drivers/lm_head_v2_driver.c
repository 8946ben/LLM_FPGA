#include "lm_head_v2_driver.h"

#include <math.h>
#include <stddef.h>

static int aligned_64(uint64_t address) {
    return (address & (LMH_V2_BUFFER_ALIGNMENT - 1u)) == 0u;
}

int lmh_v2_validate_job(const struct lmh_v2_job *job) {
    if (job == NULL) {
        return LMH_DRV_INTERNAL_ERROR;
    }
    if (job->abi_version != LMH_V2_ABI_VERSION) {
        return LMH_DRV_BAD_ABI;
    }
    if (job->hidden_size != LMH_V2_HIDDEN_SIZE ||
        job->vocab_size != LMH_V2_VOCAB_SIZE ||
        job->valid_rows != 1u ||
        job->run_mode > 1u ||
        job->write_logits > 1u ||
        job->enable_penalty > 1u) {
        return LMH_DRV_BAD_DIMENSION;
    }
    if ((job->flags & ~0x0fu) != 0u) {
        return LMH_DRV_BAD_FLAGS;
    }
    if (job->hidden_phys_addr == 0u || job->weight_phys_addr == 0u ||
        (job->enable_penalty && job->history_phys_addr == 0u) ||
        (job->write_logits && job->logits_phys_addr == 0u)) {
        return LMH_DRV_BAD_ADDRESS_RANGE;
    }
    if (!aligned_64(job->hidden_phys_addr) ||
        !aligned_64(job->weight_phys_addr) ||
        (job->enable_penalty && !aligned_64(job->history_phys_addr)) ||
        (job->write_logits && !aligned_64(job->logits_phys_addr))) {
        return LMH_DRV_BAD_ALIGNMENT;
    }
    if (job->enable_penalty &&
        (!isfinite(job->repetition_penalty) ||
         job->repetition_penalty < 1.0f)) {
        return LMH_DRV_NUMERIC_ERROR;
    }
    return LMH_DRV_OK;
}
