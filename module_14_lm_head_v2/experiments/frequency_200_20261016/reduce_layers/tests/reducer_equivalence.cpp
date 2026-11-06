#include <cmath>
#include <cstdint>
#include <cstring>
#include <iostream>
#include "reducers.inc"

static std::uint32_t bits(float x) {
    std::uint32_t u;
    std::memcpy(&u, &x, sizeof(u));
    return u;
}

int main() {
    std::uint32_t rng = 0x14a52026u;
    unsigned compared = 0;
    for (unsigned sample = 0; sample < 50004; ++sample) {
        float a[8][16], b[8][16];
        for (int lane = 0; lane < 8; ++lane) {
            for (int slot = 0; slot < 16; ++slot) {
                rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5;
                const int mantissa = static_cast<int>(rng & 0xffff) - 32768;
                const int exponent = static_cast<int>((rng >> 16) % 201) - 100;
                float x = std::ldexp(static_cast<float>(mantissa) / 32768.0f, exponent);
                if (sample < 2) x = sample == 0 ? 0.0f : -0.0f;
                if (sample == 2) {
                    x = 0;
                    if (lane == 0 && slot == 0) x = 16777216.0f;
                    if (lane == 0 && slot == 8) x = -16777216.0f;
                    if (lane == 0 && (slot == 1 || slot == 9)) x = 1.0f;
                }
                if (sample == 3) {
                    x = 0;
                    if (slot == 0 && lane == 0) x = 16777216.0f;
                    if (slot == 0 && lane == 2) x = -16777216.0f;
                    if (slot == 0 && (lane == 1 || lane == 3)) x = 1.0f;
                }
                a[lane][slot] = b[lane][slot] = x;
            }
        }
        const float expected = baseline::reduce_partials(a);
        const float actual = candidate::reduce_partials(b);
        if (bits(expected) != bits(actual) ||
            (sample == 2 && expected != 2.0f) ||
            (sample == 3 && expected != 1.0f)) {
            std::cerr << "FAIL sample=" << sample << " expected=" << bits(expected)
                      << " actual=" << bits(actual) << std::endl;
            return 1;
        }
        ++compared;
    }
    std::cout << "REDUCER_BIT_EXACT_PASS samples=" << compared
              << " inputs_per_sample=128 seed=0x14a52026" << std::endl;
    return 0;
}
