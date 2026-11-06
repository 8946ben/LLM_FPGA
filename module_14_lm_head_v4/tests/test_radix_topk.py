import unittest
import numpy as np
from reference.radix_topk import radix_topk_ids

class RadixTopK(unittest.TestCase):
    def test_full_vocabulary_against_independent_stable_sort(self):
        rng=np.random.default_rng(20261021);x=rng.standard_normal(151936).astype('f4')
        x[::7]=np.float32(-2);x[::11]=np.float32(2)
        ids,_=radix_topk_ids(x,16384);expected=np.sort(np.lexsort((np.arange(len(x)),-x))[:16384])
        np.testing.assert_array_equal(ids,expected)

    def test_signed_zero_negative_cutoff_ties_and_all_budgets(self):
        x=np.array([-2,-0.,0.,-1,2,2,-2,1],dtype='f4')
        for k in range(1,len(x)+1):
            ids,meta=radix_topk_ids(x,k);expected=np.sort(np.lexsort((np.arange(len(x)),-x))[:k])
            np.testing.assert_array_equal(ids,expected);self.assertEqual(len(meta['passes']),4)

    def test_reject_invalid_and_nonfinite_scores(self):
        for x,k in [([1,np.nan],1),([1,np.inf],1),([1,2],True),([1,2],0),([1,2],3),([1,2],1.5)]:
            with self.assertRaises(ValueError):radix_topk_ids(np.array(x,dtype='f4'),k)

if __name__=='__main__':unittest.main()
