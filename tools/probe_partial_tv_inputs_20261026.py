"""Inspect original CoSim input TV against frozen binary; no EDA or source writes."""
from pathlib import Path
import hashlib,json,datetime
import numpy as np
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
SOL=ROOT/'.cache/p64_rtl_full_r3/hls/solution1'
TV=SOL/'sim/tv/cdatafile/c.lm_head_v4_partial_proto.autotvin_weights.dat'
W=ROOT/'module_14_lm_head_v4/reports/layout_topk_20261024_r1/assets/tiled_W_B1024.bin'
CAN=ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
with TV.open('rb') as f:
 header=f.readline()+f.readline();origin=f.tell();line=f.readline();width=len(line)
 assert line.startswith(b'0x') and width==35
 a=np.memmap(W,dtype='V16',mode='r');c=np.memmap(CAN,dtype='V16',mode='r')
 records=[]
 for tile in range(7):
  start=tile*896*128;f.seek(origin+start*width);raw=f.read(896*128*width)
  v=b''.join(int(s,16).to_bytes(16,'little') for s in raw.splitlines())
  expected=a[start:start+896*128].tobytes();bad=np.flatnonzero(np.frombuffer(v,'V16')!=np.frombuffer(expected,'V16'))
  records.append(dict(tile=tile,beats=896*128,mismatches=len(bad),first_bad=bad[:10].tolist(),actual_sha256=hashlib.sha256(v).hexdigest(),expected_sha256=hashlib.sha256(expected).hexdigest()))
 f.seek(origin+len(a)*width);v=b''.join(int(f.readline(),16).to_bytes(16,'little') for _ in range(1024))
 canonical_start=dict(beats=1024,equal=v==c[:1024].tobytes())
print(json.dumps(dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),tv=str(TV),header=header.decode(),record_bytes=width,tiled_binary_sha256=sha(W),canonical_binary_sha256=sha(CAN),tiled_first7=records,canonical_start=canonical_start),indent=2))
