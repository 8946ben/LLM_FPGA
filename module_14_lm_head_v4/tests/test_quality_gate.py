from pathlib import Path
from types import SimpleNamespace
import importlib.util,unittest
from unittest.mock import patch

path=Path(__file__).resolve().parents[1]/'scripts/evaluate_selectors.py'
spec=importlib.util.spec_from_file_location('selector_evaluator',path)
evaluator=importlib.util.module_from_spec(spec);spec.loader.exec_module(evaluator)

class QualityGate(unittest.TestCase):
    def test_candidate_p95_uses_same_nearest_rank_convention(self):
        import numpy as np
        r=evaluator.describe_counts(np.arange(1,31),0)
        self.assertEqual(r['p95'],29)

    def test_aggregate_cannot_hide_a_weak_category(self):
        report=dict(decode=dict(steps=10000,recall=.9999,by_category=dict(chinese=dict(steps=1000,recall=.998),english=dict(steps=9000,recall=1))))
        self.assertFalse(evaluator.preliminary_gate(report))

    def test_no_holdout_opened_after_failed_calibration(self):
        with patch.object(evaluator,'load_split',side_effect=AssertionError('holdout was opened')):
            evaluator.holdout_phase(SimpleNamespace(),None,None,None,dict(chosen_calibration_configuration=None),None,None)

if __name__=='__main__':unittest.main()
