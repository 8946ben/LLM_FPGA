from pathlib import Path
import hashlib,json,tarfile
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';E=M/'experiments/memory_reuse_probe_20261103';R=M/'reports/memory_reuse_probe_20261103_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 E.mkdir(exist_ok=True);R.mkdir(exist_ok=True);assert not (R/'PLAN.json').exists()
 t=(M/'experiments/memory_allocation_micro_20261103_r2/allocation_tb.sv').read_text()
 t=t.replace('checksum=0;done_children=0;sample(0);','''checksum=0;done_children=0;
 if(mode==6)begin plain=new();for(j=0;j<16;j++)plain.data.push_back(j);end
 if(mode==7 || mode==8)begin packet=new("reused");for(j=0;j<16;j++)packet.data.push_back(j);end
 sample(0);''')
 t=t.replace('   default:$fatal(1,"bad mode");','''   6:begin for(j=0;j<16;j++)plain.data[j]=(i+j)&255;checksum+=plain.data[0];end
   7:begin for(j=0;j<16;j++)packet.data[j]=(i+j)&255;checksum+=packet.data[0];end
   8:begin packet.init();for(j=0;j<16;j++)packet.data.push_back((i+j)&255);checksum+=packet.data[0];end
   default:$fatal(1,"bad mode");''')
 (E/'allocation_tb.sv').write_text(t)
 s=(ROOT/'tools/run_memory_allocation_micro_20261103.py').read_text().replace('experiments/memory_allocation_micro_20261103_r2','experiments/memory_reuse_probe_20261103').replace('reports/memory_allocation_micro_20261103_r2','reports/memory_reuse_probe_20261103_r1').replace('.cache/memory_allocation_micro_20261103_r2','.cache/memory_reuse_probe_20261103_r1')
 start=s.index("  run('elaborate',");end=s.index("  state.update(state='TOOL_PASS",start)
 s=s[:start]+'''  for debug in ['all','default']:
   flag=' -debug all' if debug=='all' else ''
   snap='reuse_'+debug
   run('elaborate_'+debug,'/tools/Xilinx/Vivado/2022.2/bin/xelab xil_defaultlib.allocation_tb -prj micro.prj -L uvm -L xil_defaultlib -i ./axivip -relax'+flag+' -s '+snap)
   for mode in [2,6,7,8]:
    run('mode_'+debug+'_'+str(mode),'/tools/Xilinx/Vivado/2022.2/bin/xsim '+snap+' -runall -testplusarg MODE='+str(mode)+' -testplusarg N=1000000')
'''+s[end:]
 compile(s,'run_reuse.py','exec');(E/'run_micro.py').write_text(s)
 plan={'state':'FROZEN_REUSE_AND_DEBUG_CONTROL','sources':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in E.iterdir() if p.is_file()},
 'cases':['new AXI each iteration','reuse plain and overwrite data','reuse AXI overwrite data','reuse AXI init/delete then refill'],'n':1000000,'debug':['all','default no -debug option'],
 'full_m14':'NOT_RUN','board':'NOT_RUN','automatic_next_stage':False}
 (R/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
 with tarfile.open(R/'entry.tar.gz','w:gz') as a:
  for p in list(E.iterdir())+[R/'PLAN.json']:a.add(p,arcname=str(p.relative_to(ROOT)))
 print(json.dumps({'archive':str(R/'entry.tar.gz'),'sha256':sha(R/'entry.tar.gz')}))
if __name__=='__main__':main()
