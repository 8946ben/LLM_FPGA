import struct
import unittest
import numpy as np
from reference.candidate_head import (candidate_ids,encode_candidate_table,
    decode_candidate_table,select_candidate,run_candidate_head)
from reference.numeric_contract import float32_to_bf16_bits,run_reference


class CandidateContract(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(20261021)
        self.w=float32_to_bf16_bits(rng.normal(size=(160,896)).astype('f4'))
        self.h=float32_to_bf16_bits(rng.normal(size=896).astype('f4'))
        self.history=np.zeros(5,dtype='u4');self.history[4]=1<<3 # global 131

    def test_full_set_matches_independent_dense_path(self):
        dense=run_reference(self.h,self.w,self.history,True,1.1,token_block=17)
        sparse=run_candidate_head(self.h,self.w,np.arange(160),self.history,token_block=31)
        np.testing.assert_array_equal(sparse['raw_scores'].view('u4'),dense['raw_logits'].view('u4'))
        np.testing.assert_array_equal(sparse['policy_scores'].view('u4'),dense['processed_scores'].view('u4'))
        self.assertEqual(sparse['selected_token'],dense['selected_token'])
        self.assertEqual(sparse['output_crc'],dense['output_crc'])

    def test_noncontiguous_global_rows(self):
        ids=np.array([0,7,31,32,127,128,131,159])
        dense=run_reference(self.h,self.w,self.history,True,1.1)
        got=run_candidate_head(self.h,self.w,ids,self.history,token_block=3)
        np.testing.assert_array_equal(got['raw_scores'].view('u4'),dense['raw_logits'][ids].view('u4'))
        np.testing.assert_array_equal(got['policy_scores'].view('u4'),dense['processed_scores'][ids].view('u4'))
        self.assertEqual(got['logical_weight_bytes'],8*1792)
        self.assertEqual(got['output_coverage'],'CANDIDATES_ONLY')
        self.assertEqual(got['records'].dtype.itemsize,8)

    def test_penalty_global_boundary_and_tie(self):
        ids=np.array([159,131,1,128]);raw=np.array([3,4,-4,3],dtype='f4')
        h=np.zeros(5,dtype='u4');h[4]=1<<3;h[0]=1<<1
        scores,token,_=select_candidate(raw,ids,160,h,penalty=2)
        np.testing.assert_array_equal(scores,np.array([3,2,-8,3],dtype='f4'))
        self.assertEqual(token,128)
        _,token,_=select_candidate(np.zeros(4,dtype='f4'),ids,160,None,enable_penalty=False)
        self.assertEqual(token,1)

    def test_invalid_ids(self):
        for ids in ([],[1,1],[-1],[160],[1.5],[True],[[1]], [0,2**40],[2,1]):
            with self.subTest(ids=ids),self.assertRaises(ValueError):candidate_ids(ids,160)

    def test_table_roundtrip_and_corruption(self):
        data=encode_candidate_table([0,32,159],160)
        np.testing.assert_array_equal(decode_candidate_table(data,160),[0,32,159])
        for bad in (data[:4],data[:-1],data+b'\x00',b'NOPE'+data[4:],data[:4]+b'\x02\x00'+data[6:]):
            with self.subTest(bad=bad[:16]),self.assertRaises(ValueError):decode_candidate_table(bad,160)
        with self.assertRaises(ValueError):decode_candidate_table(data,161)

    def test_skipped_nonfinite_scope(self):
        # Sparse cannot detect NaN in an unselected row. Explicitly test this limit.
        self.w[159,0]=0x7fc0
        run_candidate_head(self.h,self.w,[0,1],self.history)
        with self.assertRaises(FloatingPointError):run_candidate_head(self.h,self.w,[159],self.history)

    def test_penalty_off_ignores_inactive_parameters(self):
        run_candidate_head(self.h,self.w,[0,1],None,enable_penalty=False,penalty=float('nan'))

    def test_missing_or_short_global_history_rejected(self):
        for h in (None,np.zeros(4,dtype='u4')):
            with self.assertRaises(ValueError):run_candidate_head(self.h,self.w,[131],h)


if __name__=='__main__':unittest.main()
