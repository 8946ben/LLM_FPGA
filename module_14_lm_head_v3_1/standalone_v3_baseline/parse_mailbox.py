#!/usr/bin/env python3
"""Decode an M14 V2 mailbox dump and optionally append a board JSON record."""

from __future__ import annotations

import argparse
import json
import pathlib
import struct
from board_profile import load_profile

MAGIC = 0x4D313456
VERSION = 2
DONE = 0x444F4E45
FAILED = 0x4641494C


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def u64(data: bytes, offset: int) -> int:
    return struct.unpack_from("<Q", data, offset)[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mailbox", type=pathlib.Path)
    parser.add_argument("--step", default="manual")
    parser.add_argument("--json-output", type=pathlib.Path)
    parser.add_argument("--append", action="store_true")
    parser.add_argument("--package-dir", type=pathlib.Path,
                        help="Hash-checked package clock/build profile; default is legacy 100 MHz")
    args = parser.parse_args()
    profile = load_profile(args.package_dir)

    data = args.mailbox.read_bytes()
    if len(data) != 256:
        raise SystemExit(f"mailbox length {len(data)} != 256")
    if u32(data, 0) != MAGIC or u32(data, 4) != VERSION:
        raise SystemExit("mailbox magic/version mismatch")

    state = u32(data, 8)
    score_bits = u32(data, 120)
    timer_hz = u64(data, 200)
    record = {
        "step": args.step,
        "source_run": str(args.mailbox.parent.resolve()),
        "state": f"0x{state:08x}",
        "repeat_count": u32(data, 12),
        "run_mode": u32(data, 48),
        "write_logits": u32(data, 52),
        "enable_penalty": u32(data, 56),
        "job_id": u32(data, 68),
        "expected_status": u32(data, 100),
        "driver_status": u32(data, 112),
        "selected_token": u32(data, 116),
        "selected_score_bits": score_bits,
        "selected_score": struct.unpack("<f", struct.pack("<I", score_bits))[0],
        "output_crc": u32(data, 124),
        "wall_ticks": u64(data, 128),
        "perf_cycles_total": u64(data, 136),
        "weight_wait_cycles": u64(data, 144),
        "dot_active_cycles": u64(data, 152),
        "perf_cycles_compute": u64(data, 160),
        "perf_read_beats": u64(data, 168),
        "perf_write_beats": u64(data, 176),
        "weight_read_beats_128": u64(data, 184),
        "logits_write_beats_128": u64(data, 192),
        "timer_counts_per_second": timer_hz,
        "vocab_rows_done": u32(data, 208),
        "history_read_words": u32(data, 212),
        "logits_written": u32(data, 216),
        "processed_rows": u32(data, 220),
        "build_config": u32(data, 224),
        "capabilities": u32(data, 228),
        "result_job_id": u32(data, 232),
        "status_code": u32(data, 236),
    }
    if timer_hz:
        record["wall_seconds"] = record["wall_ticks"] / timer_hz
    record["ip_clock_hz"] = profile["ip_clock_hz"]
    record["clock_basis"] = profile["clock_basis"]
    record["expected_build_config"] = profile["build_config"]
    record["profile_source"] = profile["profile_source"]
    record["build_profile_match"] = record["build_config"] == profile["build_config"]
    record["ip_seconds"] = record["perf_cycles_total"] / profile["ip_clock_hz"]
    if profile["ip_clock_hz"] == 100_000_000:
        record["ip_seconds_100mhz"] = record["ip_seconds"]

    print(json.dumps(record, ensure_ascii=False, indent=2))
    if args.json_output:
        if args.append and args.json_output.exists():
            document = json.loads(args.json_output.read_text(encoding="utf-8"))
            records = document.setdefault("records", [])
        else:
            document = {"format": "M14_LM_HEAD_V2_BOARD_RESULTS", "records": []}
            records = document["records"]
        records.append(record)
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(document, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    if not record["build_profile_match"]:
        print("MAILBOX_RESULT=FAIL build_config/package profile mismatch")
        return 1
    if state == DONE and record["driver_status"] == 0:
        print("MAILBOX_RESULT=PASS")
        return 0
    if state == FAILED:
        print("MAILBOX_RESULT=FAIL")
        return 1
    print("MAILBOX_RESULT=INCOMPLETE")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
