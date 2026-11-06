"""Verify generated M14 V2 assets against a trace manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    failures: list[str] = []
    weight = args.asset_root / "shared_vocab_weight.bf16.bin"
    if not weight.is_file():
        failures.append("missing shared_vocab_weight.bf16.bin")
    else:
        if weight.stat().st_size != manifest["weight_bytes"]:
            failures.append("weight byte count mismatch")
        if sha256(weight) != manifest["weight_sha256"]:
            failures.append("weight SHA256 mismatch")

    for entry in manifest["trace"]:
        directory = args.asset_root / "trace" / entry["step"]
        files = {
            "hidden_sha256": directory / "hidden.bf16.bin",
            "history_sha256": directory / "history_bitmap.u32.bin",
            "raw_logits_sha256": directory / "raw_logits.fp32.bin",
            "processed_scores_sha256": directory / "processed_scores.fp32.bin",
        }
        for key, path in files.items():
            if key not in entry:
                continue
            if not path.is_file():
                failures.append(f"{entry['step']}: missing {path.name}")
            elif sha256(path) != entry[key]:
                failures.append(f"{entry['step']}: {path.name} SHA256 mismatch")
        result_path = directory / "result.json"
        if result_path.is_file():
            result = json.loads(result_path.read_text(encoding="utf-8"))
            keys = ["selected_token", "output_crc"]
            if "selected_score_bits" in entry:
                keys.append("selected_score_bits")
            for key in keys:
                if result.get(key) != entry.get(key):
                    failures.append(f"{entry['step']}: {key} mismatch")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        print(f"ASSET_VERIFY=FAIL count={len(failures)}")
        return 1
    print(
        f"ASSET_VERIFY=PASS steps={len(manifest['trace'])} "
        f"weight_sha256={manifest['weight_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
