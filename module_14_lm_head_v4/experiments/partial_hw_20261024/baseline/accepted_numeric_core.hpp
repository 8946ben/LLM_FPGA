#ifndef LMH4_ACCEPTED_NUMERIC_CORE_HPP
#define LMH4_ACCEPTED_NUMERIC_CORE_HPP
#include "lm_head_v4_candidate.hpp"
#include "hls_stream.h"
namespace lmh4_detail {


union uint_float_bits {
    unsigned int u;
    float f;
};

float bf16_to_float(ap_uint<16> value) {
#pragma HLS INLINE
    uint_float_bits converted;
    converted.u = value.to_uint() << 16;
    return converted.f;
}

ap_uint<32> float_to_bits(float value) {
#pragma HLS INLINE
    uint_float_bits converted;
    converted.f = value;
    return converted.u;
}

float bits_to_float(unsigned int value) {
#pragma HLS INLINE
    uint_float_bits converted;
    converted.u = value;
    return converted.f;
}

bool finite_float(float value) {
#pragma HLS INLINE
    const ap_uint<32> bits = float_to_bits(value);
    return bits.range(30, 23) != 0xffu;
}

ap_uint<32> crc32_token_score(
    ap_uint<32> token,
    ap_uint<32> score_bits) {
    ap_uint<64> payload = 0;
    payload.range(31, 0) = token;
    payload.range(63, 32) = score_bits;
    ap_uint<32> crc = 0xffffffffu;

crc_byte_loop:
    for (int byte_index = 0; byte_index < 8; ++byte_index) {
        ap_uint<8> byte_value = payload.range(
            byte_index * 8 + 7,
            byte_index * 8);
    crc_bit_loop:
        for (int bit_index = 0; bit_index < 8; ++bit_index) {
#pragma HLS PIPELINE II=1
            const bool mix = (crc[0] ^ byte_value[bit_index]) != 0;
            crc >>= 1;
            if (mix) {
                crc ^= 0xedb88320u;
            }
        }
    }
    return crc ^ 0xffffffffu;
}

void load_hidden(
    const ap_uint<128> *hidden,
    float hidden_cache[LMH_V2_H_LANES][LMH_V2_HIDDEN_WORDS]) {
load_hidden_word:
    for (int word = 0; word < LMH_V2_HIDDEN_WORDS; ++word) {
#pragma HLS PIPELINE II=1
        const ap_uint<128> packed = hidden[word];
    unpack_hidden_lane:
        for (int lane = 0; lane < LMH_V2_H_LANES; ++lane) {
#pragma HLS UNROLL
            const ap_uint<16> value = packed.range(
                lane * 16 + 15,
                lane * 16);
            hidden_cache[lane][word] = bf16_to_float(value);
        }
    }
}

void read_weight_stream(
    const ap_uint<128> *weight,
    ap_uint<32> total_words,
    hls::stream<ap_uint<128> > &weight_fifo,
    hls::stream<ap_uint<1> > &done) {
read_weight_word:
    for (ap_uint<32> index = 0; index < total_words; ++index) {
#pragma HLS PIPELINE II=1
#pragma HLS LOOP_TRIPCOUNT min=256 max=17016832
        weight_fifo.write(weight[index]);
    }
    done.write(1);
}

float reduce_partials(
    const float partial[LMH_V2_H_LANES][LMH_V2_ACC_INTERLEAVE]) {
#pragma HLS INLINE off
    // Each level has a distinct destination: no in-place indexed writeback.
    // Preserve the original slot pairing and every FP32 rounding boundary.
    float level8[LMH_V2_H_LANES][8];
    float level4[LMH_V2_H_LANES][4];
    float level2[LMH_V2_H_LANES][2];
#pragma HLS ARRAY_PARTITION variable=level8 complete dim=0
#pragma HLS ARRAY_PARTITION variable=level4 complete dim=0
#pragma HLS ARRAY_PARTITION variable=level2 complete dim=0

reduce_16_to_8:
    for (int index = 0; index < 8; ++index) {
#pragma HLS PIPELINE II=1
    reduce_16_to_8_lane:
        for (int lane = 0; lane < LMH_V2_H_LANES; ++lane) {
#pragma HLS UNROLL
            level8[lane][index] =
                partial[lane][index] + partial[lane][index + 8];
        }
    }

reduce_8_to_4:
    for (int index = 0; index < 4; ++index) {
#pragma HLS PIPELINE II=1
    reduce_8_to_4_lane:
        for (int lane = 0; lane < LMH_V2_H_LANES; ++lane) {
#pragma HLS UNROLL
            level4[lane][index] =
                level8[lane][index] + level8[lane][index + 4];
        }
    }

reduce_4_to_2:
    for (int index = 0; index < 2; ++index) {
#pragma HLS PIPELINE II=1
    reduce_4_to_2_lane:
        for (int lane = 0; lane < LMH_V2_H_LANES; ++lane) {
#pragma HLS UNROLL
            level2[lane][index] =
                level4[lane][index] + level4[lane][index + 2];
        }
    }

    float lane_sum[LMH_V2_H_LANES];
#pragma HLS ARRAY_PARTITION variable=lane_sum complete dim=1
reduce_2_to_1:
    for (int lane = 0; lane < LMH_V2_H_LANES; ++lane) {
#pragma HLS UNROLL
        lane_sum[lane] = level2[lane][0] + level2[lane][1];
    }

    const float sum01 = lane_sum[0] + lane_sum[1];
    const float sum23 = lane_sum[2] + lane_sum[3];
    const float sum45 = lane_sum[4] + lane_sum[5];
    const float sum67 = lane_sum[6] + lane_sum[7];
    const float sum03 = sum01 + sum23;
    const float sum47 = sum45 + sum67;
    return sum03 + sum47;
}

// One FIFO word carries the same interleave slot from all eight lanes.  A
// depth of 32 stores two complete 16-slot accumulator contexts, so the dot
// stage can start the next vocabulary row while the reduction stage consumes
// the previous one without creating a 4096-bit-wide internal bus.
typedef ap_uint<256> accumulator_slice_t;

void dot_product_rows(
    hls::stream<ap_uint<128> > &weight_fifo,
    const float hidden_cache[LMH_V2_H_LANES][LMH_V2_HIDDEN_WORDS],
    ap_uint<32> vocab_size,
    hls::stream<accumulator_slice_t> &context_fifo) {
    float partial[LMH_V2_H_LANES][LMH_V2_ACC_INTERLEAVE];
#pragma HLS ARRAY_PARTITION variable=partial complete dim=1

dot_vocab_loop:
    for (ap_uint<32> token = 0; token < vocab_size; ++token) {
#pragma HLS LOOP_TRIPCOUNT min=64 max=151936
    clear_partial_lane:
        for (int lane = 0; lane < LMH_V2_H_LANES; ++lane) {
#pragma HLS UNROLL
        clear_partial_slot:
            for (int slot = 0; slot < LMH_V2_ACC_INTERLEAVE; ++slot) {
#pragma HLS UNROLL
                partial[lane][slot] = 0.0f;
            }
        }

    dot_word_loop:
        for (int word = 0; word < LMH_V2_HIDDEN_WORDS; ++word) {
#pragma HLS PIPELINE II=1
#pragma HLS DEPENDENCE variable=partial inter RAW distance=16 true
            const ap_uint<128> packed_weight = weight_fifo.read();
            const int slot = word & (LMH_V2_ACC_INTERLEAVE - 1);
        dot_lane_loop:
            for (int lane = 0; lane < LMH_V2_H_LANES; ++lane) {
#pragma HLS UNROLL
                const ap_uint<16> weight_bits = packed_weight.range(
                    lane * 16 + 15,
                    lane * 16);
                const float coefficient = bf16_to_float(weight_bits);
                const float product = hidden_cache[lane][word] * coefficient;
                partial[lane][slot] = partial[lane][slot] + product;
            }
        }

    emit_context_slot:
        for (int slot = 0; slot < LMH_V2_ACC_INTERLEAVE; ++slot) {
#pragma HLS PIPELINE II=1
            accumulator_slice_t context_slice = 0;
        pack_context_lane:
            for (int lane = 0; lane < LMH_V2_H_LANES; ++lane) {
#pragma HLS UNROLL
                context_slice.range(lane * 32 + 31, lane * 32) =
                    float_to_bits(partial[lane][slot]);
            }
            context_fifo.write(context_slice);
        }
    }
}

void reduce_rows(
    hls::stream<accumulator_slice_t> &context_fifo,
    hls::stream<float> &raw_score_fifo,
    ap_uint<32> vocab_size) {
    float partial[LMH_V2_H_LANES][LMH_V2_ACC_INTERLEAVE];
#pragma HLS ARRAY_PARTITION variable=partial complete dim=0

reduce_vocab_loop:
    for (ap_uint<32> token = 0; token < vocab_size; ++token) {
#pragma HLS LOOP_TRIPCOUNT min=64 max=151936
    read_context_slot:
        for (int slot = 0; slot < LMH_V2_ACC_INTERLEAVE; ++slot) {
#pragma HLS PIPELINE II=1
            const accumulator_slice_t context_slice = context_fifo.read();
        unpack_context_lane:
            for (int lane = 0; lane < LMH_V2_H_LANES; ++lane) {
#pragma HLS UNROLL
                const ap_uint<32> bits = context_slice.range(
                    lane * 32 + 31,
                    lane * 32);
                partial[lane][slot] = bits_to_float(bits.to_uint());
            }
        }
        raw_score_fifo.write(reduce_partials(partial));
    }
}


}
#endif
