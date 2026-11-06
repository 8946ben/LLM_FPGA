from pathlib import Path
import random,struct,unittest
from reference.selector_layout import validate_descriptor,PHYSICAL_BASE
M=Path(__file__).resolve().parents[1]

class SelectorLayoutTests(unittest.TestCase):
    def setUp(self):self.data=(M/'reports/selector_integration_fixture_20261021/descriptor_debug.bin').read_bytes()
    def test_full64bit_base_and_disabled_debug(self):
        p=validate_descriptor(self.data)
        self.assertGreater(p['regions'][0]['address'],0xffffffff)
        self.assertEqual(p['physical_descriptor'],PHYSICAL_BASE+1048576)
        validate_descriptor(self.data,history_address=p['history_address'])
        for history in (0,0x51000000,p['history_address']+16,p['history_address']&0xffffffff):
            with self.assertRaises(ValueError):validate_descriptor(self.data,history_address=history)
        for base in (0,0x51000000,0x40000000,PHYSICAL_BASE+16):
            with self.assertRaises(ValueError):validate_descriptor(self.data,physical_base=base)
        p=validate_descriptor((M/'reports/selector_integration_fixture_20261021/descriptor_production.bin').read_bytes())
        self.assertIsNone(p['regions'][12])
    def test_capacity_alias_and_uint64_overflow(self):
        for off,size in ((0xfffffffffffffff0,272269312),(1048832,0xfffffffffffffff0),(1048833,272269312),(1048832,16)):
            b=bytearray(self.data);struct.pack_into('<QQ',b,32,off,size)
            with self.assertRaises(ValueError):validate_descriptor(b)
        b=bytearray(self.data);b[32+10*16:40+10*16]=b[32+11*16:40+11*16]
        with self.assertRaises(ValueError):validate_descriptor(b)
    def test_seeded_random_legal_layouts_and_overlap(self):
        rng=random.Random(20261021)
        for _ in range(32):
            b=bytearray(self.data);cursor=1048576+256
            for i in range(13):
                _,capacity=struct.unpack_from('<QQ',b,32+i*16);cursor=(cursor+63)&~63
                struct.pack_into('<QQ',b,32+i*16,cursor,capacity);cursor+=capacity+16*rng.randrange(0,8)
            validate_descriptor(b)
            b[32+11*16:40+11*16]=b[32+10*16:40+10*16]
            with self.assertRaises(ValueError):validate_descriptor(b)

if __name__=='__main__':unittest.main()
