"""Synthetic file-only capture tests; do not save these as board results."""
import unittest,zlib,struct
from standalone import selector_ps_mailbox as m

def fixture(validate=False):
    token=20412;score=0x41de477c;crc=zlib.crc32(struct.pack('<II',token,score))
    meta={'expected':{'token':token,'score_bits':hex(score),'crc32':f'{crc:08x}'},'image_digest':{'crc32':'d1a10b86'}}
    request=m.prepare_request(meta,validate_only=validate,warmups=1,measurements=30,stability=2,nonce=73)
    h=list(m.HEADER.unpack(request));n=1 if validate else 33
    h[12:16]=[0,3,n,0xffffffff];h[16:20]=[1000000,0 if validate else 500,1000,1000000];h[20:28]=[m.SIGNATURE,1,4,0,128,2048,4096,0]
    records=[]
    for i in range(n):
        kind=3 if validate else (0 if i==0 else (1 if i<=30 else 2));dt=10000+i
        values=[i,kind,0,0,1 if validate else 6,0,8527,21529,0,token,score,crc,int(not validate),0,0,0,
                2000+i*20000,2000+i*20000+dt,dt-1,0,0,0,0,0]
        if validate:values[6:13]=[0]*7
        records.append(m.RECORD.pack(*values))
    return request,m.HEADER.pack(*h),b''.join(records)

class PrivateMailbox(unittest.TestCase):
    def test_counts_and_nearest_rank(self):
        result=m.parse_capture(*fixture());self.assertEqual(result['measurement_calls'],30)
        self.assertAlmostEqual(result['token_ready_median_ms'],10.0155)
        self.assertAlmostEqual(result['token_ready_p95_ms'],10.029)
        self.assertAlmostEqual(result['m14_equivalent_tokens_per_second'],1000000/10015.5)
        self.assertEqual(result['ttft'],'NOT_MEASURED')
    def test_validate_has_no_throughput(self):
        result=m.parse_capture(*fixture(True));self.assertEqual(result['command'],'VALIDATE_ONLY')
        self.assertNotIn('m14_equivalent_tokens_per_second',result)
    def test_stale_nonce_rejected(self):
        request,h,r=fixture();words=list(m.HEADER.unpack(h));words[11]^=1
        with self.assertRaises(ValueError):m.parse_capture(request,m.HEADER.pack(*words),r)
    def test_incomplete_failed_wrong_image(self):
        request,h,r=fixture()
        for field,value in [(12,6),(13,2),(14,32),(15,0),(16,0),(20,0),(21,0),(24,64)]:
            words=list(m.HEADER.unpack(h));words[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):m.parse_capture(request,m.HEADER.pack(*words),r)
    def test_invalid_call_results_and_timestamps(self):
        request,h,r=fixture()
        for field,value in [(0,4),(1,1),(2,0xfffffff8),(4,5),(7,0),(9,1),(12,0),(13,1),(17,1)]:
            first=list(m.RECORD.unpack(r[:128]));first[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):m.parse_capture(request,h,m.RECORD.pack(*first)+r[128:])
    def test_truncated_records(self):
        request,h,r=fixture()
        with self.assertRaises(ValueError):m.parse_capture(request,h,r[:-1])
    def test_expected_contract_rejected_even_with_matching_header(self):
        request,h,r=fixture();rq=list(m.HEADER.unpack(request));head=list(m.HEADER.unpack(h))
        rq[10]^=1;head[10]=rq[10]
        with self.assertRaises(ValueError):m.parse_capture(m.HEADER.pack(*rq),m.HEADER.pack(*head),r)
    def test_request_invalid_configuration(self):
        meta={'expected':{'token':20412,'score_bits':'0x41de477c','crc32':'1c6404e7'},'image_digest':{'crc32':'d1a10b86'}}
        for kwargs in [dict(warmups=9),dict(measurements=0),dict(stability=1001)]:
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):m.prepare_request(meta,**kwargs)
        meta['expected']['crc32']='0'
        with self.assertRaises(ValueError):m.prepare_request(meta)

if __name__=='__main__':unittest.main()
