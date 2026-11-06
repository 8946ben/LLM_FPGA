import unittest
import numpy as np
from reference.numeric_contract import float32_to_bf16_bits
from reference.selector_arithmetic import lowrank_preview,router_ids

class SelectorArithmeticTests(unittest.TestCase):
    def test_projection_and_global_sign_sensitive_penalty(self):
        h=np.zeros(896,dtype='f4');h[:3]=[2,-3,1]
        b=np.zeros((896,128),dtype='f4');b[:128]=np.eye(128,dtype='f4')
        a=np.zeros((3,128),dtype='f4');a[0,:3]=[1,2,0];a[1,2]=5;a[2,0]=1
        scores,z=lowrank_preview(float32_to_bf16_bits(h),float32_to_bf16_bits(a),float32_to_bf16_bits(b),[0,1],penalty=2)
        np.testing.assert_array_equal(z[:3],np.array([2,-3,1],dtype='f4'))
        np.testing.assert_array_equal(scores,np.array([-8,2.5,2],dtype='f4'))
    def test_distance_stable_cluster_id_tie(self):
        h=np.zeros(896,dtype='u2');c=np.zeros((128,896),dtype='u2')
        ids,distance=router_ids(h,c,np.zeros(128,dtype='f4'))
        np.testing.assert_array_equal(ids,[0,1,2,3]);np.testing.assert_array_equal(distance,np.zeros(128,dtype='f4'))
    def test_invalid_policy_history_and_norms(self):
        h=np.zeros(896,dtype='u2');a=np.zeros((3,128),dtype='u2');b=np.zeros((896,128),dtype='u2')
        for history in ([-1],[3],[0.5]):
            with self.assertRaises(ValueError):lowrank_preview(h,a,b,history)
        with self.assertRaises(ValueError):lowrank_preview(h,a,b,penalty=0.5)
        with self.assertRaises(ValueError):router_ids(h,np.zeros((128,896),dtype='u2'),np.full(128,-1,dtype='f4'))

if __name__=='__main__':unittest.main()
