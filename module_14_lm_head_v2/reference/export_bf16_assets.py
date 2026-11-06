"""Convert legacy FP16 LM Head assets into the ABI V2 BF16 byte layout."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
from pathlib import Path

import numpy as np

from lm_head_v2_ref import (
    NUMERIC_IMPL,
    PRODUCTION_HIDDEN_SIZE,
    PRODUCTION_VOCAB_SIZE,
    float32_to_bf16_bits,
    run_reference,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


TENSOR_NAME = "model.embed_tokens.weight"


def _read_safetensors_header(path: Path) -> tuple[dict[str, object], int]:
    with path.open("rb") as stream:
        header_bytes = stream.read(8)
        if len(header_bytes) != 8:
            raise ValueError(f"invalid safetensors header: {path}")
        header_size = struct.unpack("<Q", header_bytes)[0]
        header = json.loads(stream.read(header_size).decode("utf-8"))
    return header, 8 + header_size


def _find_safetensors(model_path: Path) -> Path:
    if model_path.is_file():
        return model_path
    index_path = model_path / "model.safetensors.index.json"
    if index_path.is_file():
        index = json.loads(index_path.read_text(encoding="utf-8"))
        filename = index["weight_map"].get(TENSOR_NAME)
        if filename is None:
            raise KeyError(f"{TENSOR_NAME} missing from {index_path}")
        return model_path / filename
    for candidate in sorted(model_path.glob("*.safetensors")):
        header, _ = _read_safetensors_header(candidate)
        if TENSOR_NAME in header:
            return candidate
    raise FileNotFoundError(f"cannot find {TENSOR_NAME} under {model_path}")


def copy_exact_bf16_weight(model_path: Path, destination: Path) -> dict[str, object]:
    source = _find_safetensors(model_path)
    header, data_start = _read_safetensors_header(source)
    info = header[TENSOR_NAME]
    shape = tuple(int(value) for value in info["shape"])
    if shape != (PRODUCTION_VOCAB_SIZE, PRODUCTION_HIDDEN_SIZE):
        raise ValueError(f"unexpected {TENSOR_NAME} shape: {shape}")
    if info["dtype"] != "BF16":
        raise ValueError(f"expected original BF16 tensor, got {info['dtype']}")
    start, stop = (int(value) for value in info["data_offsets"])
    expected_bytes = PRODUCTION_VOCAB_SIZE * PRODUCTION_HIDDEN_SIZE * 2
    if stop - start != expected_bytes:
        raise ValueError("safetensors byte count does not match V2 weight shape")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as input_stream, destination.open("wb") as output_stream:
        input_stream.seek(data_start + start)
        remaining = expected_bytes
        while remaining:
            chunk = input_stream.read(min(8 * 1024 * 1024, remaining))
            if not chunk:
                raise EOFError("safetensors ended inside embedding tensor")
            output_stream.write(chunk)
            remaining -= len(chunk)
    return {
        "source": str(source),
        "source_tensor": TENSOR_NAME,
        "source_dtype": "BF16",
        "exact_original_bf16": True,
    }


def convert_legacy_fp16_weight(
    source: Path, destination: Path, rows_per_chunk: int
) -> dict[str, object]:
    weight = np.load(source, mmap_mode="r")
    expected = (PRODUCTION_VOCAB_SIZE, PRODUCTION_HIDDEN_SIZE)
    if weight.shape != expected or weight.dtype != np.float16:
        raise ValueError(f"expected FP16 weight {expected}, got {weight.shape}/{weight.dtype}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    output = np.memmap(destination, mode="w+", dtype="<u2", shape=expected)
    for start in range(0, expected[0], rows_per_chunk):
        stop = min(start + rows_per_chunk, expected[0])
        output[start:stop] = float32_to_bf16_bits(
            np.asarray(weight[start:stop], dtype=np.float32)
        )
    output.flush()
    del output
    return {
        "source": str(source),
        "source_tensor": TENSOR_NAME,
        "source_dtype": "FP16_NPY",
        "exact_original_bf16": False,
    }


def convert_trace(
    fixture_root: Path,
    output_root: Path,
    weight_path: Path,
    generate_golden: bool,
    token_block: int,
) -> list[dict[str, object]]:
    weight = np.memmap(
        weight_path,
        mode="r",
        dtype="<u2",
        shape=(PRODUCTION_VOCAB_SIZE, PRODUCTION_HIDDEN_SIZE),
    )
    trace_entries: list[dict[str, object]] = []
    for source_dir in sorted(fixture_root.glob("step_*")):
        destination = output_root / source_dir.name
        destination.mkdir(parents=True, exist_ok=True)
        hidden_fp16 = np.fromfile(source_dir / "hidden.fp16.bin", dtype="<f2")
        if hidden_fp16.size != PRODUCTION_HIDDEN_SIZE:
            raise ValueError(f"bad hidden size in {source_dir}")
        hidden_bf16 = float32_to_bf16_bits(hidden_fp16.astype(np.float32))
        hidden_path = destination / "hidden.bf16.bin"
        hidden_bf16.astype("<u2").tofile(hidden_path)
        history_path = destination / "history_bitmap.u32.bin"
        shutil.copyfile(source_dir / "history_bitmap.u32.bin", history_path)
        history = np.fromfile(history_path, dtype="<u4")

        entry: dict[str, object] = {
            "step": source_dir.name,
            "hidden_sha256": sha256(hidden_path),
            "history_sha256": sha256(history_path),
        }
        if generate_golden:
            result = run_reference(
                hidden_bf16,
                weight,
                history,
                enable_penalty=True,
                repetition_penalty=1.1,
                token_block=token_block,
            )
            raw_path = destination / "raw_logits.fp32.bin"
            processed_path = destination / "processed_scores.fp32.bin"
            np.asarray(result["raw_logits"], dtype="<f4").tofile(raw_path)
            np.asarray(result["processed_scores"], dtype="<f4").tofile(processed_path)
            result_json = {
                "selected_token": result["selected_token"],
                "selected_score": float(result["selected_score"]),
                "selected_score_bits": int(result["selected_score"].view(np.uint32)),
                "output_crc": result["output_crc"],
            }
            (destination / "result.json").write_text(
                json.dumps(result_json, indent=2) + "\n", encoding="utf-8"
            )
            entry.update(
                {
                    "raw_logits_sha256": sha256(raw_path),
                    "processed_scores_sha256": sha256(processed_path),
                    **result_json,
                }
            )
        trace_entries.append(entry)
    return trace_entries


def main() -> int:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--model",
        type=Path,
        help="Model directory or safetensors file; copies the original BF16 bits.",
    )
    source.add_argument(
        "--weight-fp16-npy",
        type=Path,
        help="Legacy fallback; BF16 converted from FP16 is not bit-exact to the model.",
    )
    parser.add_argument("--fixture-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--rows-per-chunk", type=int, default=1024)
    parser.add_argument("--token-block", type=int, default=1024)
    parser.add_argument("--skip-golden", action="store_true")
    args = parser.parse_args()

    args.output_root.mkdir(parents=True, exist_ok=True)
    weight_path = args.output_root / "shared_vocab_weight.bf16.bin"
    if args.model is not None:
        source_info = copy_exact_bf16_weight(args.model, weight_path)
    else:
        source_info = convert_legacy_fp16_weight(
            args.weight_fp16_npy, weight_path, args.rows_per_chunk
        )
    trace_root = args.output_root / "trace"
    entries = convert_trace(
        args.fixture_root,
        trace_root,
        weight_path,
        not args.skip_golden,
        args.token_block,
    )
    manifest = {
        "format": "M14_LM_HEAD_V2_ASSETS",
        "hidden_size": PRODUCTION_HIDDEN_SIZE,
        "vocab_size": PRODUCTION_VOCAB_SIZE,
        "dtype": "BF16_RNE_BITS_LE",
        "weight_layout": "VOCAB_VH_V2_ROW_MAJOR_HIDDEN_GROUP32",
        "weight_bytes": weight_path.stat().st_size,
        "weight_sha256": sha256(weight_path),
        "numeric_impl": NUMERIC_IMPL,
        **source_info,
        "trace": entries,
    }
    (args.output_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
