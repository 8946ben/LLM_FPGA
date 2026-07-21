#!/usr/bin/env python3
"""Export tied Qwen2.5 embedding/LM-Head weight from safetensors to .npy.

This reader intentionally uses only Python and NumPy, so it also works in the
minimal FPGA verification environment without torch or the safetensors package.
"""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path

import numpy as np


TENSOR_NAME = "model.embed_tokens.weight"
EXPECTED_SHAPE = (151_936, 896)


def read_header(path: Path) -> tuple[dict, int]:
    with path.open("rb") as handle:
        length_bytes = handle.read(8)
        if len(length_bytes) != 8:
            raise ValueError(f"Invalid safetensors header in {path}")
        header_length = struct.unpack("<Q", length_bytes)[0]
        header = json.loads(handle.read(header_length).decode("utf-8"))
    return header, 8 + header_length


def find_tensor_file(model_path: Path, tensor_name: str) -> Path:
    if model_path.is_file():
        return model_path
    if not model_path.is_dir():
        raise FileNotFoundError(model_path)

    index_path = model_path / "model.safetensors.index.json"
    if index_path.is_file():
        index = json.loads(index_path.read_text(encoding="utf-8"))
        filename = index.get("weight_map", {}).get(tensor_name)
        if filename is None:
            raise KeyError(f"{tensor_name!r} is not present in {index_path}")
        return model_path / filename

    candidates = sorted(model_path.glob("*.safetensors"))
    for candidate in candidates:
        header, _ = read_header(candidate)
        if tensor_name in header:
            return candidate
    raise FileNotFoundError(
        f"Could not find {tensor_name!r} in safetensors files under {model_path}"
    )


def bf16_to_float32(raw: np.ndarray) -> np.ndarray:
    bits = raw.astype(np.uint32) << np.uint32(16)
    return bits.view(np.float32)


def read_tensor(path: Path, tensor_name: str) -> np.ndarray:
    header, data_start = read_header(path)
    if tensor_name not in header:
        raise KeyError(f"{tensor_name!r} is not present in {path}")
    info = header[tensor_name]
    shape = tuple(int(value) for value in info["shape"])
    start, stop = (int(value) for value in info["data_offsets"])
    dtype_name = info["dtype"]
    dtype_map = {
        "F16": np.dtype("<f2"),
        "F32": np.dtype("<f4"),
        "F64": np.dtype("<f8"),
        "I8": np.dtype("i1"),
        "U8": np.dtype("u1"),
        "I16": np.dtype("<i2"),
        "I32": np.dtype("<i4"),
        "I64": np.dtype("<i8"),
    }
    source_dtype = np.dtype("<u2") if dtype_name == "BF16" else dtype_map.get(dtype_name)
    if source_dtype is None:
        raise ValueError(f"Unsupported safetensors dtype {dtype_name!r}")

    count = int(np.prod(shape, dtype=np.int64))
    expected_bytes = count * source_dtype.itemsize
    if stop - start != expected_bytes:
        raise ValueError(
            f"Tensor byte count mismatch: header={stop - start}, expected={expected_bytes}"
        )
    raw = np.memmap(
        path,
        mode="r",
        dtype=source_dtype,
        offset=data_start + start,
        shape=(count,),
    )
    values = bf16_to_float32(raw) if dtype_name == "BF16" else np.asarray(raw)
    return values.reshape(shape)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export tied Qwen2.5 LM Head weight to a NumPy array."
    )
    parser.add_argument(
        "model_path",
        type=Path,
        help="Model directory, model.safetensors, or one safetensors shard.",
    )
    parser.add_argument("output", type=Path, help="Output .npy path.")
    parser.add_argument(
        "--dtype",
        choices=("float16", "float32"),
        default="float16",
        help="Export dtype; float16 matches the recorded model execution.",
    )
    parser.add_argument("--tensor-name", default=TENSOR_NAME)
    parser.add_argument(
        "--allow-other-shape",
        action="store_true",
        help="Permit a shape other than Qwen2.5-0.5B [151936, 896].",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = find_tensor_file(args.model_path, args.tensor_name)
    tensor = read_tensor(source, args.tensor_name)
    if not args.allow_other_shape and tensor.shape != EXPECTED_SHAPE:
        raise ValueError(f"Expected shape {EXPECTED_SHAPE}, got {tensor.shape}")
    output_dtype = np.float16 if args.dtype == "float16" else np.float32
    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.save(args.output, tensor.astype(output_dtype, copy=False), allow_pickle=False)
    print(
        f"exported tensor={args.tensor_name} source={source} output={args.output} "
        f"shape={tensor.shape} dtype={np.dtype(output_dtype).name}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
