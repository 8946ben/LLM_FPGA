import unittest
import numpy as np
from reference.hybrid_selector import stable_topk_ids

class StableTopK(unittest.TestCase):
    def test_cutoff_ties_use_lower_global_id_and_output_global_order(self):
        np.testing.assert_array_equal(stable_topk_ids(np.array([2,4,2,4,2],dtype='f4'),np.array([],dtype='u4'),3),[0,1,3])

    def test_history_policy_both_signs_changes_selection(self):
        np.testing.assert_array_equal(stable_topk_ids(np.array([10,9.5,-1,-1.05],dtype='f4'),np.array([0,2],dtype='u4'),1),[1])
        np.testing.assert_array_equal(stable_topk_ids(np.array([-1,-1.05],dtype='f4'),np.array([0],dtype='u4'),1),[1])

    def test_invalid_nonfinite_and_global_history_rejected(self):
        for values,seen,k in [([1,np.nan],[],1),([1,2],[2],1),([1,2],[],0)]:
            with self.assertRaises(ValueError):stable_topk_ids(np.array(values,dtype='f4'),np.array(seen,dtype='u4'),k)

if __name__=='__main__':unittest.main()
