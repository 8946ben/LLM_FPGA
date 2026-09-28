#ifndef LMH_BUFFERS_H
#define LMH_BUFFERS_H

#include "xil_types.h"

/*
 * 2026-07-24 zb: Shared PS-DDR layout for the Module 16 network server and
 * lm_head_argmax HLS IP.  Storage is reserved by lscript.ld as NOLOAD.
 */
#define LMH_HIDDEN_SIZE         896U
#define LMH_VOCAB_SIZE          151936U
#define LMH_HISTORY_WORDS       4748U
#define LMH_WEIGHT_BYTES        272269312U
#define LMH_HIDDEN_BYTES        1792U
#define LMH_HISTORY_BYTES       18992U
#define LMH_LOGITS_BYTES        303872U
#define LMH_NETWORK_RX_BYTES    1048576U
#define LMH_BUFFER_ALIGNMENT    64U

extern u8 __lmh_buffers_start[];
extern u8 __lmh_weight_start[];
extern u8 __lmh_weight_end[];
extern u8 __lmh_hidden_start[];
extern u8 __lmh_hidden_end[];
extern u8 __lmh_history_start[];
extern u8 __lmh_history_end[];
extern u8 __lmh_logits_start[];
extern u8 __lmh_logits_end[];
extern u8 __lmh_network_rx_start[];
extern u8 __lmh_network_rx_end[];
extern u8 __lmh_buffers_end[];

#define LMH_WEIGHT_ADDR      ((UINTPTR)__lmh_weight_start)
#define LMH_HIDDEN_ADDR      ((UINTPTR)__lmh_hidden_start)
#define LMH_HISTORY_ADDR     ((UINTPTR)__lmh_history_start)
#define LMH_LOGITS_ADDR      ((UINTPTR)__lmh_logits_start)
#define LMH_NETWORK_RX_ADDR  ((UINTPTR)__lmh_network_rx_start)

#endif
