"""CPU-side client for the module-16 binary TCP protocol."""

from __future__ import annotations

import socket
from dataclasses import dataclass
from typing import Callable

import numpy as np

from .fpga_server_emulator import STATUS_OK
from .lmh_protocol import (
    Flags,
    LOAD_PREFIX,
    Opcode,
    PING_RESULT,
    RESULT_PREFIX,
    RUN_PREFIX,
    ProtocolError,
    recv_frame,
    response_opcode,
    send_frame,
)


@dataclass(frozen=True)
class PingResult:
    hidden_size: int
    vocab_size: int
    weight_bytes: int


@dataclass(frozen=True)
class TokenResult:
    token_id: int
    score: float
    raw_logits: np.ndarray | None


class LmHeadClient:
    def __init__(self, stream: socket.socket):
        self.stream = stream
        self._next_request_id = 1

    @classmethod
    def connect(cls, host: str, port: int, *, timeout: float = 30.0) -> "LmHeadClient":
        return cls(socket.create_connection((host, port), timeout=timeout))

    def close(self) -> None:
        self.stream.close()

    def __enter__(self) -> "LmHeadClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _exchange(self, opcode: Opcode, flags: int = 0, payload: bytes = b"") -> bytes:
        request_id = self._next_request_id
        self._next_request_id += 1
        send_frame(self.stream, opcode, request_id, flags, payload)
        frame = recv_frame(self.stream)
        if frame.opcode == Opcode.ERROR:
            raise ProtocolError(frame.payload.decode("utf-8", errors="replace"))
        if frame.request_id != request_id or frame.opcode != response_opcode(opcode):
            raise ProtocolError("response opcode or request_id does not match request")
        return frame.payload

    def ping(self) -> PingResult:
        payload = self._exchange(Opcode.PING)
        if len(payload) != PING_RESULT.size:
            raise ProtocolError("invalid PING response length")
        return PingResult(*PING_RESULT.unpack(payload))

    def load_weight(
        self,
        weight: np.ndarray,
        *,
        chunk_bytes: int = 4 << 20,
        progress: Callable[[int, int], None] | None = None,
    ) -> None:
        if chunk_bytes <= 0:
            raise ValueError("chunk_bytes must be positive")
        weight = np.asarray(weight)
        if weight.dtype != np.dtype("<f2") or not weight.flags.c_contiguous:
            weight = np.ascontiguousarray(weight, dtype="<f2")
        if weight.ndim != 2:
            raise ValueError("weight must have shape [vocab_size, hidden_size]")
        vocab_size, hidden_size = weight.shape
        raw = memoryview(weight).cast("B")
        total = len(raw)
        for offset in range(0, total, chunk_bytes):
            end = min(offset + chunk_bytes, total)
            flags = Flags.NONE
            if offset == 0:
                flags |= Flags.FIRST_CHUNK
            if end == total:
                flags |= Flags.LAST_CHUNK
            prefix = LOAD_PREFIX.pack(total, hidden_size, vocab_size, offset)
            response = self._exchange(
                Opcode.LOAD_WEIGHT, int(flags), prefix + raw[offset:end].tobytes()
            )
            status, _, _, _ = RESULT_PREFIX.unpack(response)
            if status != STATUS_OK:
                raise ProtocolError(f"LOAD_WEIGHT failed with status {status}")
            if progress is not None:
                progress(end, total)

    def run_token(
        self,
        hidden: np.ndarray,
        history_bitmap: np.ndarray,
        *,
        vocab_size: int,
        repetition_penalty: float = 1.1,
        enable_repetition_penalty: bool = True,
        return_logits: bool = False,
    ) -> TokenResult:
        hidden = np.ascontiguousarray(hidden, dtype="<f2").reshape(-1)
        history = np.ascontiguousarray(history_bitmap, dtype="<u4").reshape(-1)
        flags = Flags.NONE
        if enable_repetition_penalty:
            flags |= Flags.ENABLE_REPETITION_PENALTY
        if return_logits:
            flags |= Flags.WANT_LOGITS
        prefix = RUN_PREFIX.pack(
            hidden.size, vocab_size, repetition_penalty, history.size
        )
        response = self._exchange(
            Opcode.RUN_TOKEN,
            int(flags),
            prefix + hidden.tobytes() + history.tobytes(),
        )
        if len(response) < RESULT_PREFIX.size:
            raise ProtocolError("invalid RUN_TOKEN response length")
        status, token_id, score, logits_bytes = RESULT_PREFIX.unpack_from(response)
        if status != STATUS_OK:
            raise ProtocolError(f"RUN_TOKEN failed with status {status}")
        raw = response[RESULT_PREFIX.size :]
        if len(raw) != logits_bytes:
            raise ProtocolError("RUN_TOKEN logits byte count mismatch")
        logits = (
            np.frombuffer(raw, dtype="<f2").copy() if logits_bytes else None
        )
        return TokenResult(token_id, score, logits)
