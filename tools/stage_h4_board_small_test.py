#!/usr/bin/env python3
"""Run a hand-checkable 4x4 LM Head test on the real AXU9EGB board."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from module16_lm_head_hls.net.cpu_client import LmHeadClient, TokenResult
from module16_lm_head_hls.net.lmh_protocol import ProtocolError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="192.168.8.190")
    parser.add_argument("--port", type=int, default=19016)
    parser.add_argument("--timeout", type=float, default=30.0)
    return parser.parse_args()


def check_result(
    name: str,
    result: TokenResult,
    expected_token: int,
    expected_score: float,
    expected_logits: np.ndarray | None,
) -> dict[str, object]:
    token_ok = result.token_id == expected_token
    score_error = abs(result.score - expected_score)
    score_ok = score_error <= 1e-6
    if expected_logits is None:
        logits_ok = result.raw_logits is None
        max_abs = None
    else:
        logits_ok = (
            result.raw_logits is not None
            and result.raw_logits.shape == expected_logits.shape
        )
        max_abs = (
            float(
                np.max(
                    np.abs(
                        result.raw_logits.astype(np.float32)
                        - expected_logits.astype(np.float32)
                    )
                )
            )
            if logits_ok and result.raw_logits is not None
            else None
        )
        logits_ok = logits_ok and max_abs == 0.0
    passed = token_ok and score_ok and logits_ok
    record = {
        "name": name,
        "token": result.token_id,
        "expected_token": expected_token,
        "score": result.score,
        "expected_score": expected_score,
        "score_error": score_error,
        "logits_max_abs": max_abs,
        "status": "PASS" if passed else "FAIL",
    }
    print(json.dumps(record, sort_keys=True))
    return record


def main() -> int:
    args = parse_args()

    # For hidden=[1,0,0,0], raw logits are [10,6,-2,-3].  Marking token 0
    # as seen and applying penalty=2 changes its score from 10 to 5, so token
    # 1 becomes Top-1 with score 6.
    #
    # For hidden=[0,1,0,0], tokens 0 and 1 both score 5.  The HLS strict
    # comparison must preserve the smaller token ID 0.
    weight = np.asarray(
        [
            [10.0, 5.0, 0.0, 0.0],
            [6.0, 5.0, 0.0, 0.0],
            [-2.0, 1.0, 0.0, 0.0],
            [-3.0, 0.0, 0.0, 0.0],
        ],
        dtype="<f2",
    )
    hidden_policy = np.asarray([1.0, 0.0, 0.0, 0.0], dtype="<f2")
    hidden_tie = np.asarray([0.0, 1.0, 0.0, 0.0], dtype="<f2")
    history_token_0 = np.asarray([1], dtype="<u4")
    raw_policy = np.asarray([10.0, 6.0, -2.0, -3.0], dtype="<f2")
    raw_tie = np.asarray([5.0, 5.0, 1.0, 0.0], dtype="<f2")
    records: list[dict[str, object]] = []

    with LmHeadClient.connect(args.host, args.port, timeout=args.timeout) as client:
        ping_before = client.ping()
        print(
            "ping_before="
            + json.dumps(
                {
                    "hidden": ping_before.hidden_size,
                    "vocab": ping_before.vocab_size,
                    "weight_bytes": ping_before.weight_bytes,
                },
                sort_keys=True,
            )
        )

        # Eight-byte chunks force a four-frame upload for this 32-byte tensor.
        client.load_weight(weight, chunk_bytes=8)
        ping_after = client.ping()
        ping_ok = (
            ping_after.hidden_size == 4
            and ping_after.vocab_size == 4
            and ping_after.weight_bytes == 32
        )
        print(
            "ping_after="
            + json.dumps(
                {
                    "hidden": ping_after.hidden_size,
                    "vocab": ping_after.vocab_size,
                    "weight_bytes": ping_after.weight_bytes,
                    "status": "PASS" if ping_ok else "FAIL",
                },
                sort_keys=True,
            )
        )

        no_penalty = client.run_token(
            hidden_policy,
            history_token_0,
            vocab_size=4,
            repetition_penalty=2.0,
            enable_repetition_penalty=False,
            return_logits=True,
        )
        records.append(
            check_result(
                "raw_argmax_no_penalty",
                no_penalty,
                expected_token=0,
                expected_score=10.0,
                expected_logits=raw_policy,
            )
        )

        with_penalty = client.run_token(
            hidden_policy,
            history_token_0,
            vocab_size=4,
            repetition_penalty=2.0,
            enable_repetition_penalty=True,
            return_logits=True,
        )
        records.append(
            check_result(
                "penalty_changes_top1",
                with_penalty,
                expected_token=1,
                expected_score=6.0,
                expected_logits=raw_policy,
            )
        )

        tie = client.run_token(
            hidden_tie,
            history_token_0,
            vocab_size=4,
            repetition_penalty=2.0,
            enable_repetition_penalty=False,
            return_logits=True,
        )
        records.append(
            check_result(
                "tie_keeps_lower_token",
                tie,
                expected_token=0,
                expected_score=5.0,
                expected_logits=raw_tie,
            )
        )

        token_only = client.run_token(
            hidden_policy,
            history_token_0,
            vocab_size=4,
            repetition_penalty=2.0,
            enable_repetition_penalty=True,
            return_logits=False,
        )
        records.append(
            check_result(
                "token_only_response",
                token_only,
                expected_token=1,
                expected_score=6.0,
                expected_logits=None,
            )
        )

        dimension_error_ok = False
        try:
            client.run_token(
                np.asarray([1.0, 0.0, 0.0], dtype="<f2"),
                history_token_0,
                vocab_size=4,
                repetition_penalty=2.0,
                enable_repetition_penalty=True,
                return_logits=False,
            )
        except ProtocolError as error:
            dimension_error_ok = "dimensions do not match loaded weight" in str(error)
            print(
                "dimension_mismatch="
                + json.dumps(
                    {
                        "message": str(error),
                        "status": "PASS" if dimension_error_ok else "FAIL",
                    },
                    sort_keys=True,
                )
            )

        recovery_ping = client.ping()
        recovery_ok = (
            recovery_ping.hidden_size == 4
            and recovery_ping.vocab_size == 4
            and recovery_ping.weight_bytes == 32
        )
        print(
            "same_connection_recovery="
            + json.dumps(
                {"status": "PASS" if recovery_ok else "FAIL"},
                sort_keys=True,
            )
        )

    passed = (
        ping_ok
        and dimension_error_ok
        and recovery_ok
        and all(record["status"] == "PASS" for record in records)
    )
    print(f"STAGE_H4_BOARD_SMALL_TEST={'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
