// Extracted verbatim from the two actual kernel sources.
static const unsigned int LMH_V2_H_LANES = 8;
static const unsigned int LMH_V2_ACC_INTERLEAVE = 16;
namespace baseline {
float reduce_partials(
    float partial[LMH_V2_H_LANES][LMH_V2_ACC_INTERLEAVE]) {
#pragma HLS INLINE off

reduce_16_to_8:
    for (int index = 0; index < 8; ++index) {
#pragma HLS PIPELINE II=1
    reduce_16_to_8_lane:
        for (int lane = 0; lane < LMH_V2_H_LANES; ++lane) {
#pragma HLS UNROLL
            partial[lane][index] =
                partial[lane][index] + partial[lane][index + 8];
        }
    }

reduce_8_to_4:
    for (int index = 0; index < 4; ++index) {
#pragma HLS PIPELINE II=1
    reduce_8_to_4_lane:
        for (int lane = 0; lane < LMH_V2_H_LANES; ++lane) {
#pragma HLS UNROLL
            partial[lane][index] =
                partial[lane][index] + partial[lane][index + 4];
        }
    }

reduce_4_to_2:
    for (int index = 0; index < 2; ++index) {
#pragma HLS PIPELINE II=1
    reduce_4_to_2_lane:
        for (int lane = 0; lane < LMH_V2_H_LANES; ++lane) {
#pragma HLS UNROLL
            partial[lane][index] =
                partial[lane][index] + partial[lane][index + 2];
        }
    }

reduce_2_to_1:
    for (int lane = 0; lane < LMH_V2_H_LANES; ++lane) {
#pragma HLS UNROLL
        partial[lane][0] = partial[lane][0] + partial[lane][1];
    }

    float lane_sum[LMH_V2_H_LANES];
#pragma HLS ARRAY_PARTITION variable=lane_sum complete dim=1
copy_lane_sum:
    for (int lane = 0; lane < LMH_V2_H_LANES; ++lane) {
#pragma HLS UNROLL
        lane_sum[lane] = partial[lane][0];
    }

    const float sum01 = lane_sum[0] + lane_sum[1];
    const float sum23 = lane_sum[2] + lane_sum[3];
    const float sum45 = lane_sum[4] + lane_sum[5];
    const float sum67 = lane_sum[6] + lane_sum[7];
    const float sum03 = sum01 + sum23;
    const float sum47 = sum45 + sum67;
    return sum03 + sum47;
}

}
namespace candidate {
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

}
