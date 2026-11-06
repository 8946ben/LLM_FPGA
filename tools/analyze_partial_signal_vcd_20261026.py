"""Parse edge-sampled original AXI transactions; no simulator or design writes."""
from pathlib import Path
from collections import deque
import sys,json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261026_diagnosis_r1'
vcd=Path(sys.argv[1]);out=Path(sys.argv[2])
w=np.memmap(ROOT/'module_14_lm_head_v4/reports/layout_topk_20261024_r1/assets/tiled_W_B1024.bin','V16',mode='r')
ids={};state={};changes={};time=0;reads=[];writes=[];ar=deque();aw=deque();pending_w=deque();burst=[]
def number(x):
 if x is None or 'x' in x.lower() or 'z' in x.lower():return None
 return int(x,2)
def edge():
 global state,changes
 cur=state.copy();cur.update(changes)
 if number(state.get('ap_clk'))==0 and number(cur.get('ap_clk'))==1:
  n=lambda k:number(state.get(k))
  if n('weights_ARVALID')==1 and n('weights_ARREADY')==1:
   address=n('weights_ARADDR');count=n('weights_ARLEN')+1
   ar.append([address,count]);burst.append(dict(time_ps=time,address=address,beats=count))
  if n('weights_RVALID')==1 and n('weights_RREADY')==1:
   assert ar,'Data without queued AR'
   address,count=ar[0];data=n('weights_RDATA');expected=int.from_bytes(w[address//16].tobytes(),'little')
   reads.append(dict(time_ps=time,address=address,actual=hex(data) if data is not None else None,expected=hex(expected),equal=data==expected))
   assert n('weights_RLAST')==(count==1)
   if count==1:ar.popleft()
   else:ar[0]=[address+16,count-1]
  if n('meta_AWVALID')==1 and n('meta_AWREADY')==1:aw.append([n('meta_AWADDR'),n('meta_AWLEN')+1])
  if n('meta_WVALID')==1 and n('meta_WREADY')==1:pending_w.append((n('meta_WDATA'),n('meta_WSTRB'),n('meta_WLAST'),time))
  while aw and pending_w:
   address,count=aw[0];data,strobe,last,t=pending_w.popleft()
   writes.append(dict(time_ps=t,address=address,data=hex(data) if data is not None else None,strobe=strobe,last=last))
   assert last==(count==1)
   if count==1:aw.popleft()
   else:aw[0]=[address+16,count-1]
 state=cur;changes={}
with vcd.open() as f:
 header=True
 for line in f:
  # A live-file prefix may end inside a timestamp/value; do not parse it.
  if not line.endswith('\n'):break
  line=line.strip()
  if header:
   if line.startswith('$var '):
    fields=line.split();ids[fields[3]]=fields[4]
   if line=='$enddefinitions $end':header=False
   continue
  if not line or line.startswith('$'):continue
  if line.startswith('#'):
   edge();nexttime=int(line[1:]);assert nexttime>=time;time=nexttime;continue
  if line.startswith('b'):
   b,i=line[1:].split()
  else:b,i=line[0],line[1:]
  if i in ids:changes[ids[i]]=b
edge()
bad=[x for x in reads if not x['equal']]
result=dict(state='AXI_TRACE_PARSED',trace_sha256=hashlib.sha256(vcd.read_bytes()).hexdigest(),
 last_time_ps=time,read_beats=len(reads),input_mismatches=len(bad),first_mismatches=bad[:16],ar_bursts=len(burst),
 first_bursts=burst[:8],write_beats=len(writes),last_writes=writes[-8:],
 sampling='At rising clock use all values stable immediately before that timestamp; RLAST and AR queue checked')
out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
