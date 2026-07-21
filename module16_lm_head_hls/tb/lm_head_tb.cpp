#include "lm_head_kernel.hpp"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

template <typename T>
std::vector<T> read_binary(const std::string &path, std::size_t count) {
    std::ifstream stream(path.c_str(), std::ios::binary);
    if (!stream) {
        throw std::runtime_error("Cannot open " + path);
    }
    std::vector<T> values(count);
    stream.read(
        reinterpret_cast<char *>(values.data()),
        static_cast<std::streamsize>(count * sizeof(T)));
    if (stream.gcount() != static_cast<std::streamsize>(count * sizeof(T))) {
        throw std::runtime_error("Unexpected byte count in " + path);
    }
    return values;
}

std::vector<half> read_half_npy(
    const std::string &path,
    std::size_t expected_elements) {
    std::ifstream stream(path.c_str(), std::ios::binary);
    if (!stream) {
        throw std::runtime_error("Cannot open " + path);
    }
    char magic[6];
    stream.read(magic, sizeof(magic));
    const char expected_magic[6] = {'\x93', 'N', 'U', 'M', 'P', 'Y'};
    for (int index = 0; index < 6; ++index) {
        if (magic[index] != expected_magic[index]) {
            throw std::runtime_error("Not an NPY file: " + path);
        }
    }
    unsigned char major = 0;
    unsigned char minor = 0;
    stream.read(reinterpret_cast<char *>(&major), 1);
    stream.read(reinterpret_cast<char *>(&minor), 1);
    (void)minor;
    std::uint32_t header_length = 0;
    if (major == 1) {
        std::uint16_t short_length = 0;
        stream.read(reinterpret_cast<char *>(&short_length), sizeof(short_length));
        header_length = short_length;
    } else if (major == 2 || major == 3) {
        stream.read(reinterpret_cast<char *>(&header_length), sizeof(header_length));
    } else {
        throw std::runtime_error("Unsupported NPY version in " + path);
    }
    std::string header(header_length, '\0');
    stream.read(&header[0], static_cast<std::streamsize>(header_length));
    if (header.find("'<f2'") == std::string::npos &&
        header.find("\"<f2\"") == std::string::npos) {
        throw std::runtime_error("Expected little-endian FP16 NPY: " + path);
    }

    std::vector<half> values(expected_elements);
    stream.read(
        reinterpret_cast<char *>(values.data()),
        static_cast<std::streamsize>(expected_elements * sizeof(half)));
    if (stream.gcount() !=
        static_cast<std::streamsize>(expected_elements * sizeof(half))) {
        throw std::runtime_error("Unexpected tensor size in " + path);
    }
    return values;
}

void set_history(std::vector<ap_uint<32> > &bitmap, int token_id) {
    bitmap[token_id / 32][token_id % 32] = 1;
}

bool run_synthetic_test() {
    const int hidden_size = 4;
    const int vocab_size = 4;
    // Allocate the configured interface depths.  Normal C simulation uses the
    // production dimensions; LMH_COSIM_SMALL uses the 4x4 RTL interface image.
    std::vector<half> hidden(LMH_MAX_HIDDEN_SIZE, half(0.0f));
    hidden[0] = half(1.0f);
    hidden[1] = half(0.5f);
    hidden[2] = half(-1.0f);
    hidden[3] = half(2.0f);

    const float raw_weight[vocab_size][hidden_size] = {
        {1.0f, 0.0f, 0.0f, 1.5f},   // raw score 4.0, penalized 3.636...
        {0.8f, 0.0f, 0.0f, 1.5f},   // raw score 3.8, selected after penalty
        {-1.0f, 0.5f, 1.0f, 0.0f},
        {0.0f, 1.0f, 0.0f, 0.0f},
    };
    std::vector<half> weight(
        static_cast<std::size_t>(LMH_MAX_VOCAB_SIZE) * LMH_MAX_HIDDEN_SIZE,
        half(0.0f));
    for (int token = 0; token < vocab_size; ++token) {
        for (int index = 0; index < hidden_size; ++index) {
            weight[token * hidden_size + index] = half(raw_weight[token][index]);
        }
    }
    std::vector<ap_uint<32> > history(LMH_HISTORY_WORDS, 0);
    set_history(history, 0);
    std::vector<half> logits(LMH_MAX_VOCAB_SIZE, half(0.0f));
    ap_uint<32> selected = 0;
    float selected_score = 0.0f;
    lm_head_argmax(
        hidden.data(),
        weight.data(),
        history.data(),
        logits.data(),
        hidden_size,
        vocab_size,
        1,
        1,
        1.1f,
        &selected,
        &selected_score);

    const bool passed = selected.to_uint() == 1 &&
                        std::fabs(static_cast<float>(logits[0]) - 4.0f) < 0.01f &&
                        std::fabs(static_cast<float>(logits[1]) - 3.8f) < 0.01f;
    std::cout << "synthetic selected=" << selected.to_uint()
              << " score=" << selected_score
              << " status=" << (passed ? "PASS" : "FAIL") << std::endl;
    return passed;
}

