#include "lm_head_v2.hpp"

#include "hls_stream.h"

namespace {

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

void policy_and_argmax(
    hls::stream<float> &raw_score_fifo,
    const ap_uint<128> *history_bitmap,
    ap_uint<128> *optional_logits,
    ap_uint<32> vocab_size,
    bool write_logits,
    bool enable_penalty,
    float repetition_penalty,
    ap_uint<32> &best_token_out,
    float &best_score_out,
    ap_uint<32> &rows_done_out,
    ap_uint<32> &history_words_out,
    ap_uint<64> &logit_beats_out,
    bool &numeric_error_out,
    hls::stream<ap_uint<1> > &done) {
    ap_uint<128> history_word = 0;
    ap_uint<128> logits_pack = 0;
    ap_uint<32> best_token = 0;
    float best_score = 0.0f;
    bool numeric_error = false;
    ap_uint<64> logit_beats = 0;

policy_vocab_loop:
    for (ap_uint<32> token = 0; token < vocab_size; ++token) {
#pragma HLS LOOP_TRIPCOUNT min=64 max=151936
        const float raw_score = raw_score_fifo.read();
        const bool raw_is_finite = finite_float(raw_score);
        numeric_error |= !raw_is_finite;

        if (write_logits) {
            const int pack_lane = token.to_uint() & 3;
            logits_pack.range(pack_lane * 32 + 31, pack_lane * 32) =
                float_to_bits(raw_score);
            if (pack_lane == 3 || token + 1 == vocab_size) {
                optional_logits[token.to_uint() >> 2] = logits_pack;
                logits_pack = 0;
                ++logit_beats;
            }
        }

        bool seen = false;
        if (enable_penalty) {
            if ((token.to_uint() & 127) == 0) {
                history_word = history_bitmap[token.to_uint() >> 7];
            }
            seen = history_word[token.to_uint() & 127] != 0;
        }

        float policy_score = raw_score;
        if (!raw_is_finite) {
            policy_score = bits_to_float(0xff800000u);
        } else if (enable_penalty && seen) {
            policy_score = raw_score < 0.0f
                               ? raw_score * repetition_penalty
                               : raw_score / repetition_penalty;
        }

        if (token == 0 || policy_score > best_score) {
            best_score = policy_score;
            best_token = token;
        }
    }

    best_token_out = best_token;
    best_score_out = best_score;
    rows_done_out = vocab_size;
    if (enable_penalty) {
        history_words_out = (vocab_size + 31) / 32;
    } else {
        history_words_out = 0;
    }
    logit_beats_out = logit_beats;
    numeric_error_out = numeric_error;
    done.write(1);
}

void count_until_done(
    hls::stream<ap_uint<1> > &done,
    ap_uint<64> &cycles) {
    bool finished = false;
    ap_uint<64> count = 0;
count_loop:
    while (!finished) {
#pragma HLS PIPELINE II=1
        if (!done.empty()) {
            (void)done.read();
            finished = true;
        } else {
            ++count;
        }
    }
    cycles = count;
}

void run_dataflow(
    const ap_uint<128> *weight,
    const float hidden_cache[LMH_V2_H_LANES][LMH_V2_HIDDEN_WORDS],
    const ap_uint<128> *history_bitmap,
    ap_uint<128> *optional_logits,
    ap_uint<32> vocab_size,
    bool write_logits,
    bool enable_penalty,
    float repetition_penalty,
    ap_uint<32> &best_token,
    float &best_score,
    ap_uint<32> &rows_done,
    ap_uint<32> &history_words,
    ap_uint<64> &logit_beats,
    bool &numeric_error,
    ap_uint<64> &weight_reader_cycles,
    ap_uint<64> &compute_cycles) {
#pragma HLS DATAFLOW
    hls::stream<ap_uint<128> > weight_fifo("weight_fifo");
    hls::stream<accumulator_slice_t> context_fifo("context_fifo");
    hls::stream<float> raw_score_fifo("raw_score_fifo");
    hls::stream<ap_uint<1> > weight_reader_done("weight_reader_done");
    hls::stream<ap_uint<1> > compute_done("compute_done");
#pragma HLS STREAM variable=weight_fifo depth=LMH_V2_WEIGHT_FIFO_DEPTH
#pragma HLS STREAM variable=context_fifo depth=32
#pragma HLS STREAM variable=raw_score_fifo depth=32
#pragma HLS STREAM variable=weight_reader_done depth=2
#pragma HLS STREAM variable=compute_done depth=2

    const ap_uint<32> total_words = vocab_size * LMH_V2_HIDDEN_WORDS;
    read_weight_stream(weight, total_words, weight_fifo, weight_reader_done);
    dot_product_rows(
        weight_fifo,
        hidden_cache,
        vocab_size,
        context_fifo);
    reduce_rows(context_fifo, raw_score_fifo, vocab_size);
    policy_and_argmax(
        raw_score_fifo,
        history_bitmap,
        optional_logits,
        vocab_size,
        write_logits,
        enable_penalty,
        repetition_penalty,
        best_token,
        best_score,
        rows_done,
        history_words,
        logit_beats,
        numeric_error,
        compute_done);
    count_until_done(weight_reader_done, weight_reader_cycles);
    count_until_done(compute_done, compute_cycles);
}

ap_uint<32> validate_job(
    ap_uint<32> hidden_size,
    ap_uint<32> vocab_size,
    ap_uint<32> run_mode,
    ap_uint<32> valid_rows,
    ap_uint<32> write_logits,
    ap_uint<32> enable_penalty,
    float repetition_penalty,
    ap_uint<32> abi_version,
    ap_uint<32> flags) {
#pragma HLS INLINE
    if (abi_version != LMH_V2_ABI_VERSION) {
        return LMH_V2_BAD_ABI;
    }
    if ((flags & ~LMH_V2_VALID_FLAGS) != 0) {
        return LMH_V2_BAD_FLAGS;
    }
    if (hidden_size != LMH_V2_MAX_HIDDEN_SIZE ||
        vocab_size != LMH_V2_MAX_VOCAB_SIZE ||
        valid_rows != 1 ||
        (run_mode != LMH_V2_RUN_PREFILL &&
         run_mode != LMH_V2_RUN_DECODE) ||
        write_logits > 1 ||
        enable_penalty > 1) {
        return LMH_V2_BAD_DIMENSION;
    }
    if (enable_penalty &&
        (!finite_float(repetition_penalty) || repetition_penalty < 1.0f)) {
        return LMH_V2_NUMERIC_ERROR;
    }
    return LMH_V2_OK;
}

}  // namespace

