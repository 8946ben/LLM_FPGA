#include "lm_head_v2_driver.h"
#include <assert.h>
#include <stdio.h>

int main(void) {
    struct lmh_v2_job job = {0};
    job.hidden_phys_addr = 0x4104a8000ull;
    job.weight_phys_addr = 0x400100000ull;
    job.history_phys_addr = 0x4104a8700ull;
    job.logits_phys_addr = 0x4104ad140ull;
    job.hidden_size = LMH_V2_HIDDEN_SIZE;
    job.vocab_size = LMH_V2_VOCAB_SIZE;
    job.valid_rows = 1u;
    job.write_logits = 1u;
    job.enable_penalty = 1u;
    job.repetition_penalty = 1.1f;
    job.abi_version = LMH_V2_ABI_VERSION;
    assert(lmh_v2_validate_job(&job) == LMH_DRV_OK);
    job.weight_phys_addr = 0x00100000ull; /* Legacy local offset must not pass. */
    assert(lmh_v2_validate_job(&job) == LMH_DRV_BAD_ADDRESS_RANGE);
    job.weight_phys_addr = LMH_V31_DDR_SYSTEM_BASE + LMH_V31_DDR_BYTES - LMH_V2_WEIGHT_BYTES;
    assert(lmh_v2_validate_job(&job) == LMH_DRV_OK); /* Exact end is legal. */
    job.weight_phys_addr += 64u;
    assert(lmh_v2_validate_job(&job) == LMH_DRV_BAD_ADDRESS_RANGE);
    job.weight_phys_addr = 0xffffffffffffffc0ull;
    assert(lmh_v2_validate_job(&job) == LMH_DRV_BAD_ADDRESS_RANGE);
    job.weight_phys_addr = 0x400100000ull;
    job.logits_phys_addr = LMH_V31_DDR_SYSTEM_BASE + LMH_V31_DDR_BYTES;
    assert(lmh_v2_validate_job(&job) == LMH_DRV_BAD_ADDRESS_RANGE);
    job.write_logits = 0u;
    assert(lmh_v2_validate_job(&job) == LMH_DRV_OK); /* Inactive output ignored. */
    puts("M14_V31_DRIVER_ADDRESS_BOUNDARIES=PASS");
    return 0;
}
