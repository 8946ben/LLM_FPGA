from pathlib import Path
import hashlib,json,tarfile
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';E=M/'experiments/memory_random_probe_20261103_r2';R=M/'reports/memory_random_probe_20261103_r2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 E.mkdir(exist_ok=True);R.mkdir(exist_ok=True);assert not (R/'PLAN.json').exists()
 t=(M/'experiments/memory_allocation_micro_20261103_r2/allocation_tb.sv').read_text();a=t.index('class plain_packet;');b=t.index('task automatic sample',a)
 t=t[:a]+'''class original_latency extends axi_latency;
 function new(string name="original_latency");super.new(name);endfunction
 virtual function int get_rdata_lat();
  int delay;
  void'(std::randomize(delay) with {delay dist {0:=8, 0:=1, 256:=1, [0:256]:/2};});
  return delay;
 endfunction
endclass
class compiled_delay;
 rand int delay;
 constraint c {delay dist {0:=8, 0:=1, 256:=1, [0:256]:/2};}
endclass
original_latency original;compiled_delay reused;
integer mode,n,fd,i,j,done_children,delay;
longint unsigned checksum;
bit clk=0;always #0.5 clk=~clk;
'''+t[b:]
 a=t.index(' source=new(');b=t.index(' #10;',a)
 t=t[:a]+''' original=new("original");reused=new();checksum=0;sample(0);
 for(i=0;i<n;i++)begin
  case(mode)
   0:delay=0;
   1:if(!std::randomize(delay) with {delay dist {0:=8, 0:=1, 256:=1, [0:256]:/2};})$fatal(1,"std random fail");
   2:delay=original.get_rdata_lat();
   3:begin if(!reused.randomize())$fatal(1,"class random fail");delay=reused.delay;end
  endcase
  if(delay<0 || delay>256)$fatal(1,"random bound");checksum+=delay;
  #1;if((i+1)%(n/4)==0)sample(i+1);
 end
'''+t[b:]
 t=t.replace(' if(mode==5 && done_children!=n)$fatal(1,"fork children unfinished");','')
 (E/'allocation_tb.sv').write_text(t)
 s=(ROOT/'tools/run_memory_allocation_micro_20261103.py').read_text().replace('experiments/memory_allocation_micro_20261103_r2','experiments/memory_random_probe_20261103_r2').replace('reports/memory_allocation_micro_20261103_r2','reports/memory_random_probe_20261103_r2').replace('.cache/memory_allocation_micro_20261103_r2','.cache/memory_random_probe_20261103_r2').replace('for mode in range(6)','for mode in range(4)').replace('-testplusarg N=100000','-testplusarg N=20000')
 (E/'run_micro.py').write_text(s)
 plan={'state':'FROZEN_ORIGINAL_STALL_RANDOMIZATION_CONTROL','sources':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in E.iterdir() if p.is_file()},'n':20000,
 'cases':['no randomization','std randomize module variable','exact original virtual callback local randomize','reused object compiled same distribution'],
 'scope':'Exact delay dist expression, finite solver allocation diagnosis, no DUT or original pressure modification','full_m14':'NOT_RUN','board':'NOT_RUN','automatic_next_stage':False}
 (R/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
 with tarfile.open(R/'entry.tar.gz','w:gz') as a:
  for p in list(E.iterdir())+[R/'PLAN.json']:a.add(p,arcname=str(p.relative_to(ROOT)))
 print(json.dumps({'archive':str(R/'entry.tar.gz'),'sha256':sha(R/'entry.tar.gz')}))
if __name__=='__main__':main()
