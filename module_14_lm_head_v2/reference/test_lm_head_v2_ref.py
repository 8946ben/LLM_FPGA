import unittest

import numpy as np

from lm_head_v2_ref import (
    apply_repetition_penalty,
    float32_to_bf16_bits,
    run_reference,
)


class LmHeadV2ReferenceTest(unittest.TestCase):
    def test_lane_tree_cancellation_changes_top1(self) -> None:
        # All inputs are exact BF16 values. Adjacent FP32 sums produce 1;
        # the old half-split lane tree produces 2 and selects token 0.
        hidden = np.zeros(32, dtype=np.float32)
        hidden[:8] = 1.0
        weight = np.zeros((64, 32), dtype=np.float32)
        weight[0, :4] = [16777216.0, 1.0, -16777216.0, 1.0]
        weight[1, 0] = 1.5
        result = run_reference(float32_to_bf16_bits(hidden),
                               float32_to_bf16_bits(weight))
        self.assertEqual(int(result["raw_logits"][0].view(np.uint32)), 0x3F800000)
        self.assertEqual(result["selected_token"], 1)
        self.assertEqual(int(result["selected_score"].view(np.uint32)), 0x3FC00000)

    def test_penalty_changes_top1(self) -> None:
        hidden = np.zeros(32, dtype=np.float32)
        hidden[:4] = [1.0, 0.5, -1.0, 2.0]
        weight = np.zeros((64, 32), dtype=np.float32)
        weight[0, [0, 3]] = [1.0, 1.5]
        weight[1, [0, 3]] = [0.796875, 1.5]
        history = np.zeros(2, dtype=np.uint32)
        history[0] = 1

        result = run_reference(
            float32_to_bf16_bits(hidden),
            float32_to_bf16_bits(weight),
            history,
            enable_penalty=True,
            repetition_penalty=1.1,
            token_block=16,
        )
        self.assertEqual(result["selected_token"], 1)
        self.assertEqual(result["raw_logits"][0], np.float32(4.0))
        self.assertEqual(result["raw_logits"][1], np.float32(3.796875))

    def test_fixed_reduction_and_tie_choose_lower_token(self) -> None:
        hidden = np.zeros(32, dtype=np.float32)
        hidden[0] = 1.0
        weight = np.zeros((64, 32), dtype=np.float32)
        weight[0, 0] = 1.0
        weight[1, 0] = 1.0
        result = run_reference(
            float32_to_bf16_bits(hidden),
            float32_to_bf16_bits(weight),
            token_block=64,
        )
        self.assertEqual(result["selected_token"], 0)
        self.assertEqual(result["selected_score"], np.float32(1.0))

    def test_negative_seen_score_is_multiplied(self) -> None:
        raw = np.array([-2.0, 2.0, -3.0], dtype=np.float32)
        history = np.array([0b011], dtype=np.uint32)
        actual = apply_repetition_penalty(raw, history, 1.25)
        np.testing.assert_array_equal(
            actual,
            np.array([-2.5, 1.6, -3.0], dtype=np.float32),
        )

    def test_invalid_penalty_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            apply_repetition_penalty(
                np.array([1.0], dtype=np.float32),
                np.array([1], dtype=np.uint32),
                0.5,
            )


if __name__ == "__main__":
    unittest.main()
