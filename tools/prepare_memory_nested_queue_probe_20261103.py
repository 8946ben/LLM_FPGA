from pathlib import Path
import hashlib,json,tarfile
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';E=M/'experiments/memory_nested_queue_probe_20261103';R=M/'reports/memory_nested_queue_probe_20261103_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 E.mkdir(exist_ok=True);R.mkdir(exist_ok=True);assert not (R/'PLAN.json').exists()
 old=(M/'experiments/memory_allocation_micro_20261103_r2/allocation_tb.sv').read_text()
 a=old.index('class plain_packet;');b=old.index('task automatic sample',a)
 old=old[:a]+'''integer mode,n,fd,i,j,done_children;
longint unsigned checksum;
int nested[][$];int flat[$];int dyn[];
bit clk=0;always #0.5 clk=~clk;
'''+old[b:]
 a=old.index(' source=new(');b=old.index(' #10;',a)
 old=old[:a]+''' nested=new[1];nested[0].push_back(1);flat.push_back(1);dyn=new[1];dyn[0]=1;
 checksum=0;sample(0);
 for(i=0;i<n;i++)begin
  case(mode)
   0:checksum=0;
   1:begin nested[0][0]++;checksum=nested[0][0]-1;end
   2:begin flat[0]++;checksum=flat[0]-1;end
   3:begin dyn[0]++;checksum=dyn[0]-1;end
   4:checksum+=nested[0].size();
   5:checksum+=nested[0][0];
  endcase
  #1;
  if((i+1)%(n/4)==0)sample(i+1);
 end
 if(mode!=0 && checksum!=n)$fatal(1,"counter mismatch");
'''+old[b:]
 old=old.replace(' if(mode==5 && done_children!=n)$fatal(1,"fork children unfinished");','')
 (E/'allocation_tb.sv').write_text(old)
 s=(ROOT/'tools/run_memory_allocation_micro_20261103.py').read_text().replace('experiments/memory_allocation_micro_20261103_r2','experiments/memory_nested_queue_probe_20261103').replace('reports/memory_allocation_micro_20261103_r2','reports/memory_nested_queue_probe_20261103_r1').replace('.cache/memory_allocation_micro_20261103_r2','.cache/memory_nested_queue_probe_20261103_r1').replace('-testplusarg N=100000','-testplusarg N=1000000')
 (E/'run_micro.py').write_text(s)
 plan={'state':'FROZEN_NESTED_QUEUE_OPERATION_CONTROL','sources':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in E.iterdir() if p.is_file()},'n':1000000,
 'cases':['idle','dynamic array of queue counter','flat queue counter','dynamic array counter','nested queue size','nested queue read'],
 'full_m14':'NOT_RUN','board':'NOT_RUN','automatic_next_stage':False}
 (R/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
 with tarfile.open(R/'entry.tar.gz','w:gz') as a:
  for p in list(E.iterdir())+[R/'PLAN.json']:a.add(p,arcname=str(p.relative_to(ROOT)))
 print(json.dumps({'archive':str(R/'entry.tar.gz'),'sha256':sha(R/'entry.tar.gz')}))
if __name__=='__main__':main()