std::vector<int> top_k_ids(const std::vector<half> &values, int count) {
    std::vector<int> ids(values.size());
    for (std::size_t index = 0; index < values.size(); ++index) {
        ids[index] = static_cast<int>(index);
    }
    const int actual_count = std::min(count, static_cast<int>(ids.size()));
    std::partial_sort(
        ids.begin(),
        ids.begin() + actual_count,
        ids.end(),
        [&values](int left, int right) {
            const float left_value = static_cast<float>(values[left]);
            const float right_value = static_cast<float>(values[right]);
            return left_value == right_value ? left < right : left_value > right_value;
        });
    ids.resize(actual_count);
    return ids;
}

int top_k_overlap(
    const std::vector<half> &left,
    const std::vector<half> &right,
    int count) {
    const std::vector<int> left_ids = top_k_ids(left, count);
    const std::vector<int> right_ids = top_k_ids(right, count);
    int overlap = 0;
    for (std::size_t left_index = 0; left_index < left_ids.size(); ++left_index) {
        if (std::find(right_ids.begin(), right_ids.end(), left_ids[left_index]) !=
            right_ids.end()) {
            ++overlap;
        }
    }
    return overlap;
}

bool run_trace_case(
    const std::vector<half> &weight,
    const std::string &hidden_path,
    const std::string &golden_path,
    const std::string &history_path,
    unsigned int expected_token,
    const std::string &case_name) {
    std::vector<half> hidden = read_binary<half>(hidden_path, LMH_MAX_HIDDEN_SIZE);
    std::vector<half> golden = read_binary<half>(golden_path, LMH_MAX_VOCAB_SIZE);
    std::vector<ap_uint<32> > history =
        read_binary<ap_uint<32> >(history_path, LMH_HISTORY_WORDS);
    std::vector<half> actual(LMH_MAX_VOCAB_SIZE);

    ap_uint<32> selected = 0;
    float selected_score = 0.0f;
    lm_head_argmax(
        hidden.data(),
        weight.data(),
        history.data(),
        actual.data(),
        LMH_MAX_HIDDEN_SIZE,
        LMH_MAX_VOCAB_SIZE,
        1,
        1,
        1.1f,
        &selected,
        &selected_score);

    float max_abs_error = 0.0f;
    double abs_error_sum = 0.0;
    double dot_product = 0.0;
    double actual_square_sum = 0.0;
    double golden_square_sum = 0.0;
    int mismatch_count = 0;
    for (int index = 0; index < LMH_MAX_VOCAB_SIZE; ++index) {
        const float actual_value = static_cast<float>(actual[index]);
        const float golden_value = static_cast<float>(golden[index]);
        const float error = std::fabs(actual_value - golden_value);
        if (error > max_abs_error) {
            max_abs_error = error;
        }
        abs_error_sum += error;
        dot_product += static_cast<double>(actual_value) * golden_value;
        actual_square_sum += static_cast<double>(actual_value) * actual_value;
        golden_square_sum += static_cast<double>(golden_value) * golden_value;
        if (actual[index].get_bits() != golden[index].get_bits()) {
            ++mismatch_count;
        }
    }
    const double mean_abs_error = abs_error_sum / LMH_MAX_VOCAB_SIZE;
    const double cosine_similarity =
        dot_product / std::sqrt(actual_square_sum * golden_square_sum);
    const int overlap = top_k_overlap(actual, golden, 5);
    const bool passed = selected.to_uint() == expected_token &&
                        max_abs_error <= 0.02f &&
                        cosine_similarity >= 0.999 &&
                        overlap >= 4;
    std::cout << "trace case=" << case_name
              << " selected=" << selected.to_uint()
              << " expected=" << expected_token
              << " selected_score=" << selected_score
              << " max_abs_error=" << max_abs_error
              << " mean_abs_error=" << mean_abs_error
              << " cosine=" << cosine_similarity
              << " top5_overlap=" << overlap << "/5"
              << " fp16_bit_mismatches=" << mismatch_count
              << " status=" << (passed ? "PASS" : "FAIL") << std::endl;
    return passed;
}

