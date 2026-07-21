from __future__ import annotations

import importlib.util
import json
import struct
import tempfile
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolves annotations through sys.modules during import.
    import sys

    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ref = load_module(
    "lm_head_cpu_reference",
    ROOT / "qwen25_0p5b_python_reference" / "lm_head_cpu_reference.py",
)
exporter = load_module(
    "export_lm_head_weight", ROOT / "tools" / "export_lm_head_weight.py"
)


class LmHeadReferenceTests(unittest.TestCase):
    def test_last_hidden_state_selects_prefill_tail(self) -> None:
        states = np.arange(24, dtype=np.float16).reshape(1, 3, 8)
        np.testing.assert_array_equal(ref.last_hidden_state(states), states[0, -1])

    def test_chunked_lm_head_matches_dense_float32(self) -> None:
        hidden = np.array([1.0, -2.0, 0.5], dtype=np.float16)
        weight = np.array(
            [[1.0, 2.0, 3.0], [-1.0, 0.0, 4.0], [3.0, 1.0, -2.0]],
            dtype=np.float16,
        )
        actual = ref.lm_head_chunked(hidden, weight, vocab_chunk_size=2)
        expected = weight.astype(np.float32) @ hidden.astype(np.float32)
        np.testing.assert_array_equal(actual, expected)

    def test_repetition_penalty_uses_unique_history(self) -> None:
        logits = np.array([2.2, -3.0, 4.0, -5.0], dtype=np.float32)
        actual = ref.apply_repetition_penalty(logits, [0, 0, 1], 1.1)
        expected = np.array([2.0, -3.3, 4.0, -5.0], dtype=np.float32)
        np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-6)

    def test_argmax_breaks_ties_with_lowest_id(self) -> None:
        self.assertEqual(ref.greedy_argmax(np.array([1.0, 7.0, 7.0])), 1)

    def test_argmax_uses_lm_head_output_dtype_after_accumulation(self) -> None:
        accumulator = np.array([20.20183, 20.205446], dtype=np.float32)
        self.assertEqual(ref.greedy_argmax(accumulator), 1)
        fp16_logits = accumulator.astype(np.float16)
        self.assertEqual(float(fp16_logits[0]), float(fp16_logits[1]))
        self.assertEqual(ref.greedy_argmax(fp16_logits), 0)

    def test_builtin_safetensors_reader_handles_bf16(self) -> None:
        values = np.array([[1.5, -2.0], [0.25, 8.0]], dtype=np.float32)
        bf16 = (values.view(np.uint32) >> np.uint32(16)).astype("<u2")
        header = {
            "model.embed_tokens.weight": {
                "dtype": "BF16",
                "shape": [2, 2],
                "data_offsets": [0, int(bf16.nbytes)],
            }
        }
        header_bytes = json.dumps(header, separators=(",", ":")).encode("utf-8")
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "model.safetensors"
            with path.open("wb") as handle:
                handle.write(struct.pack("<Q", len(header_bytes)))
                handle.write(header_bytes)
                handle.write(bf16.tobytes())
            actual = exporter.read_tensor(path, "model.embed_tokens.weight")
        np.testing.assert_array_equal(actual, values)


if __name__ == "__main__":
    unittest.main()
