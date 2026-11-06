"""No sockets: fragmented protocol replies and independent rejection cases."""
import unittest
from unittest.mock import patch
import hashlib,json,tempfile
from pathlib import Path
from standalone import upload_arena_tcp as u

class FragmentedSocket:
    def __init__(self,data):self.data=bytearray(data);self.sent=[]
    def sendall(self,data):self.sent.append(bytes(data))
    def recv(self,n):
        n=min(n,3,len(self.data));out=bytes(self.data[:n]);del self.data[:n];return out

def response(op=u.DATA,seq=7,offset=1048576,crc=123,status=0,magic=u.MAGIC,version=1,total=u.IMAGE_BYTES,body=b''):
    return u.HEADER.pack(magic,version,op|0x80000000,seq,offset,status,total,crc)+body

class ArenaTransport(unittest.TestCase):
    def test_fragmented_data_reply(self):
        sock=FragmentedSocket(response())
        self.assertEqual(u.request(sock,u.DATA,7,payload=b'abc',crc=123,expected_offset=1048576),1048576)
        h=u.HEADER.unpack(sock.sent[0]);self.assertEqual(h,(u.MAGIC,1,u.DATA,7,0,3,u.IMAGE_BYTES,123))
        self.assertEqual(sock.sent[1],b'abc')
    def test_wrong_identity_replies(self):
        for fields in [dict(magic=0x5734314D),dict(version=2),dict(total=272269312),dict(seq=8),dict(op=u.COMMIT)]:
            with self.subTest(fields=fields),self.assertRaises(ValueError):
                u.request(FragmentedSocket(response(**fields)),u.DATA,7,crc=123,expected_offset=1048576)
    def test_status_offset_crc_rejections(self):
        for fields in [dict(status=3),dict(offset=0),dict(crc=124)]:
            with self.subTest(fields=fields),self.assertRaises(ValueError):
                u.request(FragmentedSocket(response(**fields)),u.DATA,7,crc=123,expected_offset=1048576)
    def test_read_reply_fragmented(self):
        data=bytes(range(240))
        sock=FragmentedSocket(response(op=u.READ,offset=1048576,crc=u.zlib.crc32(data),body=data))
        self.assertEqual(u.request(sock,u.READ,7,1048576,crc=240,expected_offset=1048576),data)
        self.assertEqual(u.HEADER.unpack(sock.sent[0])[5],0)
    def test_read_crc_rejects_corruption(self):
        sock=FragmentedSocket(response(op=u.READ,offset=0,crc=0,body=b'not target data'))
        with self.assertRaises(ValueError):u.request(sock,u.READ,7,0,crc=15,expected_offset=0)
    def test_read_truncation(self):
        sock=FragmentedSocket(response(op=u.READ,offset=0,crc=0,body=b'ab'))
        with self.assertRaises(RuntimeError):u.request(sock,u.READ,7,0,crc=16,expected_offset=0)
    def test_truncated_header(self):
        with self.assertRaises(RuntimeError):u.request(FragmentedSocket(b'\0'*31),u.BEGIN,0)
    def test_region_hash_truncation(self):
        import io
        with self.assertRaises(ValueError):u.sha_region(io.BytesIO(b'ab'),0,3)
    def test_read_invalid_bounds_before_send(self):
        for offset,n in [(0,0),(0,513),(u.IMAGE_BYTES,1),(-1,16)]:
            sock=FragmentedSocket(b'')
            with self.subTest(offset=offset,n=n),self.assertRaises(ValueError):
                u.request(sock,u.READ,7,offset,crc=n)
            self.assertEqual(sock.sent,[])

