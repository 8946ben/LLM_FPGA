"""Synthetic campaign fixtures test acceptance bookkeeping, not hardware."""
import contextlib
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("acceptance_summary", MODULE / "scripts/summarize_acceptance.py")
SUMMARY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SUMMARY)


class CampaignSummaryTest(unittest.TestCase):
    def check_fixture(self, mutation=None):
        temp_root = MODULE / "build/test_campaign_summary"
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as directory:
            root = Path(directory)
            raw = bytes(16)
            entries = [{"step": f"step_{i:02d}", "selected_token": 1,
                        "selected_score_bits": 0x3FC00000, "output_crc": 123,
                        "raw_logits_sha256": hashlib.sha256(raw).hexdigest()} for i in range(8)]
            records = []
            def record(phase, step="step_00", repeats=1, error=0):
                sequence = len(records)
                run = root / f"run_{sequence}"
                run.mkdir()
                write = int(phase == "accuracy_logits")
                if write:
                    (run / "raw_logits.fp32.bin").write_bytes(raw)
                r = {"step": step, "campaign_phase": phase, "campaign_sequence": sequence,
                     "source_run": str(run), "state": "0x444f4e45", "driver_status": 0,
                     "job_id": 1, "repeat_count": repeats, "result_job_id": repeats,
                     "build_config": 0x10008011, "capabilities": 0x182,
                     "expected_status": error, "status_code": error,
                     "selected_token": 1, "selected_score_bits": 0x3FC00000,
                     "output_crc": 123, "processed_rows": 0 if error else 1,
                     "vocab_rows_done": 0 if error else 151936,
                     "weight_read_beats_128": 0 if error else 17016832,
                     "dot_active_cycles": 17016832, "history_read_words": 4748,
                     "perf_read_beats": 17018131, "run_mode": 1, "enable_penalty": 1,
                     "perf_write_beats": 37984 if write else 0,
                     "logits_write_beats_128": 37984 if write else 0,
                     "logits_written": write, "write_logits": write,
                     "perf_cycles_total": 22486802, "wall_ticks": 7495515 * repeats,
                     "timer_counts_per_second": 33333000}
                records.append(r)
            for entry in entries:
                for phase in ("accuracy_production", "accuracy_logits"):
                    record(phase, entry["step"])
            for step, error in {"bad_abi": 1, "bad_flags": 11, "bad_dimension": 2, "numeric_error": 9}.items():
                record("negative", step, error=error)
            for _ in range(30):
                record("performance")
            record("golden_failure")
            records[-1]["state"] = "0x4641494c"
            records[-1]["driver_status"] = 7
            record("stability", repeats=1000)
            if mutation:
                mutation(records)
            (root / "campaign.json").write_text(json.dumps({"state": "PASS", "records": records}))
            (root / "manifest.json").write_text(json.dumps({"trace": entries}))
            with patch.object(sys, "argv", ["summary", str(root / "campaign.json"),
                                            "--manifest", str(root / "manifest.json"),
                                            "--output", str(root / "summary.json")]), contextlib.redirect_stdout(io.StringIO()):
                status = SUMMARY.main()
            result = json.loads((root / "summary.json").read_text())
        return status, result

    def test_complete_independent_fixture_passes(self):
        status, result = self.check_fixture()
        self.assertEqual(status, 0)
        self.assertEqual(result["performance_samples"], 30)
        self.assertEqual(result["stability_calls"], 1000)
        self.assertEqual(result["accuracy_logits_steps"], 8)

    def test_duplicate_run_is_not_an_independent_sample(self):
        def duplicate(records):
            samples = [r for r in records if r["campaign_phase"] == "performance"]
            samples[1]["source_run"] = samples[0]["source_run"]
        status, result = self.check_fixture(duplicate)
        self.assertEqual(status, 1)
        self.assertEqual(result["performance_samples"], 29)

    def test_score_bit_corruption_and_failed_mailbox_rejected(self):
        def corrupt(records):
            records[0]["selected_score_bits"] += 1
            records[-1]["state"] = "0x4641494c"
        status, result = self.check_fixture(corrupt)
        self.assertEqual(status, 1)
        self.assertIn("selected_score_bits", " ".join(result["failures"]))
        self.assertIn("mailbox failure", " ".join(result["failures"]))


if __name__ == "__main__":
    unittest.main()
