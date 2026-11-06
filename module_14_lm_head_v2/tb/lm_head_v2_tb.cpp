#include "lm_head_v2.hpp"

#include <cmath>
#include <cstdint>
#include <iostream>
#include <vector>

namespace {

union uint_float_bits {
    std::uint32_t u;
    float f;
};

ap_uint<16> float_to_bf16(float value) {
    uint_float_bits bits;
    bits.f = value;
    const std::uint32_t upper_lsb = (bits.u >> 16) & 1u;
    bits.u += 0x7fffu + upper_lsb;
    return static_cast<ap_uint<16> >(bits.u >> 16);
}

float bits_to_float(std::uint32_t value) {
    uint_float_bits bits;
    bits.u = value;
    return bits.f;
}

std::uint32_t float_bits(float value) {
    uint_float_bits bits;
    bits.f = value;
    return bits.u;
}

void set_bf16(
    std::vector<ap_uint<128> > &buffer,
    std::size_t element_index,
    float value) {
    const std::size_t word = element_index / 8;
    const int lane = static_cast<int>(element_index % 8);
    buffer[word].range(lane * 16 + 15, lane * 16) = float_to_bf16(value);
}

float get_fp32(
    const std::vector<ap_uint<128> > &buffer,
    std::size_t element_index) {
    const std::size_t word = element_index / 4;
    const int lane = static_cast<int>(element_index % 4);
    const std::uint32_t bits = buffer[word]
                                   .range(lane * 32 + 31, lane * 32)
                                   .to_uint();
    return bits_to_float(bits);
}

std::uint32_t crc32_token_score(std::uint32_t token, float score) {
    const std::uint32_t values[2] = {token, float_bits(score)};
    std::uint32_t crc = 0xffffffffu;
    for (int word = 0; word < 2; ++word) {
        for (int byte = 0; byte < 4; ++byte) {
            const std::uint8_t value =
                static_cast<std::uint8_t>(values[word] >> (byte * 8));
            crc ^= value;
            for (int bit = 0; bit < 8; ++bit) {
                crc = (crc >> 1) ^
                      ((crc & 1u) ? 0xedb88320u : 0u);
            }
        }
    }
    return crc ^ 0xffffffffu;
}

struct kernel_result {
    ap_uint<32> selected_token;
    float selected_score;
    ap_uint<32> result_job_id;
    ap_uint<32> status_code;
    ap_uint<32> processed_rows;
    ap_uint<64> perf_cycles_total;
    ap_uint<64> perf_cycles_compute;
    ap_uint<64> perf_read_beats;
    ap_uint<64> perf_write_beats;
    ap_uint<32> output_crc;
    ap_uint<32> build_config;
    ap_uint<32> capabilities;
    ap_uint<32> vocab_rows_done;
    ap_uint<64> weight_read_beats_128;
    ap_uint<32> history_read_words;
    ap_uint<64> logits_write_beats_128;
    ap_uint<64> weight_wait_cycles;
    ap_uint<64> dot_active_cycles;
    ap_uint<32> logits_written;
};

kernel_result run_kernel(
    const std::vector<ap_uint<128> > &hidden,
    const std::vector<ap_uint<128> > &weight,
    const std::vector<ap_uint<128> > &history,
    std::vector<ap_uint<128> > &logits,
    ap_uint<32> write_logits,
    ap_uint<32> enable_penalty,
    float penalty,
    ap_uint<32> abi_version = LMH_V2_ABI_VERSION,
    ap_uint<32> flags = LMH_V2_FLAG_ENABLE_OUTPUT_CRC,
    ap_uint<32> valid_rows = 1) {
    kernel_result result = {};
    lm_head_v2(
        hidden.data(),
        weight.data(),
        history.data(),
        logits.data(),
        LMH_V2_MAX_HIDDEN_SIZE,
        LMH_V2_MAX_VOCAB_SIZE,
        LMH_V2_RUN_DECODE,
        valid_rows,
        write_logits,
        enable_penalty,
        penalty,
        abi_version,
        0x12345678u,
        flags,
        &result.selected_token,
        &result.selected_score,
        &result.result_job_id,
        &result.status_code,
        &result.processed_rows,
        &result.perf_cycles_total,
        &result.perf_cycles_compute,
        &result.perf_read_beats,
        &result.perf_write_beats,
        &result.output_crc,
        &result.build_config,
        &result.capabilities,
        &result.vocab_rows_done,
        &result.weight_read_beats_128,
        &result.history_read_words,
        &result.logits_write_beats_128,
        &result.weight_wait_cycles,
        &result.dot_active_cycles,
        &result.logits_written);
    return result;
}

bool expect(bool condition, const char *message) {
    if (!condition) {
        std::cerr << "FAIL: " << message << std::endl;
    }
    return condition;
}

bool test_penalty_changes_top1() {
    std::vector<ap_uint<128> > hidden(LMH_V2_HIDDEN_WORDS, 0);
    std::vector<ap_uint<128> > weight(LMH_V2_WEIGHT_WORDS, 0);
    std::vector<ap_uint<128> > history(LMH_V2_HISTORY_BEATS, 0);
    std::vector<ap_uint<128> > logits(LMH_V2_LOGIT_BEATS, 0);

    set_bf16(hidden, 0, 1.0f);
    set_bf16(hidden, 1, 0.5f);
    set_bf16(hidden, 2, -1.0f);
    set_bf16(hidden, 3, 2.0f);

    set_bf16(weight, 0 * LMH_V2_MAX_HIDDEN_SIZE + 0, 1.0f);
    set_bf16(weight, 0 * LMH_V2_MAX_HIDDEN_SIZE + 3, 1.5f);
    set_bf16(weight, 1 * LMH_V2_MAX_HIDDEN_SIZE + 0, 0.796875f);
    set_bf16(weight, 1 * LMH_V2_MAX_HIDDEN_SIZE + 3, 1.5f);
    set_bf16(weight, 2 * LMH_V2_MAX_HIDDEN_SIZE + 0, -1.0f);
    history[0][0] = 1;

    const kernel_result result = run_kernel(
        hidden,
        weight,
        history,
        logits,
        1,
        1,
        1.1f);

    bool ok = true;
    ok &= expect(result.status_code == LMH_V2_OK, "penalty status");
    ok &= expect(result.selected_token == 1, "penalty changes top-1");
    ok &= expect(std::fabs(get_fp32(logits, 0) - 4.0f) < 1e-6f,
                 "token 0 raw FP32 logit");
    ok &= expect(std::fabs(get_fp32(logits, 1) - 3.796875f) < 1e-6f,
                 "token 1 raw FP32 logit");
    ok &= expect(result.processed_rows == 1, "processed_rows");
    ok &= expect(result.result_job_id == 0x12345678u, "job id echo");
    ok &= expect(result.vocab_rows_done == LMH_V2_MAX_VOCAB_SIZE,
                 "vocab row count");
    ok &= expect(result.weight_read_beats_128 == LMH_V2_WEIGHT_WORDS,
                 "weight beat count");
    ok &= expect(result.history_read_words ==
                     (LMH_V2_MAX_VOCAB_SIZE + 31) / 32,
                 "logical history word count");
    ok &= expect(result.logits_write_beats_128 == LMH_V2_LOGIT_BEATS,
                 "logit beat count");
    ok &= expect(result.output_crc == crc32_token_score(
                     result.selected_token.to_uint(),
                     result.selected_score),
                 "token/score CRC");
    ok &= expect(result.build_config == LMH_V2_BUILD_CONFIG,
                 "build config");
    return ok;
}

bool test_tie_and_disabled_io() {
    std::vector<ap_uint<128> > hidden(LMH_V2_HIDDEN_WORDS, 0);
    std::vector<ap_uint<128> > weight(LMH_V2_WEIGHT_WORDS, 0);
    std::vector<ap_uint<128> > history(LMH_V2_HISTORY_BEATS, 0);
    std::vector<ap_uint<128> > logits(
        LMH_V2_LOGIT_BEATS,
        ap_uint<128>(0x5a5a5a5au));

    set_bf16(hidden, 0, 1.0f);
    set_bf16(weight, 0 * LMH_V2_MAX_HIDDEN_SIZE, 1.0f);
    set_bf16(weight, 1 * LMH_V2_MAX_HIDDEN_SIZE, 1.0f);
    const ap_uint<128> sentinel = logits[0];

    const kernel_result result = run_kernel(
        hidden,
        weight,
        history,
        logits,
        0,
        0,
        1.0f,
        LMH_V2_ABI_VERSION,
        0);

    bool ok = true;
    ok &= expect(result.status_code == LMH_V2_OK, "tie status");
    ok &= expect(result.selected_token == 0, "tie keeps lower token id");
    ok &= expect(result.history_read_words == 0,
                 "history not read when disabled");
    ok &= expect(result.logits_write_beats_128 == 0,
                 "logits not written when disabled");
    ok &= expect(result.logits_written == 0, "logits_written flag");
    ok &= expect(logits[0] == sentinel, "logit buffer remains untouched");
    ok &= expect(result.output_crc == 0, "CRC disabled");
    return ok;
}

bool test_lane_tree_cancellation() {
    std::vector<ap_uint<128> > hidden(LMH_V2_HIDDEN_WORDS, 0);
    std::vector<ap_uint<128> > weight(LMH_V2_WEIGHT_WORDS, 0);
    std::vector<ap_uint<128> > history(LMH_V2_HISTORY_BEATS, 0);
    std::vector<ap_uint<128> > logits(LMH_V2_LOGIT_BEATS, 0);
    for (int lane = 0; lane < 8; ++lane) {
        set_bf16(hidden, lane, 1.0f);
    }
    set_bf16(weight, 0, 16777216.0f);
    set_bf16(weight, 1, 1.0f);
    set_bf16(weight, 2, -16777216.0f);
    set_bf16(weight, 3, 1.0f);
    set_bf16(weight, LMH_V2_MAX_HIDDEN_SIZE, 1.5f);
    const kernel_result result = run_kernel(
        hidden, weight, history, logits, 1, 0, 1.0f);
    bool ok = true;
    ok &= expect(result.status_code == LMH_V2_OK, "lane tree status");
    ok &= expect(float_bits(get_fp32(logits, 0)) == 0x3f800000u,
                 "adjacent lane cancellation equals 1 (half-split equals 2)");
    ok &= expect(result.selected_token == 1, "lane tree selects token 1");
    ok &= expect(float_bits(result.selected_score) == 0x3fc00000u,
                 "lane tree score bits");
    ok &= expect(result.output_crc == crc32_token_score(1, 1.5f),
                 "lane tree exact CRC");
    return ok;
}

bool test_rejects_invalid_jobs() {
    std::vector<ap_uint<128> > hidden(LMH_V2_HIDDEN_WORDS, 0);
    std::vector<ap_uint<128> > weight(LMH_V2_WEIGHT_WORDS, 0);
    std::vector<ap_uint<128> > history(LMH_V2_HISTORY_BEATS, 0);
    std::vector<ap_uint<128> > logits(LMH_V2_LOGIT_BEATS, 0);

    const kernel_result bad_abi = run_kernel(
        hidden,
        weight,
        history,
        logits,
        0,
        0,
        1.0f,
        1);
    const kernel_result bad_flags = run_kernel(
        hidden,
        weight,
        history,
        logits,
        0,
        0,
        1.0f,
        LMH_V2_ABI_VERSION,
        1u << 31);
    const kernel_result bad_rows = run_kernel(
        hidden,
        weight,
        history,
        logits,
        0,
        0,
        1.0f,
        LMH_V2_ABI_VERSION,
        0,
        2);
    const kernel_result bad_penalty = run_kernel(
        hidden,
        weight,
        history,
        logits,
        0,
        1,
        0.5f);

    bool ok = true;
    ok &= expect(bad_abi.status_code == LMH_V2_BAD_ABI, "bad ABI");
    ok &= expect(bad_flags.status_code == LMH_V2_BAD_FLAGS, "bad flags");
    ok &= expect(bad_rows.status_code == LMH_V2_BAD_DIMENSION,
                 "bad valid_rows");
    ok &= expect(bad_penalty.status_code == LMH_V2_NUMERIC_ERROR,
                 "bad penalty");
    ok &= expect(bad_abi.vocab_rows_done == 0,
                 "invalid job performs no work");
    return ok;
}

}  // namespace

int main() {
    bool passed = true;
    passed &= test_penalty_changes_top1();
    passed &= test_tie_and_disabled_io();
    passed &= test_lane_tree_cancellation();
    passed &= test_rejects_invalid_jobs();
    std::cout << "LM_HEAD_V2_CSIM=" << (passed ? "PASS" : "FAIL")
              << std::endl;
    return passed ? 0 : 1;
}
