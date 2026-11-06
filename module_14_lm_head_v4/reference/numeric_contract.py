"""Bit-aware software reference for the M14 LM Head V2 numeric contract."""

from __future__ import annotations

import argparse
import json
import struct
import zlib
from pathlib import Path

import numpy as np


ABI_VERSION = 2
H_LANES = 8
ACC_INTERLEAVE = 16
PRODUCTION_HIDDEN_SIZE = 896
PRODUCTION_VOCAB_SIZE = 151_936
NUMERIC_IMPL = "bf16_rne_h8_interleave16_fp32_adjacent_tree_v2"


def float32_to_bf16_bits(values: np.ndarray) -> np.ndarray:
    """Convert FP32 to BF16 bits using round-to-nearest-even."""
    fp32 = np.asarray(values, dtype=np.float32)
    bits = fp32.view(np.uint32)
    exponent = bits & np.uint32(0x7F800000)
    fraction = bits & np.uint32(0x007FFFFF)
    special_nan = (exponent == np.uint32(0x7F800000)) & (fraction != 0)
    rounding_bias = np.uint32(0x00007FFF) + ((bits >> 16) & 1)
    rounded = bits + rounding_bias
    result = (rounded >> 16).astype(np.uint16)
    # Preserve NaN as a quiet NaN instead of allowing rounding to turn it into Inf.
    result = np.where(
        special_nan,
        ((bits >> 16) | np.uint32(0x0040)).astype(np.uint16),
        result,
    )
    return result


def bf16_bits_to_float32(values: np.ndarray) -> np.ndarray:
    bits = np.asarray(values, dtype=np.uint16).astype(np.uint32) << 16
    return bits.view(np.float32)


def _reduce_partials(partial: np.ndarray) -> np.ndarray:
    """Match the fixed reduction order used by lm_head_v2.cpp."""
    for width in (8, 4, 2, 1):
        partial[:, :, :width] = np.add(
            partial[:, :, :width],
            partial[:, :, width : 2 * width],
            dtype=np.float32,
        )
    # C++ sum01/sum23/sum45/sum67 pair adjacent lanes. A half-split
    # tree (0+4, 1+5, ...) changes FP32 rounding and is not bit-exact.
    lanes = partial[:, :, 0]
    pairs = np.add(lanes[:, 0::2], lanes[:, 1::2], dtype=np.float32)
    halves = np.add(pairs[:, 0::2], pairs[:, 1::2], dtype=np.float32)
    return np.add(halves[:, 0], halves[:, 1], dtype=np.float32)


def compute_raw_logits(
    hidden_bf16: np.ndarray,
    weight_bf16: np.ndarray,
    token_block: int = 1024,
) -> np.ndarray:
    """Compute FP32 raw logits with the H8/interleave16 hardware order."""
    hidden_bits = np.asarray(hidden_bf16, dtype=np.uint16).reshape(-1)
    weights = np.asarray(weight_bf16, dtype=np.uint16)
    if weights.ndim != 2:
        raise ValueError("weight_bf16 must have shape [vocab, hidden]")
    vocab_size, hidden_size = weights.shape
    if hidden_bits.size != hidden_size:
        raise ValueError("hidden and weight hidden dimensions differ")
    if hidden_size % H_LANES != 0:
        raise ValueError("hidden_size must be divisible by 8")
    if token_block <= 0:
        raise ValueError("token_block must be positive")

    hidden = bf16_bits_to_float32(hidden_bits).reshape(-1)
    words_per_row = hidden_size // H_LANES
    logits = np.empty(vocab_size, dtype=np.float32)

    for start in range(0, vocab_size, token_block):
        stop = min(start + token_block, vocab_size)
        block = bf16_bits_to_float32(weights[start:stop]).reshape(
            stop - start, words_per_row, H_LANES
        )
        partial = np.zeros(
            (stop - start, H_LANES, ACC_INTERLEAVE), dtype=np.float32
        )
        for word in range(words_per_row):
            slot = word & (ACC_INTERLEAVE - 1)
            product = np.multiply(
                block[:, word, :],
                hidden[word * H_LANES : (word + 1) * H_LANES],
                dtype=np.float32,
            )
            partial[:, :, slot] = np.add(
                partial[:, :, slot], product, dtype=np.float32
            )
        logits[start:stop] = _reduce_partials(partial)
    return logits


