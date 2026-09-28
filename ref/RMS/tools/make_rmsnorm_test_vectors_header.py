#!/usr/bin/env python3
"""Generate a C header with RMSNorm BF16 test vectors for a Zynq bare-metal app."""

from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create rmsnorm_test_vectors.h from BF16 binary tensors.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("hls/rmsnorm_layer00_prefill/data"),
        help="Directory containing input_bf16.bin, weight_bf16.bin, golden_bf16.bin.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("zynq_rmsnorm_bringup/rmsnorm_test_vectors.h"),
    )
    parser.add_argument(
        "--hex-dir",
        type=Path,
        default=Path("zynq_rmsnorm_bringup/ip_testbench/data"),
        help="Optional output directory for Verilog/Vivado $readmemh files.",
    )
    return parser.parse_args()


def read_u16_words(path: Path) -> list[int]:
    raw = path.read_bytes()
    if len(raw) % 2 != 0:
        raise ValueError(f"{path} size is not a multiple of 2 bytes")
    return [raw[index] | (raw[index + 1] << 8) for index in range(0, len(raw), 2)]


def emit_array(name: str, values: list[int], per_line: int = 12) -> str:
    lines = [f"static const uint16_t {name}[{len(values)}] = {{"]
    for start in range(0, len(values), per_line):
        chunk = values[start : start + per_line]
        suffix = "," if start + per_line < len(values) else ""
        lines.append("    " + ", ".join(f"0x{value:04x}" for value in chunk) + suffix)
    lines.append("};")
    return "\n".join(lines)


def write_hex(path: Path, values: list[int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{value:04x}\n" for value in values), encoding="ascii")


def main() -> None:
    args = parse_args()
    data_dir = args.data_dir
    input_values = read_u16_words(data_dir / "input_bf16.bin")
    weight_values = read_u16_words(data_dir / "weight_bf16.bin")
    golden_values = read_u16_words(data_dir / "golden_bf16.bin")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    text = "\n\n".join(
        [
            "#ifndef RMSNORM_TEST_VECTORS_H",
            "#define RMSNORM_TEST_VECTORS_H",
            "",
            "#include <stdint.h>",
            "",
            "#define RMSNORM_SEQ_LEN 36",
            "#define RMSNORM_HIDDEN_SIZE 896",
            "#define RMSNORM_ELEMENTS (RMSNORM_SEQ_LEN * RMSNORM_HIDDEN_SIZE)",
            "#define RMSNORM_INPUT_BYTES (RMSNORM_ELEMENTS * 2)",
            "#define RMSNORM_WEIGHT_BYTES (RMSNORM_HIDDEN_SIZE * 2)",
            "#define RMSNORM_OUTPUT_BYTES (RMSNORM_ELEMENTS * 2)",
            "",
            emit_array("rmsnorm_input_bf16", input_values),
            "",
            emit_array("rmsnorm_weight_bf16", weight_values),
            "",
            emit_array("rmsnorm_golden_bf16", golden_values),
            "",
            "#endif",
            "",
        ]
    )
    args.out.write_text(text, encoding="utf-8")
    write_hex(args.hex_dir / "input_bf16.hex", input_values)
    write_hex(args.hex_dir / "weight_bf16.hex", weight_values)
    write_hex(args.hex_dir / "golden_bf16.hex", golden_values)
    print(f"wrote {args.out}")
    print(f"wrote hex files under {args.hex_dir}")
    print(f"input={len(input_values)} weight={len(weight_values)} golden={len(golden_values)}")


if __name__ == "__main__":
    main()
