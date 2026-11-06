"""Acceptance must reject failed mailboxes and exact-score corruption."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import compare_board_results as checker


class BoardResultAcceptanceTest(unittest.TestCase):
    def run_check(self, overrides=None, excluded=False):
        golden = {"step": "step_00", "selected_token": 1,
                  "selected_score_bits": 0x3FC00000, "output_crc": 123}
        record = {"step": "step_00", "state": "0x444f4e45", "driver_status": 0,
                  "status_code": 0, "selected_token": 1, "selected_score_bits": 0x3FC00000,
                  "output_crc": 123, "vocab_rows_done": 151936,
                  "weight_read_beats_128": 17016832, "processed_rows": 1,
                  "write_logits": 0, "logits_write_beats_128": 0,
                  "perf_cycles_total": 22486802}
        record.update(overrides or {})
        records = [record]
        if excluded:
            records.insert(0, {"step": "step_00", "excluded_from_acceptance": True,
                               "exclusion_reason": "old ELF lost counters"})
        temporary_root = Path(__file__).resolve().parents[1] / "build/test_results"
        temporary_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temporary_root) as directory:
            root = Path(directory)
            (root / "manifest.json").write_text(json.dumps({"trace": [golden]}))
            (root / "results.json").write_text(json.dumps({"records": records}))
            output = io.StringIO()
            with patch.object(sys, "argv", ["checker", "--manifest", str(root / "manifest.json"),
                                            "--results", str(root / "results.json")]), contextlib.redirect_stdout(output):
                status = checker.main()
        return status, output.getvalue()

    def test_complete_exact_record_passes_with_explicit_exclusion(self):
        status, output = self.run_check(excluded=True)
        self.assertEqual(status, 0)
        self.assertIn("n=1", output)

    def test_failed_mailbox_cannot_pass_or_enter_latency(self):
        status, output = self.run_check({"state": "0x4641494c", "driver_status": 7})
        self.assertEqual(status, 1)
        self.assertNotIn("production latency", output)

    def test_score_bits_checked_even_with_matching_crc(self):
        status, output = self.run_check({"selected_score_bits": 0x3FC00001})
        self.assertEqual(status, 1)
        self.assertIn("selected_score_bits mismatch", output)
        self.assertNotIn("production latency", output)


if __name__ == "__main__":
    unittest.main()
