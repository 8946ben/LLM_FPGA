"""Check single-module board JSON results against the tracked V2 manifest."""

from __future__ import annotations

import argparse
import json
import statistics
import struct
from pathlib import Path


EXPECTED_ROWS = 151_936
EXPECTED_WEIGHT_BEATS = 17_016_832


def percentile_95(values: list[float]) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("no values")
    index = max(0, min(len(ordered) - 1, int(0.95 * len(ordered) + 0.999999) - 1))
    return ordered[index]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--clock-hz", type=float, default=100_000_000.0)
    parser.add_argument(
        "--require-score-bits",
        action="store_true",
        default=True,
        help="Compatibility option: exact score bits and CRC are always required.",
    )
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    board = json.loads(args.results.read_text(encoding="utf-8"))
    records = board["records"] if isinstance(board, dict) else board
    expected = {entry["step"]: entry for entry in manifest["trace"]}
    failures: list[str] = []
    production_seconds: list[float] = []
    accepted_steps: set[str] = set()

    for record in records:
        if record.get("excluded_from_acceptance"):
            print(f"SKIP: {record['step']}: {record.get('exclusion_reason', 'archived record')}")
            continue
        failures_before = len(failures)
        step = record["step"]
        golden = expected.get(step)
        if golden is None:
            failures.append(f"{step}: missing from manifest")
            continue
        if record.get("state") != "0x444f4e45" or record.get("driver_status") != 0:
            failures.append(f"{step}: mailbox did not complete successfully")
        if record.get("status_code") != 0:
            failures.append(f"{step}: status={record.get('status_code')}")
        if record.get("selected_token") != golden["selected_token"]:
            failures.append(
                f"{step}: token {record.get('selected_token')} != {golden['selected_token']}"
            )
        if args.require_score_bits:
            score_bits = golden.get("selected_score_bits")
            if score_bits is None:
                score_bits = struct.unpack("<I", struct.pack("<f", golden["selected_score"]))[0]
            if record.get("selected_score_bits") != score_bits:
                failures.append(f"{step}: selected_score_bits mismatch")
            if record.get("output_crc") != golden["output_crc"]:
                failures.append(
                    f"{step}: CRC {record.get('output_crc')} != {golden['output_crc']}"
                )
        if record.get("vocab_rows_done") != EXPECTED_ROWS:
            failures.append(f"{step}: bad vocab_rows_done")
        if record.get("weight_read_beats_128") != EXPECTED_WEIGHT_BEATS:
            failures.append(f"{step}: bad weight beat count")
        if record.get("processed_rows") != 1:
            failures.append(f"{step}: bad processed_rows")
        if record.get("write_logits") == 0:
            if record.get("logits_write_beats_128") != 0:
                failures.append(f"{step}: production job wrote logits")
            cycles = record.get("perf_cycles_total")
            if len(failures) == failures_before and isinstance(cycles, int) and cycles > 0:
                production_seconds.append(cycles / args.clock_hz)
        if len(failures) == failures_before:
            accepted_steps.add(step)

    missing_steps = sorted(set(expected) - accepted_steps)
    for step in missing_steps:
        failures.append(f"{step}: no board record")

    if production_seconds:
        print(
            "production latency: "
            f"median={statistics.median(production_seconds):.6f}s "
            f"p95={percentile_95(production_seconds):.6f}s "
            f"n={len(production_seconds)}"
        )
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        print(f"BOARD_RESULT_CHECK=FAIL count={len(failures)}")
        return 1
    print(f"BOARD_RESULT_CHECK=PASS records={len(records)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
