"""RMSNorm backends used to replace the Orin-side PyTorch RMSNorm.

The first real FPGA hand-off uses BF16 tensors at the Ethernet boundary:

  Orin tensor -> BF16 wire payload -> FPGA/Vitis RMSNorm -> BF16 result -> Orin tensor

`local_bf16_rmsnorm` mirrors the HLS C model numerically and is useful for a
small demo without hardware. `EthernetRMSNormClient` keeps the earlier ZIP/JSON
RPC flow for a NumPy or Vivado AXI VIP endpoint. `RawEthernetRMSNormClient` is
the board-facing protocol for the AXU9EGB lwIP bare-metal server.
"""

from __future__ import annotations

import io
import json
import socket
import struct
import uuid
import zipfile
from typing import Any, Callable

import numpy as np
import torch


MAGIC = b"OFPGZP01"
HEADER_STRUCT = struct.Struct("<8sQQ")
RAW_REQUEST_MAGIC = b"OFRMSRQ1"
RAW_RESPONSE_MAGIC = b"OFRMSRP1"
RAW_REQUEST_HEADER_STRUCT = struct.Struct("<8sQIIIIII")
RAW_RESPONSE_HEADER_STRUCT = struct.Struct("<8sQIIII")
CHUNK_SIZE = 1024 * 1024
RMSNormBackend = Callable[[torch.Tensor, torch.Tensor, float], torch.Tensor]


def float32_to_bf16_uint16(array: np.ndarray) -> np.ndarray:
    values = np.ascontiguousarray(array.astype(np.float32, copy=False))
    bits = values.view(np.uint32)
    lsb = (bits >> 16) & 1
    rounded = bits + np.uint32(0x7FFF) + lsb
    return ((rounded >> 16).astype(np.uint16)).astype("<u2", copy=False)


def bf16_uint16_to_float32(array: np.ndarray) -> np.ndarray:
    words = np.ascontiguousarray(array.astype(np.uint16, copy=False))
    return (words.astype(np.uint32) << 16).view(np.float32)


def _tensor_to_float32_numpy(tensor: torch.Tensor) -> np.ndarray:
    return tensor.detach().to(device="cpu", dtype=torch.float32).contiguous().numpy()


def _torch_from_float32_numpy(array: np.ndarray, like: torch.Tensor) -> torch.Tensor:
    return torch.from_numpy(np.ascontiguousarray(array)).to(device=like.device, dtype=like.dtype)


def _float32_to_u32_bits(value: float) -> int:
    return int(np.asarray([value], dtype="<f4").view("<u4")[0])


def local_bf16_rmsnorm(hidden_states: torch.Tensor, weight: torch.Tensor, eps: float) -> torch.Tensor:
    """HLS-like RMSNorm simulation with BF16 input/output quantization."""

    hidden_shape = tuple(hidden_states.shape)
    hidden_np = _tensor_to_float32_numpy(hidden_states)
    weight_np = _tensor_to_float32_numpy(weight)

    hidden_bf16 = float32_to_bf16_uint16(hidden_np)
    weight_bf16 = float32_to_bf16_uint16(weight_np)
    hidden_f32 = bf16_uint16_to_float32(hidden_bf16).reshape(hidden_shape)
    weight_f32 = bf16_uint16_to_float32(weight_bf16).reshape(weight_np.shape)

    variance = np.mean(hidden_f32 * hidden_f32, axis=-1, keepdims=True)
    output_f32 = hidden_f32 * (1.0 / np.sqrt(variance + np.float32(eps))) * weight_f32
    output_bf16 = float32_to_bf16_uint16(output_f32)
    output = bf16_uint16_to_float32(output_bf16).reshape(hidden_shape)
    return _torch_from_float32_numpy(output, hidden_states)


def _send_all(sock: socket.socket, data: bytes | memoryview) -> None:
    view = memoryview(data)
    while view:
        sent = sock.send(view)
        if sent == 0:
            raise RuntimeError("socket connection broken")
        view = view[sent:]


