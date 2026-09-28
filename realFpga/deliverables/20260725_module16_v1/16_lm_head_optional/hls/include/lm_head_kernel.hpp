#ifndef MODULE16_LM_HEAD_KERNEL_HPP
#define MODULE16_LM_HEAD_KERNEL_HPP

#include "ap_int.h"
#include "hls_half.h"

#ifdef LMH_COSIM_SMALL
// RTL co-simulation checks the same datapath and AXI control protocol with a
// compact interface image.  Vitis HLS otherwise serializes the full 260 MiB
// weight port into a >1 GiB text vector before starting XSIM.
static const int LMH_MAX_HIDDEN_SIZE = 4;
static const int LMH_MAX_VOCAB_SIZE = 4;
#else
static const int LMH_MAX_HIDDEN_SIZE = 896;
static const int LMH_MAX_VOCAB_SIZE = 151936;
#endif
static const int LMH_HISTORY_WORD_BITS = 32;
static const int LMH_HISTORY_WORDS =
    (LMH_MAX_VOCAB_SIZE + LMH_HISTORY_WORD_BITS - 1) / LMH_HISTORY_WORD_BITS;

extern "C" void lm_head_argmax(
    const half *hidden,
    const half *weight,
    const ap_uint<32> *history_bitmap,
    half *raw_logits,
    int hidden_size,
    int vocab_size,
    int write_logits,
    int enable_repetition_penalty,
    float repetition_penalty,
    ap_uint<32> *selected_token,
    float *selected_score);

#endif
