"""Report parsing must reject partial, duplicate and malformed completions."""
import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from selector_rtl_completion import transactions
from check_selector_rtl_traces import compare

class CompletionTests(unittest.TestCase):
    def parse(self, data):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'result.xml'; p.write_text(data)
            return transactions(p)

    def test_generated_text_table(self):
        self.assertEqual(self.parse(' latency interval\ntransaction 0: 6826306 6826211\ntransaction 1: 726 x\n'),
                         [dict(index=0,cycles=6826306),dict(index=1,cycles=726)])

    def test_missing_duplicate_unordered_and_unknown(self):
        for data in ('', 'transaction 0: 12 12\n',
                     'transaction 0: 12 12\ntransaction 0: 1 x\n',
                     'transaction 1: 12 12\ntransaction 0: 1 x\n',
                     'transaction 0: x 12\ntransaction 1: 1 x\n',
                     'transaction 0: 12 12\ntransaction 1: 1 x\ntransaction 2: 1 x\n'):
            with self.subTest(data=data), self.assertRaises(AssertionError): self.parse(data)

    def test_trace_transaction_padding_only(self):
        c=b'[[[runtime]]]\n[[transaction]] 0\n0x0001\n[[/transaction]]\n[[transaction]] 1\n0x0003\n[[/transaction]]\n[[[/runtime]]]\n'
        r=c.replace(b'[[transaction]] ',b'[[transaction]]           ')
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'c'; b=Path(d)/'rtl'; a.write_bytes(c); b.write_bytes(r)
            self.assertEqual(compare(a,b)['values'],2)
            for bad in (r.replace(b'0x0001',b'0x0002'), r.replace(b'0x0001',b'0x00xx'),
                        r.replace(b'[[transaction]]           1',b'[[transaction]]           2'),
                        r.replace(b'[[[/runtime]]]',b'')):
                b.write_bytes(bad)
                with self.assertRaises(AssertionError): compare(a,b)

if __name__=='__main__': unittest.main()
