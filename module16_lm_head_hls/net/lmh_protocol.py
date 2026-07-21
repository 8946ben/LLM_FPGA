"""Binary TCP protocol shared by the module-16 host and board service.

The transport deliberately knows nothing about Xilinx APIs.  A simulation
service and a future FPGA daemon can therefore implement exactly the same wire
contract.
"""

from __future__ import annotations

import socket
import struct
import zlib
from dataclasses import dataclass
from enum import IntEnum, IntFlag


MAGIC = b"LMH1"
VERSION = 1
HEADER = struct.Struct("<4sHHIIII")
LOAD_PREFIX = struct.Struct("<QIIQ")
RUN_PREFIX = struct.Struct("<IIfI")
RESULT_PREFIX = struct.Struct("<IIfI")
PING_RESULT = struct.Struct("<IIQ")


class Opcode(IntEnum):
    LOAD_WEIGHT = 1
    RUN_TOKEN = 2
    PING = 3
    RESPONSE_BIT = 0x8000
    ERROR = 0xFFFF


class Flags(IntFlag):
    NONE = 0
    ENABLE_REPETITION_PENALTY = 1 << 0
    WANT_LOGITS = 1 << 1
    FIRST_CHUNK = 1 << 2
    LAST_CHUNK = 1 << 3


class ProtocolError(RuntimeError):
    pass


@dataclass(frozen=True)
class Frame:
    opcode: int
    request_id: int
    flags: int
    payload: bytes


def _recv_exact(stream: socket.socket, byte_count: int) -> bytes:
    chunks: list[bytes] = []
    remaining = byte_count
    while remaining:
        chunk = stream.recv(remaining)
        if not chunk:
            raise EOFError("TCP connection closed before the frame was complete")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def send_frame(
    stream: socket.socket,
    opcode: int,
    request_id: int,
    flags: int = 0,
    payload: bytes = b"",
) -> None:
    payload_crc = zlib.crc32(payload) & 0xFFFFFFFF
    header = HEADER.pack(
        MAGIC,
        VERSION,
        int(opcode),
        request_id,
        int(flags),
        len(payload),
        payload_crc,
    )
    stream.sendall(header)
    if payload:
        stream.sendall(payload)


def recv_frame(stream: socket.socket, *, max_payload_bytes: int = 512 << 20) -> Frame:
    header_bytes = _recv_exact(stream, HEADER.size)
    magic, version, opcode, request_id, flags, payload_bytes, expected_crc = (
        HEADER.unpack(header_bytes)
    )
    if magic != MAGIC:
        raise ProtocolError(f"bad magic {magic!r}")
    if version != VERSION:
        raise ProtocolError(f"unsupported protocol version {version}")
    if payload_bytes > max_payload_bytes:
        raise ProtocolError(f"payload too large: {payload_bytes} bytes")
    payload = _recv_exact(stream, payload_bytes)
    actual_crc = zlib.crc32(payload) & 0xFFFFFFFF
    if actual_crc != expected_crc:
        raise ProtocolError(
            f"CRC32 mismatch: received 0x{actual_crc:08x}, "
            f"expected 0x{expected_crc:08x}"
        )
    return Frame(opcode, request_id, flags, payload)


def response_opcode(request_opcode: int) -> int:
    return int(request_opcode) | int(Opcode.RESPONSE_BIT)

