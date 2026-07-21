#!/usr/bin/env python3
"""Run one real Qwen trace through the module-16 TCP integration path."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from module16_lm_head_hls.net.cpu_client import LmHeadClient
from module16_lm_head_hls.net.fpga_server_emulator import (
    LmHeadBoardEmulator,
    start_loopback_server,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--weight",
        type=Path,
        default=REPO_ROOT / "artifacts" / "model.embed_tokens.weight.fp16.npy",
    )
    parser.add_argument(
        "--fixture-root",
        type=Path,
        default=REPO_ROOT / "artifacts" / "module16_hls_fixtures",
    )
    parser.add_argument("--step", type=int, default=0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    weight = np.load(args.weight, mmap_mode="r", allow_pickle=False)
    fixture = args.fixture_root / f"step_{args.step:02d}"
    hidden = np.fromfile(fixture / "hidden.fp16.bin", dtype="<f2")
    history = np.fromfile(fixture / "history_bitmap.u32.bin", dtype="<u4")
    golden = np.fromfile(fixture / "golden_logits.fp16.bin", dtype="<f2")
    expected_token = int((fixture / "expected_token.txt").read_text().strip())

    emulator = LmHeadBoardEmulator(weight)
    _, server_thread, port = start_loopback_server(emulator)
    with LmHeadClient.connect("127.0.0.1", port, timeout=120.0) as client:
        ping = client.ping()
        result = client.run_token(
            hidden,
            history,
            vocab_size=weight.shape[0],
            repetition_penalty=1.1,
            enable_repetition_penalty=True,
            return_logits=True,
        )
    server_thread.join(timeout=5.0)

    assert result.raw_logits is not None
    delta = np.abs(result.raw_logits.astype(np.float32) - golden.astype(np.float32))
    top5_actual = np.argsort(-result.raw_logits.astype(np.float32), kind="stable")[:5]
    top5_golden = np.argsort(-golden.astype(np.float32), kind="stable")[:5]
    overlap = len(set(top5_actual.tolist()) & set(top5_golden.tolist()))
    passed = (
        ping.hidden_size == 896
        and ping.vocab_size == 151_936
        and result.token_id == expected_token
        and float(delta.max()) <= 0.02
        and overlap >= 4
    )
    print(
        f"TCP_LOOPBACK step={args.step} token={result.token_id} "
        f"expected={expected_token} max_abs={float(delta.max()):.8g} "
        f"top5_overlap={overlap}/5 status={'PASS' if passed else 'FAIL'}"
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
