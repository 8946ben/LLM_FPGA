"""Migrate legacy golden to the corrected tree, preserving audited inputs."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "reference"))
from lm_head_v2_ref import NUMERIC_IMPL, run_reference
from verify_assets import sha256


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--module", type=Path, required=True)
    args = parser.parse_args()
    report = args.module / "reports/numeric_20261009"
    archive = report / "legacy_golden"
    source_manifest = args.assets / "manifest.json"
    manifest = json.loads(source_manifest.read_text(encoding="utf-8"))
    if sha256(args.assets / "shared_vocab_weight.bf16.bin") != manifest["weight_sha256"]:
        raise ValueError("weight SHA256 mismatch")
    if not (archive / "manifest.json").exists():
        if manifest["numeric_impl"] == NUMERIC_IMPL:
            raise ValueError("refusing to archive corrected assets as legacy")
        for entry in manifest["trace"]:
            directory = args.assets / "trace" / entry["step"]
            for name, key in (("hidden.bf16.bin", "hidden_sha256"),
                              ("history_bitmap.u32.bin", "history_sha256"),
                              ("raw_logits.fp32.bin", "raw_logits_sha256"),
                              ("processed_scores.fp32.bin", "processed_scores_sha256")):
                if sha256(directory / name) != entry[key]:
                    raise ValueError(f"legacy {entry['step']} {name} hash mismatch")
            target = archive / "trace" / entry["step"]
            target.mkdir(parents=True, exist_ok=True)
            for name in ("raw_logits.fp32.bin", "processed_scores.fp32.bin", "result.json"):
                shutil.copy2(directory / name, target / name)
        shutil.copy2(args.module / "golden/v2_trace_manifest.json", archive / "v2_trace_manifest.json")
        shutil.copy2(source_manifest, archive / "manifest.json")
    legacy_manifest = json.loads((archive / "manifest.json").read_text(encoding="utf-8"))
    if legacy_manifest["weight_sha256"] != manifest["weight_sha256"]:
        raise ValueError("archive weight mismatch")
    old_entries = {entry["step"]: entry for entry in legacy_manifest["trace"]}
    weight = np.memmap(args.assets / "shared_vocab_weight.bf16.bin", mode="r",
                       dtype="<u2", shape=(manifest["vocab_size"], manifest["hidden_size"]))
    summaries = []
    for entry in manifest["trace"]:
        directory = args.assets / "trace" / entry["step"]
        old = old_entries[entry["step"]]
        for name, key in (("hidden.bf16.bin", "hidden_sha256"),
                          ("history_bitmap.u32.bin", "history_sha256")):
            if sha256(directory / name) != old[key]:
                raise ValueError(f"{entry['step']} input changed: {name}")
        hidden = np.fromfile(directory / "hidden.bf16.bin", dtype="<u2")
        history = np.fromfile(directory / "history_bitmap.u32.bin", dtype="<u4")
        result = run_reference(hidden, weight, history, True, 1.1)
        if result["selected_token"] != old["selected_token"]:
            raise ValueError(f"{entry['step']} top-1 changed; review required")
        raw = np.asarray(result["raw_logits"], dtype="<f4")
        scores = np.asarray(result["processed_scores"], dtype="<f4")
        raw.tofile(directory / "raw_logits.fp32.bin")
        scores.tofile(directory / "processed_scores.fp32.bin")
        result_json = {"numeric_impl": NUMERIC_IMPL,
                       "selected_token": result["selected_token"],
                       "selected_score": float(result["selected_score"]),
                       "selected_score_bits": int(result["selected_score"].view(np.uint32)),
                       "output_crc": result["output_crc"]}
        (directory / "result.json").write_text(json.dumps(result_json, indent=2) + "\n", encoding="utf-8")
        entry.update(result_json)
        entry["raw_logits_sha256"] = sha256(directory / "raw_logits.fp32.bin")
        entry["processed_scores_sha256"] = sha256(directory / "processed_scores.fp32.bin")
        legacy = np.fromfile(archive / "trace" / entry["step"] / "raw_logits.fp32.bin", dtype="<f4")
        top = np.argsort(-scores, kind="stable")[:10]
        summaries.append({"step": entry["step"], **result_json,
                          "legacy_crc": old["output_crc"],
                          "legacy_exact_elements": int(np.count_nonzero(raw.view(np.uint32) == legacy.view(np.uint32))),
                          "max_absolute_delta": float(np.max(np.abs(raw.astype(np.float64) - legacy))),
                          "top1_margin": float(np.float64(scores[top[0]]) - scores[top[1]]),
                          "top10": [{"token": int(token), "score_bits": int(scores[token].view(np.uint32))} for token in top]})
        print(f"GOLDEN_REGENERATED={entry['step']} token={entry['selected_token']} crc={entry['output_crc']}", flush=True)
    manifest["numeric_impl"] = NUMERIC_IMPL
    manifest["numeric_contract"] = "module_14_lm_head_v2/NUMERIC_CONTRACT.md"
    encoded = json.dumps(manifest, indent=2) + "\n"
    source_manifest.write_text(encoded, encoding="utf-8")
    (args.module / "golden/v2_trace_manifest.json").write_text(encoded, encoding="utf-8")
    (report / "golden_migration.json").write_text(json.dumps({"numeric_impl": NUMERIC_IMPL, "steps": summaries}, indent=2) + "\n", encoding="utf-8")
    archive_hashes = [f"{sha256(path)}  {path.relative_to(archive).as_posix()}" for path in sorted(archive.rglob("*")) if path.is_file() and path.name != "SHA256SUMS"]
    (archive / "SHA256SUMS").write_text("\n".join(archive_hashes) + "\n", encoding="utf-8")
    print("GOLDEN_MIGRATION=PASS steps=8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
