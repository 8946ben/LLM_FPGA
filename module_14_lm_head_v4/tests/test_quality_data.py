import unittest
import numpy as np
from reference.quality_data import assert_group_disjoint,assert_compatible_collections,recall_report,penalty_aware_target_ranks

class QualityContract(unittest.TestCase):
    def test_mixed_label_models_or_policy_rejected(self):
        settings=dict(model_lock_sha256='m',canonical_weight_sha256='w',collector_sha256='c',gpu_head_sha256='g',
            torch='t',transformer_dtype='BF16',head_dtype='FP32_H8_INTERLEAVE16_SEPARATE_MULTIPLY_ADD',penalty=1.1,
            system_prompt='s',max_input_tokens=2048,max_new_tokens=16,raw_top_k=256)
        make=lambda s:dict(manifest=dict(settings=s))
        assert_compatible_collections(make(settings),make(dict(settings)))
        for changed in [dict(settings,model_lock_sha256='different'),dict(settings,penalty=1.2)]:
            with self.assertRaises(ValueError):assert_compatible_collections(make(settings),make(changed))

    def test_prompt_group_cross_split_rejected(self):
        with self.assertRaises(ValueError):assert_group_disjoint(dict(groups=['p1','p2']),dict(groups=['p2','p3']))
        assert_group_disjoint(dict(groups=['p1','p1']),dict(groups=['p2']))

    def test_prefill_and_decode_are_separate(self):
        d=dict(winner=np.zeros(4,dtype='u4'),groups=np.array(['a','a','b','b']),
            category=np.array(['code','code','math','math']),decode=np.array([False,True,False,True]))
        r=recall_report([False,True,True,True],d)
        self.assertEqual(r['all']['recall'],.75);self.assertEqual(r['decode']['recall'],1)
        self.assertEqual(r['prefill']['recall'],.5);self.assertEqual(r['prompt_groups'],2)
        self.assertEqual(r['decode_prompt_bootstrap_interval95'],[1,1])
        self.assertEqual(r['decode']['by_category']['code']['steps'],1)

    def test_penalty_rank_matches_brute_force_topk(self):
        raw=np.array([[5,4,4,-1,-2],[0,0,0,0,0]],dtype='f4')
        histories=[np.array([0,4],dtype='u4'),np.array([],dtype='u4')]
        # seen global0 drops below the equal-4 pair; lower global1 wins that tie.
        ranks=penalty_aware_target_ranks(raw,np.array([2,3]),histories,penalty=2)
        np.testing.assert_array_equal(ranks,[1,3])
        np.testing.assert_array_equal(raw[0],[5,4,4,-1,-2]) # evaluator does not mutate preview
        np.testing.assert_array_equal(penalty_aware_target_ranks(raw,np.array([2,3]),histories,mandatory=[2,3]),[-1,-1])

if __name__=='__main__':unittest.main()