unsigned int read_expected_token(const std::string &path) {
    std::ifstream stream(path.c_str());
    unsigned int token = 0;
    if (!(stream >> token)) {
        throw std::runtime_error("Cannot read expected token from " + path);
    }
    return token;
}

bool run_trace_test(int argc, char **argv) {
    if (argc == 1) {
        return true;
    }
    if (argc >= 3 && std::string(argv[1]) == "--trace-all") {
        if (argc != 4) {
            throw std::runtime_error(
                "Usage: lm_head_tb --trace-all weight.npy fixture_root");
        }
        std::cout << "loading full Qwen weight once for all trace steps..." << std::endl;
        const std::vector<half> weight = read_half_npy(
            argv[2],
            static_cast<std::size_t>(LMH_MAX_VOCAB_SIZE) * LMH_MAX_HIDDEN_SIZE);
        bool all_passed = true;
        for (int step = 0; step < 8; ++step) {
            const std::string step_name = step < 10
                                              ? "step_0" + std::to_string(step)
                                              : "step_" + std::to_string(step);
            const std::string directory = std::string(argv[3]) + "/" + step_name;
            const unsigned int expected =
                read_expected_token(directory + "/expected_token.txt");
            all_passed &= run_trace_case(
                weight,
                directory + "/hidden.fp16.bin",
                directory + "/golden_logits.fp16.bin",
                directory + "/history_bitmap.u32.bin",
                expected,
                step_name);
        }
        return all_passed;
    }
    if (argc != 7 || std::string(argv[1]) != "--trace") {
        throw std::runtime_error(
            "Usage: lm_head_tb [--trace weight.npy hidden.bin golden.bin "
            "history.bin expected_token]");
    }
    std::cout << "loading full Qwen weight..." << std::endl;
    const std::vector<half> weight = read_half_npy(
        argv[2],
        static_cast<std::size_t>(LMH_MAX_VOCAB_SIZE) * LMH_MAX_HIDDEN_SIZE);
    return run_trace_case(
        weight,
        argv[3],
        argv[4],
        argv[5],
        static_cast<unsigned int>(std::stoul(argv[6])),
        "single");
}

}  // namespace

int main(int argc, char **argv) {
    try {
        const bool synthetic_ok = run_synthetic_test();
        const bool trace_ok = run_trace_test(argc, argv);
        const bool passed = synthetic_ok && trace_ok;
        std::cout << "HLS_CSIM_OVERALL=" << (passed ? "PASS" : "FAIL") << std::endl;
        return passed ? 0 : 1;
    } catch (const std::exception &error) {
        std::cerr << "ERROR: " << error.what() << std::endl;
        return 2;
    }
}