class MockArenaPeer:
    """Protocol peer only: CRCs received bytes; READ serves reference image.

    This is deliberately not a physical DDR or lwIP receive-path test.
    """
    def __init__(self,image,corrupt_descriptor=False,bad_crc_seq=None):
        self.stream=Path(image).open('rb');self.reply=bytearray();self.pending=None
        self.next=0;self.seq=1;self.crc=0;self.sha=hashlib.sha256();self.ready=False
        self.reads=0;self.corrupt_descriptor=corrupt_descriptor;self.bad_crc_seq=bad_crc_seq
    def __enter__(self):return self
    def __exit__(self,*args):self.stream.close()
    def settimeout(self,*args):pass
    def setsockopt(self,*args):pass
    def enqueue(self,h,crc,status=0,body=b''):
        self.reply.extend(response(op=h[2],seq=h[3],offset=h[4] if h[2]==u.READ else self.next,crc=crc,status=status,body=body))
    def sendall(self,data):
        if self.pending is not None:
            h=self.pending;self.pending=None
            assert len(data)==h[5] and h[3]==self.seq and h[4]==self.next
            actual=u.zlib.crc32(data);assert actual==h[7]
            self.crc=u.zlib.crc32(data,self.crc);self.sha.update(data);self.next+=len(data);self.seq+=1
            self.enqueue(h,actual^int(self.bad_crc_seq==h[3]));return
        h=u.HEADER.unpack(data);assert (h[0],h[1],h[6])==(u.MAGIC,1,u.IMAGE_BYTES)
        if h[2]==u.BEGIN:
            assert h[3:6]==(0,0,0);self.expected=h[7];self.enqueue(h,h[7])
        elif h[2]==u.DATA:self.pending=h
        elif h[2]==u.COMMIT:
            assert self.next==u.IMAGE_BYTES and h[3]==self.seq and h[7]==self.crc==self.expected
            self.ready=True;self.enqueue(h,self.crc)
        elif h[2]==u.STATUS:
            assert self.ready;self.enqueue(h,self.crc)
        elif h[2]==u.READ:
            assert self.ready and h[5]==0 and 0<h[7]<=512
            self.stream.seek(h[4]);body=self.stream.read(h[7]);assert len(body)==h[7]
            if self.corrupt_descriptor and h[4]==1048576:body=bytes([body[0]^1])+body[1:]
            self.reads+=1;self.enqueue(h,u.zlib.crc32(body),body=body)
        else:raise AssertionError('Unknown request')
    def recv(self,n):
        n=min(n,7,len(self.reply));out=bytes(self.reply[:n]);del self.reply[:n];return out

class ArenaUploadMock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=u.M/'reports/selector_arena_chinese_20261021/MANIFEST.json'
        cls.image=cls.manifest.parent/'arena_production.bin'
        if not cls.image.exists():raise unittest.SkipTest('Full private320MiB fixture not available')
    def test_complete_real_image_with_mock_socket(self):
        peer=MockArenaPeer(self.image)
        with patch.object(u.socket,'create_connection',return_value=peer) as connect:
            result=u.upload(self.image,self.manifest,progress=False)
        self.assertEqual(connect.call_count,1);self.assertEqual(peer.next,u.IMAGE_BYTES)
        self.assertEqual(peer.reads,34);self.assertEqual(peer.sha.hexdigest(),result['image_sha256'])
        self.assertEqual(result['compute_or_quality_acceptance'],'NOT_PERFORMED')
    def test_expected_descriptor_mismatch_despite_valid_wire_crc(self):
        peer=MockArenaPeer(self.image,corrupt_descriptor=True)
        with patch.object(u.socket,'create_connection',return_value=peer),self.assertRaisesRegex(ValueError,'descriptor'):
            u.upload(self.image,self.manifest,progress=False)
    def test_bad_chunk_reply_prevents_commit(self):
        peer=MockArenaPeer(self.image,bad_crc_seq=3)
        with patch.object(u.socket,'create_connection',return_value=peer),self.assertRaisesRegex(ValueError,'Target CRC mismatch'):
            u.upload(self.image,self.manifest,progress=False)
        self.assertFalse(peer.ready);self.assertEqual(peer.next,3*u.CHUNK_BYTES)
    def test_bad_manifest_rejected_before_socket(self):
        original=json.loads(self.manifest.read_text())
        for field,value in [('physical_base','0x0'),('flags',7),('layout_sha256','0'*64),('image_bytes',272269312)]:
            changed=dict(original);changed[field]=value
            with self.subTest(field=field),tempfile.TemporaryDirectory() as temp:
                path=Path(temp)/'MANIFEST.json';path.write_text(json.dumps(changed))
                with patch.object(u.socket,'create_connection',side_effect=AssertionError('No network allowed')) as connect:
                    with self.assertRaises(ValueError):u.upload(self.image,path,progress=False)
                connect.assert_not_called()

if __name__=='__main__':unittest.main()