def _recv_exact(sock: socket.socket, byte_count: int) -> bytes:
    chunks: list[bytes] = []
    remaining = byte_count
    while remaining:
        chunk = sock.recv(min(CHUNK_SIZE, remaining))
        if not chunk:
            raise RuntimeError("socket connection closed")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _make_zip_payload(files: dict[str, bytes], manifest: dict[str, Any]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, separators=(",", ":")))
        for arcname, data in files.items():
            archive.writestr(arcname, data)
    return buffer.getvalue()


def _send_bundle(sock: socket.socket, metadata: dict[str, Any], payload: bytes) -> None:
    metadata_raw = json.dumps(metadata, separators=(",", ":")).encode("utf-8")
    header = HEADER_STRUCT.pack(MAGIC, len(metadata_raw), len(payload))
    _send_all(sock, header)
    _send_all(sock, metadata_raw)
    _send_all(sock, payload)


def _receive_payload(sock: socket.socket) -> tuple[dict[str, Any], bytes]:
    header_raw = _recv_exact(sock, HEADER_STRUCT.size)
    magic, metadata_len, payload_len = HEADER_STRUCT.unpack(header_raw)
    if magic != MAGIC:
        raise RuntimeError(f"bad magic: {magic!r}")
    metadata = json.loads(_recv_exact(sock, int(metadata_len)).decode("utf-8"))
    payload = _recv_exact(sock, int(payload_len))
    return metadata, payload


def _read_zip_payload(payload: bytes) -> tuple[dict[str, Any], dict[str, bytes]]:
    with zipfile.ZipFile(io.BytesIO(payload), "r") as archive:
        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        files = {
            name: archive.read(name)
            for name in archive.namelist()
            if name != "manifest.json" and not name.endswith("/")
        }
    return manifest, files


class EthernetRMSNormClient:
    """Call an RMSNorm accelerator over TCP using raw BF16 payloads."""

    def __init__(self, host: str, port: int = 50052, timeout: float = 30.0) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout

    def __call__(self, hidden_states: torch.Tensor, weight: torch.Tensor, eps: float) -> torch.Tensor:
        hidden_shape = tuple(int(dim) for dim in hidden_states.shape)
        weight_shape = tuple(int(dim) for dim in weight.shape)
        hidden_bf16 = float32_to_bf16_uint16(_tensor_to_float32_numpy(hidden_states))
        weight_bf16 = float32_to_bf16_uint16(_tensor_to_float32_numpy(weight))
        request_id = uuid.uuid4().hex

        manifest = {
            "request_id": request_id,
            "module": "rmsnorm",
            "wire_dtype": "bf16_uint16_le",
            "compute_dtype": "float32",
            "shape": list(hidden_shape),
            "weight_shape": list(weight_shape),
            "eps": float(eps),
        }
        payload = _make_zip_payload(
            {
                "input_bf16.bin": hidden_bf16.reshape(-1).tobytes(),
                "weight_bf16.bin": weight_bf16.reshape(-1).tobytes(),
            },
            manifest,
        )
        metadata = {
            "request_id": request_id,
            "module": "rmsnorm",
            "payload_format": "zip+bf16",
        }

        with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
            sock.settimeout(self.timeout)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            _send_bundle(sock, metadata, payload)
            response_metadata, response_payload = _receive_payload(sock)

        if response_metadata.get("status") != "ok":
            raise RuntimeError(f"RMSNorm RPC server error: {response_metadata.get('error', response_metadata)}")
        if response_metadata.get("request_id") != request_id:
            raise RuntimeError(
                f"response request_id mismatch: {response_metadata.get('request_id')} != {request_id}"
            )
        response_manifest, response_files = _read_zip_payload(response_payload)
        if response_manifest.get("shape") != list(hidden_shape):
            raise RuntimeError(f"response shape mismatch: {response_manifest.get('shape')} != {hidden_shape}")
        output_raw = response_files.get("output_bf16.bin")
        if output_raw is None:
            raise RuntimeError("response is missing output_bf16.bin")

        output_words = np.frombuffer(output_raw, dtype="<u2")
        expected_count = int(np.prod(hidden_shape))
        if output_words.size != expected_count:
            raise RuntimeError(f"output element count mismatch: {output_words.size} != {expected_count}")
        output = bf16_uint16_to_float32(output_words).reshape(hidden_shape)
        return _torch_from_float32_numpy(output, hidden_states)


