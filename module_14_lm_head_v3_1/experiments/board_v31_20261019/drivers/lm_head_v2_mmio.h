#ifndef LM_HEAD_V2_MMIO_H
#define LM_HEAD_V2_MMIO_H

#include <stdint.h>

#include "lm_head_v2_driver.h"
#include "xlm_head_v2.h"

#ifdef __cplusplus
extern "C" {
#endif

/*
 * These routines intentionally use the Vitis HLS generated accessors.  The
 * generated xlm_head_v2_hw.h remains the single source of register offsets.
 */
int lmh_v2_submit(XLm_head_v2 *instance, const struct lmh_v2_job *job);
int lmh_v2_submit_unchecked(XLm_head_v2 *instance,
                            const struct lmh_v2_job *job);
int lmh_v2_wait(XLm_head_v2 *instance, uint64_t poll_budget);
int lmh_v2_read_result(XLm_head_v2 *instance, struct lmh_v2_result *result);
int lmh_v2_verify_result(const struct lmh_v2_job *job,
                         const struct lmh_v2_result *result);

#ifdef __cplusplus
}
#endif

#endif
