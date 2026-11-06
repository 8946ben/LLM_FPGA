import unittest
import numpy as np
from reference.routing import train_router,nearest_centers,routed_candidates
from reference.numeric_contract import float32_to_bf16_bits,bf16_bits_to_float32

class Routing(unittest.TestCase):
    def test_routes_are_online_and_global(self):
        x=np.array([[-3,0],[-2.8,0],[3,0],[2.8,0]],dtype='f4')
        top=np.array([[7,31],[7,32],[131,159],[131,158]],dtype='u4')
        model=train_router(float32_to_bf16_bits(x),top,np.array([7,7,131,131]),160,2,iterations=4,max_k=8)
        routes=nearest_centers(x,bf16_bits_to_float32(model['centers_bf16']))
        for i,route in enumerate(routes):
            ids,fallback=routed_candidates(model,route,2,mandatory=[0,159])
            self.assertIn([7,7,131,131][i],ids);self.assertIn(0,ids);self.assertIn(159,ids)
            self.assertFalse(fallback);self.assertTrue(np.all(ids[1:]>ids[:-1]))

    def test_empty_route_fallback_cost_is_full_vocab(self):
        model=dict(vocab_size=np.array(160),ranked_ids=np.zeros((1,4),dtype='u4'),counts=np.array([0]))
        ids,fallback=routed_candidates(model,[0],4)
        self.assertTrue(fallback);self.assertEqual(len(ids),160)

    def test_invalid_route_or_required_token(self):
        model=dict(vocab_size=np.array(160),ranked_ids=np.zeros((1,4),dtype='u4'),counts=np.array([0]))
        for routes,k,mandatory in [([-1],1,[]),([1],1,[]),([0],0,[]),([0],1,[160])]:
            with self.subTest(routes=routes,k=k),self.assertRaises(ValueError):routed_candidates(model,routes,k,mandatory)

    def test_equal_distance_uses_stable_center_index(self):
        np.testing.assert_array_equal(nearest_centers(np.array([[0,0]],dtype='f4'),np.array([[1,0],[-1,0]],dtype='f4'),2),[[0,1]])

if __name__=='__main__':unittest.main()
