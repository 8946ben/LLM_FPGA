#!/usr/bin/env python3
"""Run one module-16 trace fixture over LMH1 TCP.

The same host program can target either the NumPy board emulator or the
AXU9EGB lwIP service.  It intentionally consumes the compact fixture files
instead of starting Qwen inference on the host.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

BACKEND_ROOT = Path(__file__).resolve().parents[1]
MODULE_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from module16_lm_head_hls.net.cpu_client import LmHeadClient
from module16_lm_head_hls.net.fpga_server_emulator import (
    LmHeadBoardEmulator,
    start_loopback_server,
)


DEFAULT_HIDDEN_SIZE = 896
DEFAULT_VOCAB_SIZE = 151_936


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send a prepared Qwen2.5 module-16 trace step over LMH1 TCP."
    )
    parser.add_argument("--host", default="192.168.8.190")
    parser.add_argument("--port", type=int, default=19016)
    parser.add_argument(
        "--weight",
        type=Path,
        default=MODULE_ROOT / "artifacts" / "model.embed_tokens.weight.fp16.npy",
    )
    parser.add_argument(
        "--fixture-root",
        type=Path,
        default=MODULE_ROOT / "artifacts" / "module16_hls_fixtures",
    )
    parser.add_argument(
        "--trace-root",
        type=Path,
        default=MODULE_ROOT / "qwen25_0p5b_instruct_full_generation_trace",
        help="Used to validate model.generate processed scores.",
    )
    parser.add_argument("--step", type=int, default=0)
    parser.add_argument(
        "--vocab-limit",
        type=int,
        default=None,
        help=(
            "Use only the first N vocabulary rows. This supports progressive "
            "real-board validation without creating a second weight file."
        ),
    )
    parser.add_argument(
        "--load-weight",
        action="store_true",
        help="Upload the selected FP16 weight (full or sliced) before RUN_TOKEN.",
    )
    parser.add_argument("--chunk-bytes", type=int, default=1 << 20)
    parser.add_argument(
        "--return-logits",
        action="store_true",
        help="Request raw FP16 logits and perform numerical comparisons.",
    )
    parser.add_argument("--repetition-penalty", type=float, default=1.1)
    penalty_group = parser.add_mutually_exclusive_group()
    penalty_group.add_argument(
        "--enable-repetition-penalty",
        action="store_true",
        help=(
            "Enable history-based repetition penalty. It is disabled by "
            "default; use this flag to reproduce model.generate scores."
        ),
    )
    penalty_group.add_argument(
        "--disable-repetition-penalty",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--raw-logits-atol", type=float, default=0.02)
    parser.add_argument("--processed-atol", type=float, default=0.02)
    parser.add_argument(
        "--start-emulator",
        action="store_true",
        help="Start a blank local NumPy emulator and connect through TCP.",
    )
    parser.add_argument(
        "--inspect-only",
        action="store_true",
        help="Validate inputs and print the selected slice without using TCP.",
    )
    return parser.parse_args()


def require_file(path: Path) -> Path:
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"required file does not exist: {path}")
    return path


def read_fixture(
    fixture_root: Path, step: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray, int, Path]:
    if step < 0:
        raise ValueError("step must be non-negative")
    fixture = (fixture_root / f"step_{step:02d}").resolve()
    hidden = np.fromfile(require_file(fixture / "hidden.fp16.bin"), dtype="<f2")
    history = np.fromfile(
        require_file(fixture / "history_bitmap.u32.bin"), dtype="<u4"
    )
    golden = np.fromfile(
        require_file(fixture / "golden_logits.fp16.bin"), dtype="<f2"
    )
    expected_token = int(
        require_file(fixture / "expected_token.txt").read_text(
            encoding="ascii"
        ).strip()
    )
    return hidden, history, golden, expected_token, fixture


def processed_score_path(trace_root: Path, step: int) -> Path:
    score_dir = trace_root / "generation_token_vocab_logits"
    name = (
        "prefill_next_token_vocab_logits.npy"
        if step == 0
        else f"decode_step_{step:04d}_next_token_vocab_logits.npy"
    )
    return require_file(score_dir / name)


def repeated_token_ids(history: np.ndarray, vocab_size: int) -> np.ndarray:
    token_ids: list[int] = []
    for word_index, word_value in enumerate(history):
        word = int(word_value)
        while word:
            least_bit = word & -word
            token_id = word_index * 32 + least_bit.bit_length() - 1
            if token_id < vocab_size:
                token_ids.append(token_id)
            word ^= least_bit
    return np.asarray(token_ids, dtype=np.int64)


def apply_repetition_penalty(
    raw_logits: np.ndarray,
    history: np.ndarray,
    penalty: float,
    enabled: bool,
) -> np.ndarray:
    scores = raw_logits.astype(np.float32)
    if not enabled:
        return scores
    if penalty <= 0.0:
        raise ValueError("repetition_penalty must be greater than zero")
    token_ids = repeated_token_ids(history, scores.size)
    selected = scores[token_ids]
    scores[token_ids] = np.where(
        selected < 0.0, selected * penalty, selected / penalty
    )
    return scores


def top_token_ids(values: np.ndarray, count: int = 5) -> np.ndarray:
    return np.argsort(-values.astype(np.float32), kind="stable")[:count]


def main() -> int:
    args = parse_args()
    started_at = time.perf_counter()
    weight_path = require_file(args.weight)
    full_weight = np.load(weight_path, mmap_mode="r", allow_pickle=False)
    if full_weight.ndim != 2 or full_weight.dtype != np.dtype("float16"):
        raise ValueError(
            "weight must be a two-dimensional FP16 array, got "
            f"{full_weight.shape} {full_weight.dtype}"
        )
    full_vocab_size, hidden_size = (int(value) for value in full_weight.shape)
    if args.vocab_limit is None:
        vocab_size = full_vocab_size
    else:
        vocab_size = int(args.vocab_limit)
        if vocab_size <= 0 or vocab_size > full_vocab_size:
            raise ValueError(
                f"vocab-limit must be in [1, {full_vocab_size}], got {vocab_size}"
            )
    weight = full_weight[:vocab_size]

    hidden, full_history, full_golden, fixture_expected_token, fixture = read_fixture(
        args.fixture_root, args.step
    )
    expected_history_words = (vocab_size + 31) // 32
    history = full_history[:expected_history_words].copy()
    if vocab_size % 32:
        history[-1] &= np.uint32((1 << (vocab_size % 32)) - 1)
    golden = full_golden[:vocab_size]

    if hidden.size != hidden_size:
        raise ValueError(
            f"hidden has {hidden.size} elements, expected {hidden_size}"
        )
    full_expected_history_words = (full_vocab_size + 31) // 32
    if full_history.size != full_expected_history_words:
        raise ValueError(
            f"full history bitmap has {full_history.size} words, "
            f"expected {full_expected_history_words}"
        )
    if full_golden.size != full_vocab_size:
        raise ValueError(
            f"full golden logits has {full_golden.size} elements, "
            f"expected {full_vocab_size}"
        )
    if (hidden_size, full_vocab_size) != (
        DEFAULT_HIDDEN_SIZE,
        DEFAULT_VOCAB_SIZE,
    ):
        print(
            "warning: source dimensions differ from Qwen2.5-0.5B defaults: "
            f"hidden={hidden_size} vocab={full_vocab_size}"
        )

    host = args.host
    port = args.port
    server_thread = None
    if args.start_emulator:
        emulator = LmHeadBoardEmulator()
        _, server_thread, port = start_loopback_server(emulator)
        host = "127.0.0.1"
        print(f"emulator=STARTED endpoint={host}:{port} initial_weight=EMPTY")

    enabled_penalty = args.enable_repetition_penalty
    expected_scores = apply_repetition_penalty(
        golden,
        history,
        args.repetition_penalty,
        enabled_penalty,
    )
    expected_token = int(np.argmax(expected_scores))
    expected_top5 = top_token_ids(expected_scores).tolist()

    print(
        f"fixture={fixture} step={args.step} hidden={hidden.size} "
        f"history_words={history.size}/{full_history.size} "
        f"golden_logits={golden.size}/{full_golden.size}"
    )
    print(
        f"weight={weight_path} shape={weight.shape}/{full_weight.shape} "
        f"dtype={weight.dtype} bytes={weight.nbytes}/{full_weight.nbytes} "
        f"mmap={isinstance(full_weight, np.memmap)}"
    )
    print(
        f"slice_reference token={expected_token} top5={expected_top5} "
        f"score={float(expected_scores[expected_token])} "
        f"history_set_bits={repeated_token_ids(history, vocab_size).size} "
        f"fixture_expected_token={fixture_expected_token}"
    )
    print(
        f"repetition_penalty enabled={int(enabled_penalty)} "
        f"value={args.repetition_penalty}"
    )
    if args.inspect_only:
        print(
            f"MODULE16_TRACE_INSPECT step={args.step} vocab={vocab_size} "
            "status=PASS"
        )
        return 0

    upload_seconds = 0.0
    run_seconds = 0.0
    last_progress_bucket = -1

    def report_upload(done: int, total: int) -> None:
        nonlocal last_progress_bucket
        bucket = done // (32 << 20)
        if done == total or bucket != last_progress_bucket:
            last_progress_bucket = bucket
            print(
                f"weight_upload={done}/{total} "
                f"percent={100.0 * done / total:.1f}"
            )

    with LmHeadClient.connect(host, port, timeout=args.timeout) as client:
        ping_before = client.ping()
        print(
            f"ping_before hidden={ping_before.hidden_size} "
            f"vocab={ping_before.vocab_size} "
            f"weight_bytes={ping_before.weight_bytes}"
        )
        if args.load_weight:
            upload_started = time.perf_counter()
            client.load_weight(
                weight,
                chunk_bytes=args.chunk_bytes,
                progress=report_upload,
            )
            upload_seconds = time.perf_counter() - upload_started
            print(
                f"weight_upload_seconds={upload_seconds:.3f} "
                f"throughput_MiB_s={weight.nbytes / upload_seconds / (1 << 20):.3f}"
            )
        ping_after = client.ping()
        print(
            f"ping_after hidden={ping_after.hidden_size} "
            f"vocab={ping_after.vocab_size} "
            f"weight_bytes={ping_after.weight_bytes}"
        )
        expected_ping = (hidden_size, vocab_size, weight.nbytes)
        actual_ping = (
            ping_after.hidden_size,
            ping_after.vocab_size,
            ping_after.weight_bytes,
        )
        if actual_ping != expected_ping:
            raise RuntimeError(
                f"board is not ready for this weight: ping={actual_ping}, "
                f"expected={expected_ping}"
            )

        run_started = time.perf_counter()
        result = client.run_token(
            hidden,
            history,
            vocab_size=vocab_size,
            repetition_penalty=args.repetition_penalty,
            enable_repetition_penalty=enabled_penalty,
            return_logits=args.return_logits,
        )
        run_seconds = time.perf_counter() - run_started

    if server_thread is not None:
        server_thread.join(timeout=5.0)
        if server_thread.is_alive():
            raise RuntimeError("software emulator did not stop after client disconnect")

    checks: dict[str, bool] = {}
    checks["selected_token"] = result.token_id == expected_token
    metrics: dict[str, object] = {
        "selected_token": result.token_id,
        "expected_token": expected_token,
        "selected_score": result.score,
        "run_seconds": run_seconds,
        "repetition_penalty_enabled": enabled_penalty,
        "repetition_penalty": args.repetition_penalty,
    }

    if args.return_logits:
        if result.raw_logits is None:
            raise RuntimeError("WANT_LOGITS was set but the server returned no logits")
        raw_actual = result.raw_logits.astype(np.float32)
        raw_golden = golden.astype(np.float32)
        raw_delta = np.abs(raw_actual - raw_golden)
        raw_max_abs = float(raw_delta.max())
        raw_top5 = top_token_ids(raw_actual)
        golden_top5 = top_token_ids(raw_golden)
        raw_top5_overlap = len(
            set(raw_top5.tolist()) & set(golden_top5.tolist())
        )
        checks["raw_logits_atol"] = raw_max_abs <= args.raw_logits_atol
        checks["raw_top5"] = raw_top5_overlap == 5
        metrics.update(
            {
                "raw_max_abs": raw_max_abs,
                "raw_top5_actual": raw_top5.tolist(),
                "raw_top5_golden": golden_top5.tolist(),
                "raw_top5_overlap": raw_top5_overlap,
            }
        )

        processed_actual = apply_repetition_penalty(
            result.raw_logits,
            history,
            args.repetition_penalty,
            enabled_penalty,
        )
        host_selected_token = int(np.argmax(processed_actual))
        checks["server_vs_host_argmax"] = result.token_id == host_selected_token
        checks["server_score"] = (
            abs(result.score - float(processed_actual[host_selected_token]))
            <= args.processed_atol
        )
        metrics["host_selected_token"] = host_selected_token

        if enabled_penalty:
            reference_path = processed_score_path(args.trace_root, args.step)
            full_processed_reference = np.load(
                reference_path, allow_pickle=False
            ).reshape(-1)
            if full_processed_reference.size < vocab_size:
                raise ValueError(
                    "processed score reference is smaller than the selected "
                    "vocabulary"
                )
            processed_reference = full_processed_reference[:vocab_size]
            processed_delta = np.abs(
                processed_actual - processed_reference.astype(np.float32)
            )
            processed_max_abs = float(processed_delta.max())
            reference_top5 = top_token_ids(processed_reference)
            processed_top5 = top_token_ids(processed_actual)
            processed_top5_overlap = len(
                set(processed_top5.tolist()) & set(reference_top5.tolist())
            )
            checks["processed_scores_atol"] = (
                processed_max_abs <= args.processed_atol
            )
            checks["processed_top5"] = processed_top5_overlap == 5
            metrics.update(
                {
                    "processed_reference": str(reference_path),
                    "processed_max_abs": processed_max_abs,
                    "processed_top5_actual": processed_top5.tolist(),
                    "processed_top5_reference": reference_top5.tolist(),
                    "processed_top5_overlap": processed_top5_overlap,
                    "history_set_bits": int(
                        repeated_token_ids(history, vocab_size).size
                    ),
                }
            )

    passed = all(checks.values())
    metrics["upload_seconds"] = upload_seconds
    metrics["total_seconds"] = time.perf_counter() - started_at
    print("checks=" + json.dumps(checks, ensure_ascii=False, sort_keys=True))
    print("metrics=" + json.dumps(metrics, ensure_ascii=False, sort_keys=True))
    print(
        f"MODULE16_TRACE step={args.step} endpoint={host}:{port} "
        f"status={'PASS' if passed else 'FAIL'}"
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
