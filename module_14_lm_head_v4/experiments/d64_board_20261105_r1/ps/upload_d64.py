"""D64A loader client. Default verifieslocalimageonly;network needs explicitflag."""
from pathlib import Path
import argparse,json,hashlib,zlib,struct,socket
MAGIC=0x41343644;VERSION=1;SIZE=603979776;CHUNK=1048576;BASE=0x400000000;H=struct.Struct('<8I')
def need(v,message):
 if not v:raise ValueError(message)
def inspect(image,manifest):
 image=Path(image);m=json.loads(Path(manifest).read_text());need(m['image_bytes']==image.stat().st_size==SIZE,'Image size');need(int(m['physical_base'],0)==BASE,'Physicalbase');need(len(m['chunks'])==576 and m['chunk_bytes']==CHUNK,'Chunk count')
 sha=hashlib.sha256();crc=0
 with image.open('rb') as f:
  for i,item in enumerate(m['chunks']):
   data=f.read(CHUNK);need(item['offset']==i*CHUNK and item['bytes']==len(data)==CHUNK,'Chunkbounds');need(f'{zlib.crc32(data):08x}'==item['crc32'],'ChunkCRC');sha.update(data);crc=zlib.crc32(data,crc)
  need(not f.read(1),'Image trailing bytes')
 need(sha.hexdigest()==m['image_sha256'] and f'{crc:08x}'==m['image_crc32'],'ImageSHA/CRC')
 need(m['weight_sources']['canonical_weight']['sha256']=='4e96b0df6d274768cbb7e72404011853d23349999b658dc2f4dfb3c431ea223f','Canonicalweight identity')
 return m
def receive(s,n):
 out=bytearray()
 while len(out)<n:
  b=s.recv(n-len(out));need(b,'Connectionclosed');out.extend(b)
 return bytes(out)
def exchange(s,op,seq,offset,size,crc,payload=b''):
 need(len(payload)==size,'Requestpayloadsize');s.sendall(H.pack(MAGIC,VERSION,op,seq,offset,size,SIZE,crc)+payload);r=H.unpack(receive(s,32));need(r[:4]==(MAGIC,VERSION,op|0x80000000,seq) and r[5]==0 and r[6]==SIZE,'Responseidentity/status')
 if op==5:
  need(r[4]==offset,'READoffset');body=receive(s,crc);need(zlib.crc32(body)==r[7],'READtargetCRC');return body
 return r
def main():
 ap=argparse.ArgumentParser();ap.add_argument('image',type=Path);ap.add_argument('manifest',type=Path);g=ap.add_mutually_exclusive_group();g.add_argument('--upload',metavar='HOST');g.add_argument('--read-only',metavar='HOST');ap.add_argument('--out',type=Path);a=ap.parse_args();m=inspect(a.image,a.manifest)
 if not (a.upload or a.read_only):print('PASS_LOCAL_IMAGE_ONLY_NO_SOCKET');return
 with socket.create_connection((a.upload or a.read_only,1416),timeout=180) as s:
  if a.upload:
   expected=int(m['image_crc32'],16);r=exchange(s,1,0,0,0,expected);need(r[4]==0 and r[7]==expected,'BEGIN')
   with a.image.open('rb') as f:
    for i,item in enumerate(m['chunks']):
     data=f.read(CHUNK);r=exchange(s,2,i+1,item['offset'],len(data),int(item['crc32'],16),data);need(r[4]==(i+1)*CHUNK and r[7]==int(item['crc32'],16),'DATA targetCRC')
   r=exchange(s,3,577,SIZE,0,expected);need(r[4]==SIZE and r[7]==expected,'FulltargetCRC')
   with a.image.open('rb') as f:
    for off in [0,273416192-16,273416192,545685504-16,0x21000000,SIZE-16]:f.seek(off);need(exchange(s,5,0,off,0,16)==f.read(16),'Targetsentinel')
   print('PASS_INITIAL_LOAD_FULL_TARGET_CRC_AND_SENTINELS_NOT_KERNEL_OR_DECODE')
  else:
   need(a.out is not None and not a.out.exists(),'Fresh --out required');a.out.mkdir(parents=True);exchange(s,6,0,0,0,0)
   regions=[(f'snapshot_{i:02}.bin',0x21400000+i*0x140000,1289472) for i in range(24)]+[('state_results.bin',0x23d00000,4096),('timing_records.bin',0x23e00000,4*1033*64)]
   for name,offset,size in regions:
    with (a.out/name).open('xb') as f:
     for off in range(0,size,512):f.write(exchange(s,5,0,offset+off,0,min(512,size-off)))
   (a.out/'READBACK.json').write_text(json.dumps(dict(state='RAW_READ_ONLY_RECEIPT_AWAITING_INDEPENDENT_AUDIT',source_image_sha256=m['image_sha256'],host=a.read_only,not_a_new_load_verification=True),indent=2)+'\n');print('RAW_READBACK_ONLY_NOT_ACCEPTANCE')
if __name__=='__main__':main()
