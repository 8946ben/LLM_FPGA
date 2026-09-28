"""Stage F board smoke test for the LMH1 service.

2026-07-24 zb: exercises protocol framing without uploading the 260 MiB
weight or starting the long-running LM Head compute kernel.
"""

from __future__ import annotations

import argparse
import socket
import struct
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from module16_lm_head_hls.net.lmh_protocol import (  # noqa: E402
    Flags,
    HEADER,
    MAGIC,
    Opcode,
    PING_RESULT,
    RESULT_PREFIX,
    RUN_PREFIX,
    VERSION,
    recv_frame,
    response_opcode,
    send_frame,
)


HIDDEN_SIZE = 896
VOCAB_SIZE = 151_936
HISTORY_WORDS = 4_748
STATUS_NOT_READY = 1


def expect_ping(stream: socket.socket, request_id: int) -> tuple[int, int, int]:
    frame = recv_frame(stream)
    expected_opcode = response_opcode(Opcode.PING)
    if frame.opcode != expected_opcode or frame.request_id != request_id:
        raise AssertionError(
            f"PING response mismatch: opcode={frame.opcode:#x}, "
            f"request_id={frame.request_id}"
        )
    result = PING_RESULT.unpack(frame.payload)
    if result not in (
        (0, 0, 0),
        (HIDDEN_SIZE, VOCAB_SIZE, HIDDEN_SIZE * VOCAB_SIZE * 2),
    ):
        raise AssertionError(f"invalid PING payload: {result}")
    return result


def split_ping(stream: socket.socket, request_id: int) -> tuple[int, int, int]:
    # zlib.crc32(b"") is zero.
    frame = HEADER.pack(MAGIC, VERSION, Opcode.PING, request_id, 0, 0, 0)
    for piece in (frame[:3], frame[3:11], frame[11:]):
        stream.sendall(piece)
        time.sleep(0.02)
    return expect_ping(stream, request_id)


def test_reusable_connection(host: str, port: int, timeout: float) -> None:
    with socket.create_connection((host, port), timeout=timeout) as stream:
        stream.settimeout(timeout)
        first = split_ping(stream, 101)
        if first != (0, 0, 0):
            raise AssertionError(
                "board already reports a loaded weight; reset before Stage F smoke"
            )

        payload = (
            RUN_PREFIX.pack(HIDDEN_SIZE, VOCAB_SIZE, 1.1, HISTORY_WORDS)
            + bytes(HIDDEN_SIZE * 2)
            + bytes(HISTORY_WORDS * 4)
        )
        send_frame(
            stream,
            Opcode.RUN_TOKEN,
            102,
            int(Flags.ENABLE_REPETITION_PENALTY),
            payload,
        )
        frame = recv_frame(stream)
        if (
            frame.opcode != response_opcode(Opcode.RUN_TOKEN)
            or frame.request_id != 102
        ):
            raise AssertionError("RUN_TOKEN response opcode/request_id mismatch")
        status, token, score, logits_bytes = RESULT_PREFIX.unpack(frame.payload)
        if (status, token, score, logits_bytes) != (STATUS_NOT_READY, 0, 0.0, 0):
            raise AssertionError(
                "RUN_TOKEN before weight load did not return STATUS_NOT_READY"
            )

        send_frame(stream, Opcode.PING, 103)
        expect_ping(stream, 103)


def test_crc_recovery(host: str, port: int, timeout: float) -> None:
    with socket.create_connection((host, port), timeout=timeout) as stream:
        stream.settimeout(timeout)
        bad_ping = HEADER.pack(
            MAGIC, VERSION, Opcode.PING, 201, 0, 0, 0x12345678
        )
        stream.sendall(bad_ping)
        frame = recv_frame(stream)
        if frame.opcode != Opcode.ERROR or frame.request_id != 201:
            raise AssertionError("bad CRC did not return matching ERROR frame")
        if b"CRC32" not in frame.payload:
            raise AssertionError(f"unexpected CRC error message: {frame.payload!r}")

        send_frame(stream, Opcode.PING, 202)
        expect_ping(stream, 202)


def test_unknown_opcode(host: str, port: int, timeout: float) -> None:
    with socket.create_connection((host, port), timeout=timeout) as stream:
        stream.settimeout(timeout)
        header = HEADER.pack(MAGIC, VERSION, 0x1234, 301, 0, 0, 0)
        stream.sendall(header)
        frame = recv_frame(stream)
        if frame.opcode != Opcode.ERROR or frame.request_id != 301:
            raise AssertionError("unknown opcode did not return matching ERROR frame")
        if b"unknown" not in frame.payload.lower():
            raise AssertionError(
                f"unexpected unknown-opcode message: {frame.payload!r}"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="192.168.8.190")
    parser.add_argument("--port", type=int, default=19016)
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    test_reusable_connection(args.host, args.port, args.timeout)
    print("fragmented_header=PASS")
    print("run_before_weight_status=PASS")
    print("same_connection_multi_frame=PASS")

    test_crc_recovery(args.host, args.port, args.timeout)
    print("crc_error_and_recovery=PASS")

    test_unknown_opcode(args.host, args.port, args.timeout)
    print("unknown_opcode_error=PASS")
    print("STAGE_F_BOARD_SMOKE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