extern "C" void lm_head_v2(
    const ap_uint<128> *hidden,
    const ap_uint<128> *shared_vocab_weight,
    const ap_uint<128> *history_bitmap,
    ap_uint<128> *optional_logits,
    ap_uint<32> hidden_size,
    ap_uint<32> vocab_size,
    ap_uint<32> run_mode,
    ap_uint<32> valid_rows,
    ap_uint<32> write_logits,
    ap_uint<32> enable_penalty,
    float repetition_penalty,
    ap_uint<32> abi_version,
    ap_uint<32> job_id,
    ap_uint<32> flags,
    ap_uint<32> *selected_token,
    float *selected_score,
    ap_uint<32> *result_job_id,
    ap_uint<32> *status_code,
    ap_uint<32> *processed_rows,
    ap_uint<64> *perf_cycles_total,
    ap_uint<64> *perf_cycles_compute,
    ap_uint<64> *perf_read_beats,
    ap_uint<64> *perf_write_beats,
    ap_uint<32> *output_crc,
    ap_uint<32> *build_config,
    ap_uint<32> *capabilities,
    ap_uint<32> *vocab_rows_done,
    ap_uint<64> *weight_read_beats_128,
    ap_uint<32> *history_read_words,
    ap_uint<64> *logits_write_beats_128,
    ap_uint<64> *weight_wait_cycles,
    ap_uint<64> *dot_active_cycles,
    ap_uint<32> *logits_written) {
#ifdef LMH_V2_TEST_SMALL
#pragma HLS INTERFACE m_axi port=hidden offset=slave bundle=hidden depth=4 max_read_burst_length=64 num_read_outstanding=4
#pragma HLS INTERFACE m_axi port=shared_vocab_weight offset=slave bundle=weight depth=256 max_read_burst_length=16 num_read_outstanding=16 latency=64
#pragma HLS INTERFACE m_axi port=history_bitmap offset=slave bundle=history depth=1 max_read_burst_length=16 num_read_outstanding=4
#pragma HLS INTERFACE m_axi port=optional_logits offset=slave bundle=logits depth=16 max_write_burst_length=64 num_write_outstanding=8
#else
#pragma HLS INTERFACE m_axi port=hidden offset=slave bundle=hidden depth=112 max_read_burst_length=64 num_read_outstanding=4
#pragma HLS INTERFACE m_axi port=shared_vocab_weight offset=slave bundle=weight depth=17016832 max_read_burst_length=16 num_read_outstanding=16 latency=64
#pragma HLS INTERFACE m_axi port=history_bitmap offset=slave bundle=history depth=1187 max_read_burst_length=16 num_read_outstanding=4
#pragma HLS INTERFACE m_axi port=optional_logits offset=slave bundle=logits depth=37984 max_write_burst_length=64 num_write_outstanding=8
#endif

#pragma HLS INTERFACE s_axilite port=hidden bundle=control
#pragma HLS INTERFACE s_axilite port=shared_vocab_weight bundle=control
#pragma HLS INTERFACE s_axilite port=history_bitmap bundle=control
#pragma HLS INTERFACE s_axilite port=optional_logits bundle=control
#pragma HLS INTERFACE s_axilite port=hidden_size bundle=control
#pragma HLS INTERFACE s_axilite port=vocab_size bundle=control
#pragma HLS INTERFACE s_axilite port=run_mode bundle=control
#pragma HLS INTERFACE s_axilite port=valid_rows bundle=control
#pragma HLS INTERFACE s_axilite port=write_logits bundle=control
#pragma HLS INTERFACE s_axilite port=enable_penalty bundle=control
#pragma HLS INTERFACE s_axilite port=repetition_penalty bundle=control
#pragma HLS INTERFACE s_axilite port=abi_version bundle=control
#pragma HLS INTERFACE s_axilite port=job_id bundle=control
#pragma HLS INTERFACE s_axilite port=flags bundle=control
#pragma HLS INTERFACE s_axilite port=selected_token bundle=control
#pragma HLS INTERFACE s_axilite port=selected_score bundle=control
#pragma HLS INTERFACE s_axilite port=result_job_id bundle=control
#pragma HLS INTERFACE s_axilite port=status_code bundle=control
#pragma HLS INTERFACE s_axilite port=processed_rows bundle=control
#pragma HLS INTERFACE s_axilite port=perf_cycles_total bundle=control
#pragma HLS INTERFACE s_axilite port=perf_cycles_compute bundle=control
#pragma HLS INTERFACE s_axilite port=perf_read_beats bundle=control
#pragma HLS INTERFACE s_axilite port=perf_write_beats bundle=control
#pragma HLS INTERFACE s_axilite port=output_crc bundle=control
#pragma HLS INTERFACE s_axilite port=build_config bundle=control
#pragma HLS INTERFACE s_axilite port=capabilities bundle=control
#pragma HLS INTERFACE s_axilite port=vocab_rows_done bundle=control
#pragma HLS INTERFACE s_axilite port=weight_read_beats_128 bundle=control
#pragma HLS INTERFACE s_axilite port=history_read_words bundle=control
#pragma HLS INTERFACE s_axilite port=logits_write_beats_128 bundle=control
#pragma HLS INTERFACE s_axilite port=weight_wait_cycles bundle=control
#pragma HLS INTERFACE s_axilite port=dot_active_cycles bundle=control
#pragma HLS INTERFACE s_axilite port=logits_written bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control

    ap_uint<32> selected_token_value = 0;
    float selected_score_value = 0.0f;
    ap_uint<32> status_value = validate_job(
        hidden_size,
        vocab_size,
        run_mode,
        valid_rows,
        write_logits,
        enable_penalty,
        repetition_penalty,
        abi_version,
        flags);
    ap_uint<32> processed_rows_value = 0;
    ap_uint<64> perf_cycles_total_value = 0;
    ap_uint<64> perf_cycles_compute_value = 0;
    ap_uint<64> perf_read_beats_value = 0;
    ap_uint<64> perf_write_beats_value = 0;
    ap_uint<32> output_crc_value = 0;
    ap_uint<32> vocab_rows_done_value = 0;
    ap_uint<64> weight_read_beats_value = 0;
    ap_uint<32> history_read_words_value = 0;
    ap_uint<64> logits_write_beats_value = 0;
    ap_uint<64> weight_wait_cycles_value = 0;
    ap_uint<64> dot_active_cycles_value = 0;
    ap_uint<32> logits_written_value = 0;

    float hidden_cache[LMH_V2_H_LANES][LMH_V2_HIDDEN_WORDS];
#pragma HLS ARRAY_PARTITION variable=hidden_cache complete dim=1
#pragma HLS RESOURCE variable=hidden_cache core=RAM_1P_BRAM
    if (status_value == LMH_V2_OK) {
        load_hidden(hidden, hidden_cache);

        ap_uint<32> best_token = 0;
        float best_score = 0.0f;
        ap_uint<32> rows_done = 0;
        ap_uint<32> logical_history_words = 0;
        ap_uint<64> logit_beats = 0;
        ap_uint<64> weight_reader_cycles = 0;
        ap_uint<64> compute_cycles = 0;
        bool numeric_error = false;
        run_dataflow(
            shared_vocab_weight,
            hidden_cache,
            history_bitmap,
            optional_logits,
            vocab_size,
            write_logits != 0,
            enable_penalty != 0,
            repetition_penalty,
            best_token,
            best_score,
            rows_done,
            logical_history_words,
            logit_beats,
            numeric_error,
            weight_reader_cycles,
            compute_cycles);

        const ap_uint<64> weight_beats =
            static_cast<ap_uint<64> >(vocab_size) * LMH_V2_HIDDEN_WORDS;
        ap_uint<64> history_beats = 0;
        if (enable_penalty) {
            history_beats = (vocab_size + 127) / 128;
        }

        perf_cycles_compute_value = compute_cycles;
        perf_cycles_total_value = compute_cycles + LMH_V2_HIDDEN_WORDS;
        perf_read_beats_value = LMH_V2_HIDDEN_WORDS + weight_beats + history_beats;
        perf_write_beats_value = logit_beats;
        vocab_rows_done_value = rows_done;
        weight_read_beats_value = weight_beats;
        history_read_words_value = logical_history_words;
        logits_write_beats_value = logit_beats;
        if (weight_reader_cycles > weight_beats) {
            weight_wait_cycles_value = weight_reader_cycles - weight_beats;
        }
        dot_active_cycles_value = weight_beats;
        logits_written_value = write_logits;

        if (numeric_error) {
            status_value = LMH_V2_NUMERIC_ERROR;
        } else {
            selected_token_value = best_token;
            selected_score_value = best_score;
            processed_rows_value = 1;
            if ((flags & LMH_V2_FLAG_ENABLE_OUTPUT_CRC) != 0) {
                output_crc_value = crc32_token_score(
                    best_token,
                    float_to_bits(best_score));
            }
        }
    }

    *selected_token = selected_token_value;
    *selected_score = selected_score_value;
    *result_job_id = job_id;
    *status_code = status_value;
    *processed_rows = processed_rows_value;
    *perf_cycles_total = perf_cycles_total_value;
    *perf_cycles_compute = perf_cycles_compute_value;
    *perf_read_beats = perf_read_beats_value;
    *perf_write_beats = perf_write_beats_value;
    *output_crc = output_crc_value;
    *build_config = LMH_V2_BUILD_CONFIG;
    *capabilities = LMH_V2_CAPABILITIES;
    *vocab_rows_done = vocab_rows_done_value;
    *weight_read_beats_128 = weight_read_beats_value;
    *history_read_words = history_read_words_value;
    *logits_write_beats_128 = logits_write_beats_value;
    *weight_wait_cycles = weight_wait_cycles_value;
    *dot_active_cycles = dot_active_cycles_value;
    *logits_written = logits_written_value;
}
