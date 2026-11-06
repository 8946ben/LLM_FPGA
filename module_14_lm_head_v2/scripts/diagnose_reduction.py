"""Compare the legacy and C++ lane trees against archived production logits.

No golden assets are modified. Both candidates share the existing interleave
reduction; only the final lane tree changes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "reference"))
import lm_head_v2_ref as reference


def adjacent_lane_tree(partial: np.ndarray) -> np.ndarray:
    for width in (8, 4, 2, 1):
        partial[:, :, :width] = np.add(
            partial[:, :, :width], partial[:, :, width : 2 * width], dtype=np.float32
        )
    lanes = partial[:, :, 0]
    pairs = np.add(lanes[:, 0::2], lanes[:, 1::2], dtype=np.float32)
    halves = np.add(pairs[:, 0::2], pairs[:, 1::2], dtype=np.float32)
    return np.add(halves[:, 0], halves[:, 1], dtype=np.float32)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--board", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    hidden = np.fromfile(args.assets / "trace/step_00/hidden.bf16.bin", dtype="<u2")
    weight = np.memmap(args.assets / "shared_vocab_weight.bf16.bin", mode="r",
                       dtype="<u2", shape=(151936, 896))
    board = np.fromfile(args.board, dtype="<f4")
    legacy_path = args.output_dir / "legacy_golden/trace/step_00/raw_logits.fp32.bin"
    if not legacy_path.exists():
        legacy_path = args.assets / "trace/step_00/raw_logits.fp32.bin"
    legacy = np.fromfile(legacy_path, dtype="<f4")
    reference._reduce_partials = adjacent_lane_tree
    candidate = reference.compute_raw_logits(hidden, weight)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    candidate.astype("<f4").tofile(args.output_dir / "candidate_raw_logits.fp32.bin")
    history = np.fromfile(args.assets / "trace/step_00/history_bitmap.u32.bin", dtype="<u4")
    scores = reference.apply_repetition_penalty(candidate, history, 1.1)
    token = int(np.argmax(scores))
    summary = {
        "elements": int(board.size),
        "legacy_exact_elements": int(np.count_nonzero(board.view(np.uint32) == legacy.view(np.uint32))),
        "adjacent_exact_elements": int(np.count_nonzero(board.view(np.uint32) == candidate.view(np.uint32))),
        "max_absolute_error": float(np.max(np.abs(board.astype(np.float64) - candidate))),
        "candidate_sha256": hashlib.sha256(candidate.astype("<f4").tobytes()).hexdigest(),
        "board_sha256": hashlib.sha256(args.board.read_bytes()).hexdigest(),
        "selected_token": token,
        "selected_score_bits": int(scores[token].view(np.uint32)),
        "output_crc": reference.output_crc32(token, scores[token]),
    }
    (args.output_dir / "reduction_diagnosis.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if summary["adjacent_exact_elements"] == board.size else 1


if __name__ == "__main__":
    raise SystemExit(main())