def bitmap_to_seen(history_words: np.ndarray, vocab_size: int) -> np.ndarray:
    words = np.asarray(history_words, dtype=np.uint32).reshape(-1)
    required = (vocab_size + 31) // 32
    if words.size < required:
        raise ValueError(f"history needs {required} uint32 words")
    token_ids = np.arange(vocab_size, dtype=np.uint32)
    return ((words[token_ids >> 5] >> (token_ids & 31)) & 1).astype(bool)


def apply_repetition_penalty(
    raw_logits: np.ndarray,
    history_words: np.ndarray,
    penalty: float,
) -> np.ndarray:
    if not np.isfinite(np.float32(penalty)) or penalty < 1.0:
        raise ValueError("penalty must be finite and >= 1")
    scores = np.asarray(raw_logits, dtype=np.float32).copy()
    seen = bitmap_to_seen(history_words, scores.size)
    negative = seen & (scores < np.float32(0.0))
    positive = seen & ~negative
    scores[negative] = np.multiply(
        scores[negative], np.float32(penalty), dtype=np.float32
    )
    scores[positive] = np.divide(
        scores[positive], np.float32(penalty), dtype=np.float32
    )
    return scores


def output_crc32(selected_token: int, selected_score: np.float32) -> int:
    payload = struct.pack(
        "<II",
        int(selected_token),
        int(np.asarray(selected_score, dtype=np.float32).view(np.uint32)),
    )
    return zlib.crc32(payload) & 0xFFFFFFFF


def run_reference(
    hidden_bf16: np.ndarray,
    weight_bf16: np.ndarray,
    history_words: np.ndarray | None = None,
    enable_penalty: bool = False,
    repetition_penalty: float = 1.0,
    token_block: int = 1024,
) -> dict[str, object]:
    raw = compute_raw_logits(hidden_bf16, weight_bf16, token_block=token_block)
    if not np.all(np.isfinite(raw)):
        raise FloatingPointError("raw logits contain NaN or Inf")
    if enable_penalty:
        if history_words is None:
            raise ValueError("history_words are required when penalty is enabled")
        scores = apply_repetition_penalty(raw, history_words, repetition_penalty)
    else:
        scores = raw.copy()
    # np.argmax returns the first maximum, matching the lower-token tie rule.
    token = int(np.argmax(scores))
    score = np.float32(scores[token])
    return {
        "raw_logits": raw,
        "processed_scores": scores,
        "selected_token": token,
        "selected_score": score,
        "output_crc": output_crc32(token, score),
    }


def _load_bf16(path: Path, shape: tuple[int, ...]) -> np.memmap:
    expected_bytes = int(np.prod(shape)) * 2
    if path.stat().st_size != expected_bytes:
        raise ValueError(
            f"{path} has {path.stat().st_size} bytes, expected {expected_bytes}"
        )
    return np.memmap(path, mode="r", dtype="<u2", shape=shape)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hidden", type=Path, required=True)
    parser.add_argument("--weight", type=Path, required=True)
    parser.add_argument("--history", type=Path)
    parser.add_argument("--enable-penalty", action="store_true")
    parser.add_argument("--penalty", type=float, default=1.1)
    parser.add_argument("--hidden-size", type=int, default=PRODUCTION_HIDDEN_SIZE)
    parser.add_argument("--vocab-size", type=int, default=PRODUCTION_VOCAB_SIZE)
    parser.add_argument("--token-block", type=int, default=1024)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    hidden = _load_bf16(args.hidden, (args.hidden_size,))
    weight = _load_bf16(args.weight, (args.vocab_size, args.hidden_size))
    history = None
    if args.enable_penalty:
        if args.history is None:
            parser.error("--history is required with --enable-penalty")
        history = np.fromfile(args.history, dtype="<u4")

    result = run_reference(
        hidden,
        weight,
        history,
        args.enable_penalty,
        args.penalty,
        args.token_block,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    np.asarray(result["raw_logits"], dtype="<f4").tofile(
        args.output_dir / "raw_logits.fp32.bin"
    )
    np.asarray(result["processed_scores"], dtype="<f4").tofile(
        args.output_dir / "processed_scores.fp32.bin"
    )
    summary = {
        "abi_version": ABI_VERSION,
        "hidden_size": args.hidden_size,
        "vocab_size": args.vocab_size,
        "enable_penalty": args.enable_penalty,
        "repetition_penalty": args.penalty,
        "selected_token": result["selected_token"],
        "selected_score": float(result["selected_score"]),
        "selected_score_bits": int(
            np.asarray(result["selected_score"], dtype=np.float32).view(np.uint32)
        ),
        "output_crc": result["output_crc"],
        "numeric_impl": NUMERIC_IMPL,
    }
    (args.output_dir / "result.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
