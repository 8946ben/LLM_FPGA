#!/usr/bin/env python3
"""CPU reference and golden-trace validator for Qwen2.5 module 16.

The module has two deliberately separate responsibilities:

1. LM Head: project the last hidden state from H=896 to V=151936 logits.
2. Token selection: apply the configured logits processors and select argmax.

Keeping these paths separate makes it possible to identify whether a mismatch is
caused by matrix multiplication or by generation policy.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np


DEFAULT_TRACE_DIR = (
    Path(__file__).resolve().parents[1]
    / "qwen25_0p5b_instruct_full_generation_trace"
)
EXPECTED_HIDDEN_SIZE = 896
EXPECTED_VOCAB_SIZE = 151_936


@dataclass(frozen=True)
class StepFiles:
    index: int
    name: str
    input_path: Path
    logits_path: Path
    generation_scores_path: Path


@dataclass(frozen=True)
class ErrorMetrics:
    max_abs_error: float
    mean_abs_error: float
    cosine_similarity: float


def discover_steps(trace_dir: Path) -> list[StepFiles]:
    """Return trace steps in generation order and verify required files exist."""

    step_dirs = sorted(
        path
        for path in trace_dir.iterdir()
        if path.is_dir()
        and (path.name == "00_prefill_full_prompt" or "_decode_token_" in path.name)
    )
    score_dir = trace_dir / "generation_token_vocab_logits"
    steps: list[StepFiles] = []
    for index, step_dir in enumerate(step_dirs):
        score_name = (
            "prefill_next_token_vocab_logits.npy"
            if index == 0
            else f"decode_step_{index:04d}_next_token_vocab_logits.npy"
        )
        files = StepFiles(
            index=index,
            name=step_dir.name,
            input_path=step_dir / "lm_head_input.npy",
            logits_path=step_dir / "lm_head_vocab_logits.npy",
            generation_scores_path=score_dir / score_name,
        )
        for required in (
            files.input_path,
            files.logits_path,
            files.generation_scores_path,
        ):
            if not required.is_file():
                raise FileNotFoundError(required)
        steps.append(files)

    if not steps:
        raise ValueError(f"No LM Head trace steps found in {trace_dir}")
    return steps


def last_hidden_state(hidden_states: np.ndarray) -> np.ndarray:
    """Select the final sequence position and return shape [hidden_size]."""

    if hidden_states.ndim == 3:
        if hidden_states.shape[0] != 1:
            raise ValueError(
                f"Stage-1 reference supports batch=1, got {hidden_states.shape}"
            )
        return hidden_states[0, -1, :]
    if hidden_states.ndim == 2:
        if hidden_states.shape[0] != 1:
            raise ValueError(
                f"Expected [1, hidden_size] for a 2-D input, got {hidden_states.shape}"
            )
        return hidden_states[0]
    if hidden_states.ndim == 1:
        return hidden_states
    raise ValueError(f"Unsupported hidden-state shape: {hidden_states.shape}")


def lm_head_chunked(
    hidden: np.ndarray,
    weight: np.ndarray,
    *,
    vocab_chunk_size: int = 4096,
) -> np.ndarray:
    """Compute W @ h using FP32 accumulation and bounded temporary memory.

    `weight` must use Hugging Face layout [vocab_size, hidden_size]. The output
    remains FP32 so callers can compare it both before and after casting to the
    trace dtype.
    """

    hidden = np.asarray(hidden)
    weight = np.asarray(weight)
    if hidden.ndim != 1:
        raise ValueError(f"Expected a 1-D hidden vector, got {hidden.shape}")
    if weight.ndim != 2 or weight.shape[1] != hidden.shape[0]:
        raise ValueError(
            "Weight must have shape [vocab_size, hidden_size]; "
            f"got weight={weight.shape}, hidden={hidden.shape}"
        )
    if vocab_chunk_size <= 0:
        raise ValueError("vocab_chunk_size must be positive")

    hidden_fp32 = hidden.astype(np.float32, copy=False)
    logits = np.empty(weight.shape[0], dtype=np.float32)
    for start in range(0, weight.shape[0], vocab_chunk_size):
        stop = min(start + vocab_chunk_size, weight.shape[0])
        weight_chunk = weight[start:stop].astype(np.float32, copy=False)
        logits[start:stop] = weight_chunk @ hidden_fp32
    return logits


def apply_repetition_penalty(
    logits: np.ndarray,
    previous_token_ids: Iterable[int],
    penalty: float,
) -> np.ndarray:
    """Apply the Hugging Face repetition penalty to unique previous token IDs."""

    if penalty <= 0:
        raise ValueError("repetition penalty must be greater than zero")
    scores = np.asarray(logits, dtype=np.float32).copy()
    token_ids = np.fromiter(set(int(v) for v in previous_token_ids), dtype=np.int64)
    if token_ids.size == 0 or penalty == 1.0:
        return scores
    if token_ids.min() < 0 or token_ids.max() >= scores.shape[-1]:
        raise ValueError("previous_token_ids contains an ID outside the vocabulary")

    selected = scores[token_ids]
    scores[token_ids] = np.where(
        selected < 0,
        selected * np.float32(penalty),
        selected / np.float32(penalty),
    )
    return scores


def greedy_argmax(scores: np.ndarray) -> int:
    """Return the lowest token ID among equal maximum scores, like torch.argmax."""

    flat = np.asarray(scores).reshape(-1)
    if flat.size == 0:
        raise ValueError("Cannot select argmax from an empty tensor")
    return int(np.argmax(flat))


def error_metrics(actual: np.ndarray, expected: np.ndarray) -> ErrorMetrics:
    actual64 = np.asarray(actual, dtype=np.float64).reshape(-1)
    expected64 = np.asarray(expected, dtype=np.float64).reshape(-1)
    if actual64.shape != expected64.shape:
        raise ValueError(f"Shape mismatch: {actual64.shape} != {expected64.shape}")
    delta = np.abs(actual64 - expected64)
    denominator = np.linalg.norm(actual64) * np.linalg.norm(expected64)
    cosine = float(np.dot(actual64, expected64) / denominator) if denominator else 1.0
    return ErrorMetrics(
        max_abs_error=float(delta.max(initial=0.0)),
        mean_abs_error=float(delta.mean()) if delta.size else 0.0,
        cosine_similarity=cosine,
    )


def top_k_ids(scores: np.ndarray, k: int) -> list[int]:
    flat = np.asarray(scores).reshape(-1)
    k = min(k, flat.size)
    # Stable sorting preserves the lowest token ID when scores are equal.
    return np.argsort(-flat, kind="stable")[:k].astype(int).tolist()


def load_weight(path: Path) -> np.ndarray:
    if path.suffix.lower() != ".npy":
        raise ValueError(
            "CPU reference expects an exported .npy weight. Use "
            "tools/export_lm_head_weight.py for a model directory or safetensors file."
        )
    weight = np.load(path, mmap_mode="r", allow_pickle=False)
    if weight.ndim != 2:
        raise ValueError(f"Expected a 2-D LM Head weight, got {weight.shape}")
    return weight


def validate_trace(
    trace_dir: Path,
    *,
    repetition_penalty: float,
    weight: np.ndarray | None,
    vocab_chunk_size: int,
    output_dir: Path | None,
    selected_steps: set[int] | None,
) -> bool:
    metadata = json.loads((trace_dir / "metadata.json").read_text(encoding="utf-8"))
    input_ids = [int(value) for value in metadata["input_ids"]]
    generated_ids = [int(value) for value in metadata["generated_ids"]]
    steps = discover_steps(trace_dir)
    if len(steps) != len(generated_ids):
        raise ValueError(
            f"Trace has {len(steps)} steps but metadata has {len(generated_ids)} IDs"
        )

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)

    print(
        f"trace={trace_dir} steps={len(steps)} "
        f"repetition_penalty={repetition_penalty:g}"
    )
    generation_scores_passed = True
    token_selection_passed = True
    matmul_passed: bool | None = None if weight is None else True
    previous_ids = list(input_ids)

    for step in steps:
        expected_id = generated_ids[step.index]
        if selected_steps is not None and step.index not in selected_steps:
            previous_ids.append(expected_id)
            continue

        hidden_states = np.load(step.input_path, allow_pickle=False)
        raw_logits_array = np.load(step.logits_path, allow_pickle=False)
        golden_scores_array = np.load(step.generation_scores_path, allow_pickle=False)
        hidden = last_hidden_state(hidden_states)
        raw_logits = raw_logits_array.reshape(-1, raw_logits_array.shape[-1])[-1]
        golden_scores = golden_scores_array.reshape(
            -1, golden_scores_array.shape[-1]
        )[-1].astype(np.float32, copy=False)

        if hidden.shape != (EXPECTED_HIDDEN_SIZE,):
            raise ValueError(f"{step.name}: unexpected hidden shape {hidden.shape}")
        if raw_logits.shape != (EXPECTED_VOCAB_SIZE,):
            raise ValueError(f"{step.name}: unexpected logits shape {raw_logits.shape}")

        processed_scores = apply_repetition_penalty(
            raw_logits, previous_ids, repetition_penalty
        )
        policy_metrics = error_metrics(processed_scores, golden_scores)
        raw_token = greedy_argmax(raw_logits)
        processed_token = greedy_argmax(processed_scores)
        golden_token = greedy_argmax(golden_scores)
        policy_ok = processed_token == golden_token == expected_id
        # The saved generation scores should be reproduced to normal FP32 rounding.
        scores_ok = policy_metrics.max_abs_error <= 2e-6

        computed_summary = "weight=not-provided"
        compute_ok = True
        if weight is not None:
            computed = lm_head_chunked(
                hidden, weight, vocab_chunk_size=vocab_chunk_size
            )
            # The recorder stores FP16 logits. Compare after the same output cast,
            # while retaining FP32 results for inspection.
            computed_trace_dtype = computed.astype(raw_logits.dtype)
            compute_metrics = error_metrics(computed_trace_dtype, raw_logits)
            # Token selection consumes the LM Head output dtype. Argmax on the
            # wider accumulator can differ when two values round to the same
            # FP16 logit; torch.argmax then resolves that tie by lowest ID.
            accumulator_top1 = greedy_argmax(computed)
            compute_top1 = greedy_argmax(computed_trace_dtype)
            compute_top5_overlap = len(
                set(top_k_ids(computed_trace_dtype, 5))
                & set(top_k_ids(raw_logits, 5))
            )
            compute_ok = (
                compute_top1 == raw_token
                and compute_metrics.cosine_similarity >= 0.999
                and compute_top5_overlap >= 4
            )
            computed_summary = (
                f"matmul_top1={compute_top1} accumulator_top1={accumulator_top1} "
                f"matmul_max_abs="
                f"{compute_metrics.max_abs_error:.6g} matmul_cos="
                f"{compute_metrics.cosine_similarity:.9f} "
                f"top5_overlap={compute_top5_overlap}/5"
            )
            if output_dir is not None:
                np.save(
                    output_dir / f"{step.index:02d}_computed_logits_fp32.npy",
                    computed,
                )

        generation_scores_passed &= scores_ok
        token_selection_passed &= policy_ok
        if matmul_passed is not None:
            matmul_passed &= compute_ok
        step_ok = policy_ok and scores_ok and compute_ok
        print(
            f"[{('PASS' if step_ok else 'FAIL')}] step={step.index} "
            f"name={step.name} input={tuple(hidden_states.shape)} "
            f"raw_top1={raw_token} processed_top1={processed_token} "
            f"golden_top1={golden_token} expected={expected_id} "
            f"policy_max_abs={policy_metrics.max_abs_error:.6g} "
            f"{computed_summary}"
        )
        previous_ids.append(expected_id)

    matmul_status = (
        "NOT_RUN" if matmul_passed is None else ("PASS" if matmul_passed else "FAIL")
    )
    print("summary:")
    print(f"  lm_head_matmul={matmul_status}")
    print(
        "  generation_policy_scores="
        f"{'PASS' if generation_scores_passed else 'FAIL'}"
    )
    print(
        f"  token_selection={'PASS' if token_selection_passed else 'FAIL'}"
    )
    completed = matmul_passed is not None
    all_passed = (
        completed
        and bool(matmul_passed)
        and generation_scores_passed
        and token_selection_passed
    )
    if all_passed:
        overall_status = "PASS"
    elif not completed and generation_scores_passed and token_selection_passed:
        overall_status = "PARTIAL_PASS"
    else:
        overall_status = "FAIL"
    print(f"overall={overall_status}")
    return all_passed if completed else generation_scores_passed and token_selection_passed


def parse_step_selection(values: list[int] | None) -> set[int] | None:
    return None if values is None else set(values)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Qwen2.5 module-16 LM Head and greedy token selection."
    )
    parser.add_argument("--trace-dir", type=Path, default=DEFAULT_TRACE_DIR)
    parser.add_argument(
        "--weight",
        type=Path,
        help="Exported model.embed_tokens.weight .npy file; optional for trace-only checks.",
    )
    parser.add_argument("--repetition-penalty", type=float, default=1.1)
    parser.add_argument("--vocab-chunk-size", type=int, default=4096)
    parser.add_argument(
        "--step",
        type=int,
        action="append",
        help="Validate only this zero-based generation step; may be repeated.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optionally save computed FP32 logits when --weight is supplied.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    weight = load_weight(args.weight) if args.weight is not None else None
    if weight is not None and weight.shape != (
        EXPECTED_VOCAB_SIZE,
        EXPECTED_HIDDEN_SIZE,
    ):
        raise ValueError(
            "Qwen2.5-0.5B LM Head weight must have shape "
            f"({EXPECTED_VOCAB_SIZE}, {EXPECTED_HIDDEN_SIZE}), got {weight.shape}"
        )
    passed = validate_trace(
        args.trace_dir,
        repetition_penalty=args.repetition_penalty,
        weight=weight,
        vocab_chunk_size=args.vocab_chunk_size,
        output_dir=args.output_dir,
        selected_steps=parse_step_selection(args.step),
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