class RawEthernetRMSNormClient:
    """Call the AXU9EGB lwIP RMSNorm server with a compact BF16 TCP frame."""

    def __init__(self, host: str, port: int = 50052, timeout: float = 30.0) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.last_hw_time_us: int | None = None
        self.last_total_time_us: int | None = None

    def __call__(self, hidden_states: torch.Tensor, weight: torch.Tensor, eps: float) -> torch.Tensor:
        hidden_shape = tuple(int(dim) for dim in hidden_states.shape)
        if not hidden_shape:
            raise ValueError("hidden_states must have at least one dimension")

        hidden_size = hidden_shape[-1]
        element_count = int(np.prod(hidden_shape))
        if hidden_size <= 0 or element_count % hidden_size != 0:
            raise ValueError(f"invalid RMSNorm shape: {hidden_shape}")

        weight_count = int(np.prod(tuple(int(dim) for dim in weight.shape)))
        if weight_count != hidden_size:
            raise ValueError(f"weight element count {weight_count} does not match hidden_size {hidden_size}")

        row_count = element_count // hidden_size
        hidden_bf16 = float32_to_bf16_uint16(_tensor_to_float32_numpy(hidden_states)).reshape(-1)
        weight_bf16 = float32_to_bf16_uint16(_tensor_to_float32_numpy(weight)).reshape(-1)
        input_payload = hidden_bf16.astype("<u2", copy=False).tobytes()
        weight_payload = weight_bf16.astype("<u2", copy=False).tobytes()
        request_id = uuid.uuid4().int & 0xFFFFFFFFFFFFFFFF
        request_header = RAW_REQUEST_HEADER_STRUCT.pack(
            RAW_REQUEST_MAGIC,
            request_id,
            row_count,
            hidden_size,
            _float32_to_u32_bits(eps),
            len(input_payload),
            len(weight_payload),
            0,
        )

        with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
            sock.settimeout(self.timeout)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            _send_all(sock, request_header)
            _send_all(sock, input_payload)
            _send_all(sock, weight_payload)
            response_header_raw = _recv_exact(sock, RAW_RESPONSE_HEADER_STRUCT.size)
            magic, response_id, status, output_bytes, hw_time_us, total_time_us = RAW_RESPONSE_HEADER_STRUCT.unpack(
                response_header_raw
            )
            if magic != RAW_RESPONSE_MAGIC:
                raise RuntimeError(f"bad raw response magic: {magic!r}")
            if response_id != request_id:
                raise RuntimeError(f"raw response request_id mismatch: {response_id} != {request_id}")
            response_payload = _recv_exact(sock, int(output_bytes))

        self.last_hw_time_us = int(hw_time_us)
        self.last_total_time_us = int(total_time_us)

        if status != 0:
            message = response_payload.decode("utf-8", errors="replace") if response_payload else f"status {status}"
            raise RuntimeError(f"raw RMSNorm server error: {message}")

        expected_output_bytes = element_count * np.dtype("<u2").itemsize
        if output_bytes != expected_output_bytes:
            raise RuntimeError(f"raw output byte count mismatch: {output_bytes} != {expected_output_bytes}")

        output_words = np.frombuffer(response_payload, dtype="<u2")
        output = bf16_uint16_to_float32(output_words).reshape(hidden_shape)
        return _torch_from_float32_numpy(output, hidden_states)


def make_rmsnorm_backend(
    name: str,
    host: str | None = None,
    port: int = 50052,
    timeout: float = 30.0,
) -> RMSNormBackend | None:
    if name == "torch":
        return None
    if name == "local-bf16":
        return local_bf16_rmsnorm
    if name == "ethernet":
        if not host:
            raise ValueError("--rmsnorm-host is required for ethernet RMSNorm backend")
        return EthernetRMSNormClient(host=host, port=port, timeout=timeout)
    if name == "raw-ethernet":
        if not host:
            raise ValueError("--rmsnorm-host is required for raw-ethernet RMSNorm backend")
        return RawEthernetRMSNormClient(host=host, port=port, timeout=timeout)
    raise ValueError(f"unknown RMSNorm backend: {name}")
