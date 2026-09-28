#include "lm_head_kernel.hpp"

namespace {

bool token_seen(const ap_uint<32> *history_bitmap, int token_id) {
#pragma HLS INLINE
    const int word_index = token_id / LMH_HISTORY_WORD_BITS;
    const int bit_index = token_id % LMH_HISTORY_WORD_BITS;
    const ap_uint<32> word = history_bitmap[word_index];
    return word[bit_index] != 0;
}

float apply_repetition_penalty(
    half raw_logit,
    bool seen,
    bool enabled,
    float penalty) {
#pragma HLS INLINE
    float score = static_cast<float>(raw_logit);
    if (enabled && seen) {
        score = score < 0.0f ? score * penalty : score / penalty;
    }
    return score;
}

}  // namespace

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
    float *selected_score) {
#ifdef LMH_COSIM_SMALL
#pragma HLS INTERFACE m_axi port=hidden offset=slave bundle=gmem_hidden depth=4
#pragma HLS INTERFACE m_axi port=weight offset=slave bundle=gmem_weight depth=16
#pragma HLS INTERFACE m_axi port=history_bitmap offset=slave bundle=gmem_history depth=1
#pragma HLS INTERFACE m_axi port=raw_logits offset=slave bundle=gmem_logits depth=4
#else
#pragma HLS INTERFACE m_axi port=hidden offset=slave bundle=gmem_hidden depth=896
#pragma HLS INTERFACE m_axi port=weight offset=slave bundle=gmem_weight depth=136134656 max_read_burst_length=256 num_read_outstanding=16
#pragma HLS INTERFACE m_axi port=history_bitmap offset=slave bundle=gmem_history depth=4748
#pragma HLS INTERFACE m_axi port=raw_logits offset=slave bundle=gmem_logits depth=151936
#endif
#pragma HLS INTERFACE s_axilite port=hidden bundle=control
#pragma HLS INTERFACE s_axilite port=weight bundle=control
#pragma HLS INTERFACE s_axilite port=history_bitmap bundle=control
#pragma HLS INTERFACE s_axilite port=raw_logits bundle=control
#pragma HLS INTERFACE s_axilite port=hidden_size bundle=control
#pragma HLS INTERFACE s_axilite port=vocab_size bundle=control
#pragma HLS INTERFACE s_axilite port=write_logits bundle=control
#pragma HLS INTERFACE s_axilite port=enable_repetition_penalty bundle=control
#pragma HLS INTERFACE s_axilite port=repetition_penalty bundle=control
#pragma HLS INTERFACE s_axilite port=selected_token bundle=control
#pragma HLS INTERFACE s_axilite port=selected_score bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control

    half hidden_cache[LMH_MAX_HIDDEN_SIZE];
#pragma HLS BIND_STORAGE variable=hidden_cache type=ram_1p impl=bram

load_hidden:
    for (int hidden_index = 0; hidden_index < hidden_size; ++hidden_index) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=896
#pragma HLS PIPELINE II=1
        hidden_cache[hidden_index] = hidden[hidden_index];
    }

    float best_score = 0.0f;
    ap_uint<32> best_token = 0;

vocab_loop:
    for (int token_id = 0; token_id < vocab_size; ++token_id) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=151936
        float accumulator = 0.0f;
        const long long row_offset =
            static_cast<long long>(token_id) * static_cast<long long>(hidden_size);

dot_product:
        for (int hidden_index = 0; hidden_index < hidden_size; ++hidden_index) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=896
            const float activation = static_cast<float>(hidden_cache[hidden_index]);
            const float coefficient =
                static_cast<float>(weight[row_offset + hidden_index]);
            accumulator += activation * coefficient;
        }

        // The architectural LM Head output is FP16. Token selection must happen
        // after this conversion; equal FP16 logits keep the lower token ID.
        const half raw_logit = static_cast<half>(accumulator);
        if (write_logits != 0) {
            raw_logits[token_id] = raw_logit;
        }
        const bool seen = enable_repetition_penalty != 0
                              ? token_seen(history_bitmap, token_id)
                              : false;
        const float policy_score = apply_repetition_penalty(
            raw_logit,
            seen,
            enable_repetition_penalty != 0,
            repetition_penalty);

        if (token_id == 0 || policy_score > best_score) {
            best_score = policy_score;
            best_token = static_cast<ap_uint<32> >(token_id);
        }
    }

    *selected_token = best_token;
    *selected_score = best_score;
}
