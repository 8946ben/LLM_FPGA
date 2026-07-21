#!/usr/bin/env python3
"""Prepare compact raw trace inputs for the module-16 Vitis HLS testbench."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


VOCAB_SIZE = 151_936
HIDDEN_SIZE = 896
HISTORY_WORDS = VOCAB_SIZE // 32


def discover_step_dirs(trace_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in trace_dir.iterdir()
        if path.is_dir()
        and (path.name == "00_prefill_full_prompt" or "_decode_token_" in path.name)
    )


def build_history(token_ids: list[int]) -> np.ndarray:
    bitmap = np.zeros(HISTORY_WORDS, dtype="<u4")
    for token_id in set(token_ids):
        bitmap[token_id // 32] |= np.uint32(1 << (token_id % 32))
    return bitmap


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--trace-dir",
        type=Path,
        default=root / "qwen25_0p5b_instruct_full_generation_trace",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=root / "artifacts" / "module16_hls_fixtures",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metadata = json.loads((args.trace_dir / "metadata.json").read_text(encoding="utf-8"))
    generated_ids = [int(value) for value in metadata["generated_ids"]]
    history = [int(value) for value in metadata["input_ids"]]
    step_dirs = discover_step_dirs(args.trace_dir)
    if len(step_dirs) != len(generated_ids):
        raise ValueError("Step count and generated ID count differ")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, object]] = []
    for index, step_dir in enumerate(step_dirs):
        output = args.output_dir / f"step_{index:02d}"
        output.mkdir(parents=True, exist_ok=True)
        hidden_states = np.load(step_dir / "lm_head_input.npy", allow_pickle=False)
        hidden = np.ascontiguousarray(hidden_states[0, -1, :], dtype="<f2")
        logits = np.load(step_dir / "lm_head_vocab_logits.npy", allow_pickle=False)
        raw_logits = np.ascontiguousarray(logits.reshape(-1, VOCAB_SIZE)[-1], dtype="<f2")
        bitmap = build_history(history)
        hidden.tofile(output / "hidden.fp16.bin")
        raw_logits.tofile(output / "golden_logits.fp16.bin")
        bitmap.tofile(output / "history_bitmap.u32.bin")
        (output / "expected_token.txt").write_text(
            f"{generated_ids[index]}\n", encoding="ascii"
        )
        manifest.append(
            {
                "step": index,
                "name": step_dir.name,
                "expected_token": generated_ids[index],
                "directory": str(output),
            }
        )
        history.append(generated_ids[index])

    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"prepared {len(manifest)} HLS fixtures in {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
