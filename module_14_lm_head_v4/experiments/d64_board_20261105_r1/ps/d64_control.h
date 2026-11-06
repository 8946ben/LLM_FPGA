#ifndef D64_CONTROL_H
#define D64_CONTROL_H
#include <stdint.h>
#include "d64_layout.h"
typedef struct {void *ctx;uint32_t(*read32)(void*,uint64_t);void(*write32)(void*,uint64_t,uint32_t);void(*barrier)(void*);uint64_t(*now_us)(void*);} d64_io;
typedef struct {uint32_t capacity_beats,debug;int weights_verified;} d64_request;
typedef struct {uint32_t status,token,score_bits,k,crc,valid_mask;uint64_t preview_beats,wait_us;int launched,may_still_be_running,token_valid;} d64_result;
enum {D64_OK=0,D64_ARGUMENT=-1,D64_WRONG_IMAGE=-2,D64_NO_CALIBRATION=-3,D64_NOT_VERIFIED=-4,D64_BUSY=-5,D64_READBACK=-6,D64_TIMEOUT=-7,D64_VALID_MISSING=-8,D64_BAD_RESULT=-9};
/* Fixed PL addresses above4GiB. capacity/debug intentionally reach hardware
 * unchanged so the acceptance campaign can test actual IP error returns.
 * OK means one completed transport/control call; result.status is the IP status.
 * No automatic restart/reset after timeout. wait_us is polling only; time the
 * entire call externally for token-ready A53 latency. No IP cycle counter. */
int d64_call(const d64_io*,const d64_request*,uint64_t timeout_us,d64_result*);
uint32_t d64_token_crc(uint32_t token,uint32_t bits);
#endif
