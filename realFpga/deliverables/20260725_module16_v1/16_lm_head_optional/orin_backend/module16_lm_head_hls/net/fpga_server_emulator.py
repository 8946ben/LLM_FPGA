"""TCP board-service emulator for module-16 integration testing."""

from __future__ import annotations

import argparse
import socket
import threading
from pathlib import Path

import numpy as np

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


STATUS_OK = 0
STATUS_NOT_READY = 1
STATUS_BAD_REQUEST = 2


class LmHeadBoardEmulator:
    """Implements the future board daemon contract over a real TCP socket.

    NumPy is used only as the compute backend in this integration layer.  The
    synthesizable HLS datapath is verified separately by C simulation and RTL
    co-simulation.
    """

    def __init__(self, weight: np.ndarray | None = None, *, chunk_rows: int = 4096):
        self.weight = None if weight is None else np.asarray(weight)
        self.chunk_rows = chunk_rows
        self._upload: bytearray | None = None
        self._upload_shape: tuple[int, int] | None = None
        self._upload_next_offset = 0

    @property
    def ready(self) -> bool:
        return self.weight is not None

    def _send_error(self, stream: socket.socket, request_id: int, message: str) -> None:
        send_frame(stream, Opcode.ERROR, request_id, payload=message.encode("utf-8"))

    def _handle_ping(self, stream: socket.socket, request_id: int) -> None:
        if self.weight is None:
            hidden_size = vocab_size = weight_bytes = 0
        else:
            vocab_size, hidden_size = self.weight.shape
            weight_bytes = int(self.weight.size * self.weight.dtype.itemsize)
        payload = PING_RESULT.pack(hidden_size, vocab_size, weight_bytes)
        send_frame(stream, response_opcode(Opcode.PING), request_id, payload=payload)

    def _handle_load(
        self, stream: socket.socket, request_id: int, flags: int, payload: bytes
    ) -> None:
        if len(payload) < LOAD_PREFIX.size:
            raise ProtocolError("LOAD_WEIGHT payload is shorter than its prefix")
        total_bytes, hidden_size, vocab_size, offset = LOAD_PREFIX.unpack_from(payload)
        chunk = payload[LOAD_PREFIX.size :]
        if total_bytes != hidden_size * vocab_size * 2:
            raise ProtocolError("LOAD_WEIGHT dimensions do not match FP16 byte count")
        if flags & Flags.FIRST_CHUNK:
            self._upload = bytearray(total_bytes)
            self._upload_shape = (vocab_size, hidden_size)
            self._upload_next_offset = 0
        if self._upload is None or self._upload_shape != (vocab_size, hidden_size):
            raise ProtocolError("LOAD_WEIGHT chunk arrived before FIRST_CHUNK")
        if offset != self._upload_next_offset:
            raise ProtocolError(
                f"LOAD_WEIGHT expected offset {self._upload_next_offset}, got {offset}"
            )
        if offset + len(chunk) > total_bytes:
            raise ProtocolError("LOAD_WEIGHT chunk exceeds the declared tensor")
        self._upload[offset : offset + len(chunk)] = chunk
        self._upload_next_offset += len(chunk)
        if flags & Flags.LAST_CHUNK:
            if offset + len(chunk) != total_bytes:
                raise ProtocolError("LAST_CHUNK does not end at total_bytes")
            self.weight = np.frombuffer(self._upload, dtype="<f2").reshape(
                self._upload_shape
            )
        send_frame(
            stream,
            response_opcode(Opcode.LOAD_WEIGHT),
            request_id,
            payload=RESULT_PREFIX.pack(STATUS_OK, 0, 0.0, 0),
        )

    def _compute(self, hidden: np.ndarray) -> np.ndarray:
        assert self.weight is not None
        logits_fp32 = np.empty(self.weight.shape[0], dtype=np.float32)
        hidden_fp32 = hidden.astype(np.float32, copy=False)
        for start in range(0, self.weight.shape[0], self.chunk_rows):
            stop = min(start + self.chunk_rows, self.weight.shape[0])
            logits_fp32[start:stop] = (
                self.weight[start:stop].astype(np.float32, copy=False) @ hidden_fp32
            )
        # This conversion is architectural: policy and argmax consume FP16.
        return logits_fp32.astype("<f2")

    def _handle_run(
        self, stream: socket.socket, request_id: int, flags: int, payload: bytes
    ) -> None:
        if self.weight is None:
            result = RESULT_PREFIX.pack(STATUS_NOT_READY, 0, 0.0, 0)
            send_frame(stream, response_opcode(Opcode.RUN_TOKEN), request_id, payload=result)
            return
        if len(payload) < RUN_PREFIX.size:
            raise ProtocolError("RUN_TOKEN payload is shorter than its prefix")
        hidden_size, vocab_size, penalty, history_words = RUN_PREFIX.unpack_from(payload)
        if flags & Flags.ENABLE_REPETITION_PENALTY:
            expected_history_words = (vocab_size + 31) // 32
            if history_words != expected_history_words:
                raise ProtocolError(
                    "RUN_TOKEN history bitmap does not cover the vocabulary"
                )
        expected = RUN_PREFIX.size + hidden_size * 2 + history_words * 4
        if len(payload) != expected:
            raise ProtocolError("RUN_TOKEN payload length does not match dimensions")
        if self.weight.shape != (vocab_size, hidden_size):
            raise ProtocolError("RUN_TOKEN dimensions do not match loaded weight")
        hidden_start = RUN_PREFIX.size
        history_start = hidden_start + hidden_size * 2
        hidden = np.frombuffer(
            payload, dtype="<f2", count=hidden_size, offset=hidden_start
        )
        history = np.frombuffer(
            payload, dtype="<u4", count=history_words, offset=history_start
        )
        raw_logits = self._compute(hidden)
        scores = raw_logits.astype(np.float32)
        if flags & Flags.ENABLE_REPETITION_PENALTY:
            for word_index, word_value in enumerate(history):
                word = int(word_value)
                while word:
                    bit = (word & -word).bit_length() - 1
                    token_id = word_index * 32 + bit
                    if token_id < vocab_size:
                        score = scores[token_id]
                        scores[token_id] = score * penalty if score < 0 else score / penalty
                    word &= word - 1
        token = int(np.argmax(scores))
        score = float(scores[token])
        logits_bytes = raw_logits.tobytes() if flags & Flags.WANT_LOGITS else b""
        result = RESULT_PREFIX.pack(STATUS_OK, token, score, len(logits_bytes))
        send_frame(
            stream,
            response_opcode(Opcode.RUN_TOKEN),
            request_id,
            payload=result + logits_bytes,
        )

    def serve_connection(self, stream: socket.socket) -> None:
        with stream:
            while True:
                try:
                    frame = recv_frame(stream)
                except EOFError:
                    return
                except ProtocolError as error:
                    self._send_error(stream, 0, str(error))
                    return
                try:
                    if frame.opcode == Opcode.PING:
                        self._handle_ping(stream, frame.request_id)
                    elif frame.opcode == Opcode.LOAD_WEIGHT:
                        self._handle_load(
                            stream, frame.request_id, frame.flags, frame.payload
                        )
                    elif frame.opcode == Opcode.RUN_TOKEN:
                        self._handle_run(
                            stream, frame.request_id, frame.flags, frame.payload
                        )
                    else:
                        raise ProtocolError(f"unknown opcode {frame.opcode}")
                except (ProtocolError, ValueError) as error:
                    self._send_error(stream, frame.request_id, str(error))


def start_loopback_server(
    emulator: LmHeadBoardEmulator,
) -> tuple[socket.socket, threading.Thread, int]:
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    port = listener.getsockname()[1]

    def accept_once() -> None:
        try:
            connection, _ = listener.accept()
            emulator.serve_connection(connection)
        finally:
            listener.close()

    thread = threading.Thread(target=accept_once, daemon=True)
    thread.start()
    return listener, thread, port


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--weight", type=Path)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=19016)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    weight = np.load(args.weight, mmap_mode="r") if args.weight else None
    emulator = LmHeadBoardEmulator(weight)
    with socket.create_server((args.host, args.port), reuse_port=False) as listener:
        print(f"module16 board emulator listening on {args.host}:{args.port}")
        while True:
            connection, address = listener.accept()
            print(f"client connected: {address[0]}:{address[1]}")
            emulator.serve_connection(connection)


if __name__ == "__main__":
    raise SystemExit(main())
