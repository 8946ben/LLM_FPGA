#!/usr/bin/env python3
"""Compare a board FP32 logits dump against the golden trace."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


def read_fp32(path: Path) -> tuple[float, ...]:
    data = path.read_bytes()
    if len(data) % 4:
        raise ValueError(f"{path}: byte size {len(data)} is not a multiple of 4")
    return struct.unpack(f"<{len(data) // 4}f", data)


def float_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def ordered_bits(value: float) -> int:
    bits = float_bits(value)
    return 0x80000000 - bits if bits & 0x80000000 else 0x80000000 + bits


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentile(sorted_values: list[int], fraction: float) -> int:
    return sorted_values[min(int(len(sorted_values) * fraction), len(sorted_values) - 1)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("board", type=Path)
    parser.add_argument("golden", type=Path)
    parser.add_argument("--processed", type=Path)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    board = read_fp32(args.board)
    golden = read_fp32(args.golden)
    if len(board) != len(golden):
        raise ValueError(f"length mismatch: board={len(board)}, golden={len(golden)}")

    abs_errors = [abs(actual - expected) for actual, expected in zip(board, golden)]
    ulps = [abs(ordered_bits(actual) - ordered_bits(expected)) for actual, expected in zip(board, golden)]
    sorted_ulps = sorted(ulps)
    exact_count = sum(float_bits(actual) == float_bits(expected) for actual, expected in zip(board, golden))
    board_argmax = max(range(len(board)), key=board.__getitem__)
    golden_argmax = max(range(len(golden)), key=golden.__getitem__)
    board_top10 = sorted(range(len(board)), key=board.__getitem__, reverse=True)[:10]

    result = {
        "element_count": len(board),
        "exact_count": exact_count,
        "different_count": len(board) - exact_count,
        "exact_fraction": exact_count / len(board),
        "absolute_error": {
            "mean": sum(abs_errors) / len(abs_errors),
            "max": max(abs_errors),
            "count_le_1e-6": sum(error <= 1e-6 for error in abs_errors),
        },
        "ulp_error": {
            "mean": sum(ulps) / len(ulps),
            "max": max(ulps),
            "p50": percentile(sorted_ulps, 0.50),
            "p90": percentile(sorted_ulps, 0.90),
            "p99": percentile(sorted_ulps, 0.99),
            "counts_0_to_10": {str(value): ulps.count(value) for value in range(11)},
            "count_le_1": sum(error <= 1 for error in ulps),
            "count_le_4": sum(error <= 4 for error in ulps),
        },
        "board": {
            "path": str(args.board.resolve()),
            "sha256": sha256(args.board),
            "argmax_token": board_argmax,
            "argmax_score": board[board_argmax],
            "argmax_score_bits": float_bits(board[board_argmax]),
        },
        "golden": {
            "path": str(args.golden.resolve()),
            "sha256": sha256(args.golden),
            "argmax_token": golden_argmax,
            "argmax_score": golden[golden_argmax],
            "argmax_score_bits": float_bits(golden[golden_argmax]),
        },
        "board_top10": [
            {
                "token": token,
                "board_score": board[token],
                "golden_score": golden[token],
                "ulp_error": ulps[token],
            }
            for token in board_top10
        ],
        "largest_ulp_samples": [
            {
                "token": token,
                "board_score": board[token],
                "golden_score": golden[token],
                "absolute_error": abs_errors[token],
                "ulp_error": ulps[token],
            }
            for token in sorted(range(len(board)), key=ulps.__getitem__, reverse=True)[:10]
        ],
    }

    if args.processed:
        processed = read_fp32(args.processed)
        processed_argmax = max(range(len(processed)), key=processed.__getitem__)
        result["golden_processed"] = {
            "path": str(args.processed.resolve()),
            "sha256": sha256(args.processed),
            "argmax_token": processed_argmax,
            "argmax_score": processed[processed_argmax],
            "argmax_score_bits": float_bits(processed[processed_argmax]),
        }

    output = json.dumps(result, ensure_ascii=False, indent=2)
    print(output)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(output + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
