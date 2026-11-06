"""Replay actual wire handshakes; compare all gate variants without rerunning tools."""
from pathlib import Path
import csv,json,hashlib,tarfile,re,datetime,collections,sys
from review_memory_growth_20261103 import ready,ROOT,M,sha

ARCHIVES={1:'7bc4e2d446b03459c9f13a59d4b60883939b8f99432fa65969af33920c9a2d92',2:'d5f7c420728aeda0c11f682d34df5c37711dfb0579d70594ea858b5c6f831686',3:'8a973c9d4e187c9114627dad09a6f7c0068689f64024a90aa30f099d0a79084d',4:'a10331a427b0ead77c3e6e94f2d17cfd37dd30d517665dd1f604d935aa83b9c3',5:'8bb84d6f18a57d49f20a33217d818ce369e35e178ad4a4fdc3a925989bdeafca'}

def extract(i,h):
 a=ROOT/('.cache/memory_axi_gate_20261103_r%d_result.tar.gz'%i);assert sha(a)==h
 with tarfile.open(a) as t:
  for member in t.getmembers():
   p=(ROOT/member.name).resolve();assert ROOT in p.parents and member.isfile()
   data=t.extractfile(member).read()
   if p.exists():assert p.read_bytes()==data,str(p)
   else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)

def replay(path,read_bursts=1026):
 memory=bytearray((i*17+3)&255 for i in range(1048576));reads=collections.deque();writes=collections.deque()
 counts=collections.Counter();lastcycle=0;maxout=0
 for row in csv.reader(path.open()):
  kind=row[0];cycle=int(row[1]);assert cycle>=lastcycle;lastcycle=cycle
  counts[kind]+=1;assert int(row[2])==counts[kind]
  if kind in ['AR','AW']:
   addr,n=int(row[3]),int(row[4])+1
   assert addr%16==0 and n in [16,128] and addr+n*16<=len(memory) and addr//4096==(addr+n*16-1)//4096
   (reads if kind=='AR' else writes).append([addr,n,0]);maxout=max(maxout,len(reads));assert len(reads)<=4
  elif kind in ['R','W']:
   q=reads if kind=='R' else writes;assert q
   a,n,k=q[0];addr=a+k*16;data=int(row[3],16).to_bytes(16,'little')
   if kind=='R':assert data==memory[addr:addr+16],(cycle,addr,data.hex(),memory[addr:addr+16].hex())
   else:
    mask=int(row[4],16);assert mask in [0x5555,0xaaaa]
    for lane in range(16):
     if (mask>>lane)&1:memory[addr+lane]=data[lane]
   assert int(row[-1])==int(k==n-1)
   q[0][2]+=1
   if k==n-1:q.popleft()
  elif kind=='B':assert int(row[3])==0
  else:raise AssertionError(kind)
 assert not reads and not writes and dict(counts)==dict(AR=read_bursts,R=131104,AW=2,W=32,B=2)
 return dict(counts=counts,final_cycle=lastcycle,max_outstanding_reads=maxout)

def math_check():
 # Same lane selection for old loop and direct expression, including malformed left_len.
 cases=0
 for bus in [1,2,4,8,16,32,64,128]:
  for size in range(bus.bit_length()):
   bytenum=1<<size
   for addr in [0,1,7,15,31,4093,2**32+37,2**40+127]:
    for length in [0,1,2,15,31,127,255]:
     for left in set([0,1,length+1,length+2,max(1,length//2)]):
      low=addr;cnt=addr//bus*bus;old=[]
      for j in range(length+1):
       if length+1-j==left:old=[cnt+i if low<=cnt+i<low//bytenum*bytenum+bytenum else None for i in range(bus)]
       low=low//bytenum*bytenum+bytenum;cnt=low//bus*bus
      j=length+1-left;low=addr if j<=0 else (addr//bytenum+j)*bytenum;cnt=low//bus*bus
      new=[cnt+i if low<=cnt+i<low//bytenum*bytenum+bytenum else None for i in range(bus)] if 0<=j<=length else []
      assert old==new;(cases:=cases+1)
 return cases

def main():
 for i,h in ARCHIVES.items():extract(i,h)
 count=int(sys.argv[1]) if len(sys.argv)>1 else 5
 baseline=M/'reports/memory_axi_gate_20261103_r1/mode_axi/axi_wire.csv';bh=sha(baseline);result={}
 math_cases=math_check()
 for i in range(1,count+1):
  name='memory_axi_gate_20261103_r%d'%i;r,p,w=ready(name);e=M/'experiments'/name;wire=r/'mode_axi/axi_wire.csv'
  assert sha(wire)==bh,'Observed wire trace changed: '+name
  traffic=replay(wire);samples=[[int(x) for x in row] for row in csv.reader((r/'mode_axi/axi_epoch_samples.csv').open())]
  assert [x[0] for x in samples]==list(range(5)) and all(x[-1]==0 for x in samples)
  assert samples[-1][3:8]==[1026,131104,2,32,2]
  log=(r/'mode_axi/tool.log').read_text();assert any(x.startswith('AXI_GATE_PASS ') for x in log.splitlines())
  assert not any(x.startswith(('UVM_ERROR','UVM_FATAL','ERROR:','Fatal:')) and not re.fullmatch(r'UVM_(?:ERROR|FATAL)\s*:\s*0\s*',x) for x in log.splitlines())
  sources=json.loads((r/'COMPILED_SOURCES.json').read_text())
  for n in ['axi_transfer.sv','axi_state.sv','axi_slave_seq_lib.sv']:
   if (e/n).exists():assert sources['axivip/'+n]==sha(e/n)
  assert sources['file_agent/mem_model.sv']==p['model_sha256']
  out={'state':'PASS_INDEPENDENT_REAL_AXI_WIRE_EQUIVALENCE','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'wire_sha256':bh,'traffic':traffic,'source_sha256':sources,'kernel_growth_mib':(samples[-1][2]-samples[0][2])/1024,'epoch_samples':samples,'mode_metrics':w['phases']['mode_axi'],'direct_beat_lane_math_cases':math_cases,'limits':['No M14 compute/FIFO/FP32 qualification','Aligned 128-bit traffic / single ID; generic lane math checked separately','Passing traffic does not imply bounded memory; growth explicitly reported']}
  (r/'INDEPENDENT_REVIEW.json').write_text(json.dumps(out,indent=2)+'\n');result[name]={k:out[k] for k in ['kernel_growth_mib','mode_metrics','wire_sha256']}
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
