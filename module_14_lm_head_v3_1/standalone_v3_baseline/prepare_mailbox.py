#!/usr/bin/env python3
"""Create the 256-byte little-endian M14 V2 board-test mailbox."""

import argparse
import pathlib
import struct

MAGIC = 0x4D313456
VERSION = 2
DEFAULTS = {
    "hidden": 0x503A8000,
    "weight": 0x40000000,
    "history": 0x503A8700,
    "logits": 0x503AD140,
}


def integer(text: str) -> int:
    return int(text, 0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--hidden", type=integer, default=DEFAULTS["hidden"])
    parser.add_argument("--weight", type=integer, default=DEFAULTS["weight"])
    parser.add_argument("--history", type=integer, default=DEFAULTS["history"])
    parser.add_argument("--logits", type=integer, default=DEFAULTS["logits"])
    parser.add_argument("--run-mode", type=integer, choices=(0, 1), default=1)
    parser.add_argument("--write-logits", type=integer, choices=(0, 1), default=0)
    parser.add_argument("--enable-penalty", type=integer, choices=(0, 1), default=1)
    parser.add_argument("--penalty", type=float, default=1.1)
    parser.add_argument("--flags", type=integer, default=3)
    parser.add_argument("--job-id", type=integer, default=1)
    parser.add_argument("--expected-token", type=integer, required=True)
    parser.add_argument("--expected-crc", type=integer, default=0)
    parser.add_argument("--hidden-size", type=integer, default=896)
    parser.add_argument("--vocab-size", type=integer, default=151936)
    parser.add_argument("--valid-rows", type=integer, default=1)
    parser.add_argument("--abi-version", type=integer, default=2)
    parser.add_argument("--expected-status", type=integer, default=0)
    parser.add_argument("--bypass-host-validation", action="store_true")
    parser.add_argument("--repeat-count", type=integer, default=1)
    args = parser.parse_args()

    if not 1 <= args.repeat_count <= 1000:
        parser.error("--repeat-count must be in [1, 1000]")
    for name in ("hidden", "weight", "history", "logits"):
        if getattr(args, name) & 63:
            parser.error(f"--{name} must be 64-byte aligned")

    penalty_bits = struct.unpack("<I", struct.pack("<f", args.penalty))[0]
    prefix = struct.pack(
        "<IIIIQQQQIIIIIIIIIIIIIIII",
        MAGIC,
        VERSION,
        0,
        args.repeat_count,
        args.hidden,
        args.weight,
        args.history,
        args.logits,
        args.run_mode,
        args.write_logits,
        args.enable_penalty,
        penalty_bits,
        args.flags,
        args.job_id,
        args.expected_token,
        args.expected_crc,
        int(args.bypass_host_validation),
        args.hidden_size,
        args.vocab_size,
        args.valid_rows,
        args.abi_version,
        args.expected_status,
        0,
        0,
    )
    payload = prefix + bytes(256 - len(prefix))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(payload)
    print(f"MAILBOX_WRITE=PASS path={args.output} bytes={len(payload)}")


if __name__ == "__main__":
    main()
