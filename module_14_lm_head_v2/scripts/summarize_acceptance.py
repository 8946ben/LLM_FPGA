"""Validate an isolated campaign and summarize independent performance samples."""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "standalone"))
from board_profile import load_profile


def p95(values):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, (95 * len(ordered) + 99) // 100 - 1)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("campaign", type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    campaign = json.loads(args.campaign.read_text(encoding="utf-8-sig"))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    profile = load_profile(campaign["package_dir"])
    golden = {entry["step"]: entry for entry in manifest["trace"]}
    failures = []
    accuracy = {"accuracy_production": set(), "accuracy_logits": set()}
    perf = []
    stability = []
    negatives = {}
    seen_runs = set()
    golden_failures = []
    expected_negative = {"bad_abi": 1, "bad_flags": 11,
                         "bad_dimension": 2, "numeric_error": 9}
    for record in campaign["records"]:
        phase = record["campaign_phase"]
        label = f"{phase}:{record['step']}:{record['campaign_sequence']}"
        before = len(failures)
        source_run = record["source_run"]
        if source_run in seen_runs:
            failures.append(label + ": repeated source run is not an independent sample")
        seen_runs.add(source_run)
        expected_state = "0x4641494c" if phase == "golden_failure" else "0x444f4e45"
        expected_driver = 7 if phase == "golden_failure" else 0
        if record["state"] != expected_state or record["driver_status"] != expected_driver:
            failures.append(label + ": mailbox failure")
        expected_job = record["job_id"] + record["repeat_count"] - 1
        if record["result_job_id"] != expected_job:
            failures.append(label + ": result job ID")
        if record["build_config"] != profile["build_config"] or record["capabilities"] != 0x182:
            failures.append(label + ": hardware build/capabilities")
        if "ip_clock_hz" in record and record["ip_clock_hz"] != profile["ip_clock_hz"]:
            failures.append(label + ": counter clock does not match package")
        if phase == "negative":
            expected = expected_negative.get(record["step"])
            if record["status_code"] != expected or record["expected_status"] != expected:
                failures.append(label + ": negative status")
            if record["vocab_rows_done"] != 0 or record["processed_rows"] != 0 or record["weight_read_beats_128"] != 0:
                failures.append(label + ": invalid job performed work")
            negatives[record["step"]] = record["status_code"]
            continue
        entry = golden[record["step"]]
        for field in ("selected_token", "selected_score_bits", "output_crc"):
            if record[field] != entry[field]:
                failures.append(label + ": " + field)
        invariants = {"status_code": 0, "processed_rows": 1,
                      "run_mode": 1, "enable_penalty": 1,
                      "vocab_rows_done": 151936, "weight_read_beats_128": 17016832,
                      "dot_active_cycles": 17016832, "history_read_words": 4748,
                      "perf_read_beats": 17018131}
        for field, expected in invariants.items():
            if record[field] != expected:
                failures.append(label + ": " + field)
        expected_writes = 37984 if record["write_logits"] else 0
        for field in ("perf_write_beats", "logits_write_beats_128"):
            if record[field] != expected_writes:
                failures.append(label + ": " + field)
        if record["logits_written"] != record["write_logits"]:
            failures.append(label + ": logits_written")
        if phase in accuracy:
            expected_logits = 1 if phase == "accuracy_logits" else 0
            if record["write_logits"] != expected_logits:
                failures.append(label + ": wrong accuracy I/O mode")
        if record["perf_cycles_total"] <= 0 or record["wall_ticks"] <= 0 or record["timer_counts_per_second"] <= 0:
            failures.append(label + ": nonpositive runtime counter")
        if phase == "accuracy_logits":
            raw_path = Path(record["source_run"]) / "raw_logits.fp32.bin"
            if not raw_path.exists() or hashlib.sha256(raw_path.read_bytes()).hexdigest() != entry["raw_logits_sha256"]:
                failures.append(label + ": raw logits SHA256")
        if phase in accuracy and len(failures) == before:
            accuracy[phase].add(record["step"])
        if phase == "performance":
            if record["repeat_count"] != 1 or record["write_logits"]:
                failures.append(label + ": performance must be a single production call")
            elif len(failures) == before:
                perf.append(record)
        if phase == "stability":
            stability.append(record)
        if phase == "golden_failure" and len(failures) == before:
            golden_failures.append(record)
    for phase, steps in accuracy.items():
        if steps != set(golden):
            failures.append(phase + ": missing successful steps " + str(sorted(set(golden) - steps)))
    if set(negatives) != set(expected_negative):
        failures.append("missing negative tests")
    if len(perf) < 30:
        failures.append("fewer than 30 independent performance samples")
    if len(stability) != 1 or stability[0]["repeat_count"] != 1000:
        failures.append("missing 1000-call stability run")
    if len(golden_failures) != 1:
        failures.append("missing controlled golden-failure timing regression")
    if campaign["state"] != "PASS":
        failures.append("campaign did not finish successfully")
    summary = {"state": "FAIL" if failures else "PASS", "failures": failures,
               "build_config": profile["build_config"], "ip_clock_hz": profile["ip_clock_hz"],
               "clock_basis": profile["clock_basis"],
               "accuracy_production_steps": len(accuracy["accuracy_production"]),
               "accuracy_logits_steps": len(accuracy["accuracy_logits"]),
               "negative_statuses": negatives, "performance_samples": len(perf),
               "golden_failure_timing_checks": len(golden_failures),
               "stability_calls": sum(record["repeat_count"] for record in stability)}
    if perf:
        cycles = [record["perf_cycles_total"] for record in perf]
        ip_ms = [value * 1000 / profile["ip_clock_hz"] for value in cycles]
        wall_ms = [record["wall_ticks"] * 1000 / record["timer_counts_per_second"] for record in perf]
        summary["performance"] = {"ip_cycles_min": min(cycles), "ip_cycles_max": max(cycles),
                                  "ip_ms_median": statistics.median(ip_ms), "ip_ms_p95": p95(ip_ms),
                                  "ip_ms_max": max(ip_ms), "a53_wall_ms_median": statistics.median(wall_ms),
                                  "a53_wall_ms_p95": p95(wall_ms), "a53_wall_ms_max": max(wall_ms),
                                  "speedup_ip_vs_11_09s": 11090 / statistics.median(ip_ms)}
    if stability and stability[0]["timer_counts_per_second"] > 0:
        summary["stability_wall_seconds"] = stability[0]["wall_ticks"] / stability[0]["timer_counts_per_second"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print("M14_CAMPAIGN_CHECK=" + summary["state"])
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
