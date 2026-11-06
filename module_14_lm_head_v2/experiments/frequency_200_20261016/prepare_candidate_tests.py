"""Build a full-hidden, small-vocabulary regression from the existing kernel TB."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODULE = HERE.parents[1]
TARGET = HERE / "reduce_layers/tests/kernel_equivalence.cpp"

EXTRA = r'''
float unpack_bf16(const std::vector<ap_uint<128> > &data, int element) {
    const unsigned int u = data[element / 8].range(
        (element % 8) * 16 + 15, (element % 8) * 16).to_uint();
    return bits_to_float(u << 16);
}

float reference_row(const std::vector<ap_uint<128> > &hidden,
                    const std::vector<ap_uint<128> > &weight, int token) {
    float accum[8][16] = {};
    for (int word = 0; word < LMH_V2_HIDDEN_WORDS; ++word) {
        for (int lane = 0; lane < 8; ++lane) {
            // Explicit FP32 multiply then add; never contract to FMA.
            const float product = unpack_bf16(hidden, word * 8 + lane) *
                unpack_bf16(weight, token * LMH_V2_MAX_HIDDEN_SIZE + word * 8 + lane);
            accum[lane][word % 16] = accum[lane][word % 16] + product;
        }
    }
    for (int width = 8; width; width /= 2)
        for (int lane = 0; lane < 8; ++lane)
            for (int i = 0; i < width; ++i)
                accum[lane][i] = accum[lane][i] + accum[lane][i + width];
    float lanes[8];
    for (int lane = 0; lane < 8; ++lane) lanes[lane] = accum[lane][0];
    for (int count = 8; count > 1; count /= 2)
        for (int i = 0; i < count / 2; ++i)
            lanes[i] = lanes[2 * i] + lanes[2 * i + 1];
    return lanes[0];
}

bool test_full_hidden_exact_reference() {
    std::uint32_t rng = 0x20001416u;
    unsigned compared = 0;
    bool ok = true;
    for (int trial = 0; trial < 8; ++trial) {
        std::vector<ap_uint<128> > hidden(LMH_V2_HIDDEN_WORDS, 0);
        std::vector<ap_uint<128> > weight(LMH_V2_WEIGHT_WORDS, 0);
        std::vector<ap_uint<128> > history(LMH_V2_HISTORY_BEATS, 0);
        std::vector<ap_uint<128> > logits(LMH_V2_LOGIT_BEATS, 0);
        for (int element = 0; element < LMH_V2_MAX_HIDDEN_SIZE; ++element) {
            rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5;
            const unsigned int bf = ((rng >> 16) & 0x807f) | ((115 + (rng % 22)) << 7);
            set_bf16(hidden, element, bits_to_float(bf << 16));
        }
        for (int element = 0; element < LMH_V2_MAX_VOCAB_SIZE * LMH_V2_MAX_HIDDEN_SIZE; ++element) {
            rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5;
            unsigned int bf = ((rng >> 16) & 0x807f) | ((115 + (rng % 22)) << 7);
            if (trial == 0 && (element / 8) % 16 != 15) bf = 0; // last slot only
            set_bf16(weight, element, bits_to_float(bf << 16));
        }
        for (int token = 0; token < LMH_V2_MAX_VOCAB_SIZE; ++token)
            history[token / 128][token % 128] = (token % 3 == 0);
        const bool penalty_on = (trial & 1) != 0;
        const kernel_result result = run_kernel(hidden, weight, history, logits,
                                               1, penalty_on, 1.1f);
        ok &= expect(result.status_code == LMH_V2_OK, "full-hidden status");
        unsigned int expected_token = 0;
        float expected_score = 0;
        for (int token = 0; token < LMH_V2_MAX_VOCAB_SIZE; ++token) {
            const float raw = reference_row(hidden, weight, token);
            if (float_bits(raw) != float_bits(get_fp32(logits, token))) {
                std::cerr << "FULL_HIDDEN_MISMATCH trial=" << trial << " token=" << token
                          << " expected=" << float_bits(raw)
                          << " actual=" << float_bits(get_fp32(logits, token)) << std::endl;
                return false;
            }
            float policy = raw;
            if (penalty_on && token % 3 == 0)
                policy = raw < 0 ? raw * 1.1f : raw / 1.1f;
            if (token == 0 || policy > expected_score) {
                expected_score = policy;
                expected_token = token;
            }
            ++compared;
        }
        ok &= expect(result.selected_token == expected_token, "full-hidden selected token");
        ok &= expect(float_bits(result.selected_score) == float_bits(expected_score),
                     "full-hidden selected score bits");
        ok &= expect(result.output_crc == crc32_token_score(expected_token, expected_score),
                     "full-hidden output CRC");
    }
    std::cout << "FULL_HIDDEN_EXACT_LOGITS=" << compared
              << " HIDDEN=" << LMH_V2_MAX_HIDDEN_SIZE << " VOCAB=" << LMH_V2_MAX_VOCAB_SIZE
              << " SEED=0x20001416" << std::endl;
    return ok;
}
'''


def main():
    if TARGET.exists():
        raise SystemExit("Preserve existing test harness: " + str(TARGET))
    original = (MODULE / "tb/lm_head_v2_tb.cpp").read_text(encoding="utf-8")
    source = original.replace("}  // namespace\n\nint main()", EXTRA +
                              "\n}  // namespace\n\nint main()", 1)
    source = source.replace("    passed &= test_rejects_invalid_jobs();",
                            "    passed &= test_rejects_invalid_jobs();\n"
                            "    passed &= test_full_hidden_exact_reference();", 1)
    assert source != original and source.count("bool test_full_hidden_exact_reference") == 1
    TARGET.write_text(source, encoding="utf-8")
    print(TARGET)


if __name__ == "__main__":
    main()
