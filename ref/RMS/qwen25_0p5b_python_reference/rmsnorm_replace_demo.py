#!/usr/bin/env python3
"""Small RMSNorm replacement demo for the Orin-side Qwen2 reference.

Default mode uses `local-bf16`, which mirrors the Vitis HLS C model. To exercise
the ZIP Ethernet path on one machine:

  python rmsnorm_replace_demo.py --backend ethernet --start-local-server

To exercise the raw AXU9EGB board protocol with a local NumPy server:

  python rmsnorm_replace_demo.py --backend raw-ethernet --start-local-server
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch

from qwen2_module_reference import rmsnorm, set_rmsnorm_backend
from rmsnorm_fpga_backend import bf16_uint16_to_float32, make_rmsnorm_backend


SCRIPT_DIR = Path(__file__).resolve().parent


def find_repo_root() -> Path:
    for candidate in [SCRIPT_DIR, *SCRIPT_DIR.parents]:
        if (candidate / "hls" / "rmsnorm_layer00_prefill" / "data").is_dir():
            return candidate
    return SCRIPT_DIR.parent


REPO_ROOT = find_repo_root()
DEFAULT_DATA_DIR = REPO_ROOT / "hls" / "rmsnorm_layer00_prefill" / "data"
DEFAULT_SERVER = REPO_ROOT / "orin_ethernet_vitis_bridge" / "scripts" / "rmsnorm_rpc_server.py"
DEFAULT_RAW_SERVER = REPO_ROOT / "orin_ethernet_vitis_bridge" / "scripts" / "rmsnorm_raw_rpc_server.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a small RMSNorm backend replacement demo.")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--backend", choices=["local-bf16", "ethernet", "raw-ethernet"], default="local-bf16")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=50052)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--start-local-server", action="store_true")
    parser.add_argument("--abs-tol", type=float, default=1.0e-2)
    parser.add_argument("--rel-tol", type=float, default=1.0e-2)
    parser.add_argument("--report-json", type=Path, default=None)
    return parser.parse_args()


def read_metadata(data_dir: Path) -> dict:
    path = data_dir / "metadata.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"seq_len": 36, "hidden_size": 896, "eps": 1.0e-6}


def read_bf16(path: Path, shape: tuple[int, ...]) -> np.ndarray:
    words = np.fromfile(path, dtype="<u2")
    expected = math.prod(shape)
    if words.size != expected:
        raise ValueError(f"{path} has {words.size} elements, expected {expected}")
    return bf16_uint16_to_float32(words).reshape(shape)


def start_server(args: argparse.Namespace) -> subprocess.Popen:
    server_path = DEFAULT_RAW_SERVER if args.backend == "raw-ethernet" else DEFAULT_SERVER
    if not server_path.is_file():
        raise FileNotFoundError(f"RMSNorm RPC server not found: {server_path}")
    cmd = [
        sys.executable,
        "-u",
        str(server_path),
        "--host",
        args.host,
        "--port",
        str(args.port),
        "--once",
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.stdout is not None:
        line = proc.stdout.readline().strip()
        if line:
            print(line)
    time.sleep(0.1)
    return proc


def finish_server(proc: subprocess.Popen | None) -> None:
    if proc is None:
        return
    try:
        stdout, stderr = proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
    if stdout.strip():
        print(stdout.strip())
    if stderr.strip():
        print(stderr.strip(), file=sys.stderr)
    if proc.returncode != 0:
        raise RuntimeError(f"local RMSNorm RPC server exited with {proc.returncode}")


def compare(output: np.ndarray, golden: np.ndarray, abs_tol: float, rel_tol: float) -> dict:
    abs_err = np.abs(output.astype(np.float32) - golden.astype(np.float32))
    rel_err = abs_err / np.maximum(np.abs(golden.astype(np.float32)), 1.0e-6)
    fail_mask = (abs_err > abs_tol) & (rel_err > rel_tol)
    return {
        "passed": bool(not np.any(fail_mask)),
        "max_abs_err": float(np.max(abs_err)),
        "mean_abs_err": float(np.mean(abs_err)),
        "max_rel_err": float(np.max(rel_err)),
        "mean_rel_err": float(np.mean(rel_err)),
        "fail_count": int(np.count_nonzero(fail_mask)),
        "element_count": int(output.size),
    }


def main() -> None:
    args = parse_args()
    metadata = read_metadata(args.data_dir)
    seq_len = int(metadata.get("seq_len", 36))
    hidden_size = int(metadata.get("hidden_size", 896))
    eps = float(metadata.get("eps", 1.0e-6))

    input_np = read_bf16(args.data_dir / "input_bf16.bin", (1, seq_len, hidden_size))
    weight_np = read_bf16(args.data_dir / "weight_bf16.bin", (hidden_size,))
    golden_np = read_bf16(args.data_dir / "golden_bf16.bin", (1, seq_len, hidden_size))

    proc: subprocess.Popen | None = None
    if args.backend in ("ethernet", "raw-ethernet") and args.start_local_server:
        proc = start_server(args)

    try:
        set_rmsnorm_backend(
            make_rmsnorm_backend(
                args.backend,
                host=args.host,
                port=args.port,
                timeout=args.timeout,
            )
        )
        output = rmsnorm(
            torch.from_numpy(input_np.astype(np.float32)),
            torch.from_numpy(weight_np.astype(np.float32)),
            eps,
        )
    finally:
        set_rmsnorm_backend(None)
        finish_server(proc)

    output_np = output.detach().cpu().to(torch.float32).numpy()
    report = compare(output_np, golden_np, args.abs_tol, args.rel_tol)
    report.update(
        {
            "backend": args.backend,
            "data_dir": str(args.data_dir),
            "shape": [1, seq_len, hidden_size],
            "eps": eps,
        }
    )
    if args.report_json:
        args.report_json.parent.mkdir(parents=True, exist_ok=True)
        args.report_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
