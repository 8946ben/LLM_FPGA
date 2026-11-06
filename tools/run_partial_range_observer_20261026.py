from pathlib import Path
import json,tarfile,hashlib,shutil,subprocess,os,signal,datetime,re
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
E=ROOT/'module_14_lm_head_v4/experiments/full_bank_cosim_20261026';R=ROOT/'module_14_lm_head_v4/reports/range_observer_20261026_r1'
V=ROOT/'.cache/p64_range_observer_20261026_r1';OLD=ROOT/'.cache/p64_rtl_full_r3/hls/solution1/sim/verilog'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
archive=ROOT/'range_observer_entry_20261026.tar.gz'
assert not V.exists()
with tarfile.open(archive) as t:
 for m in t.getmembers():
  p=(ROOT/m.name).resolve();assert ROOT in p.parents and m.isfile();data=t.extractfile(m).read()
  if p.exists():assert p.read_bytes()==data
  else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
plan=json.loads((R/'PLAN.json').read_text())
for n,h in plan['source_sha256'].items():assert sha(ROOT/n)==h,n
shutil.copytree(OLD,V,ignore=shutil.ignore_patterns('*.log','*.wdb','*.vcd','*.jou','*.rpt','*.csv','*.zip'))
for name in ['range_observer.sv','range_tb.sv','range_bind.sv']:shutil.copy2(E/name,V/name)
(V/'range_unit.prj').write_text('sv xil_defaultlib "range_observer.sv"\nsv xil_defaultlib "range_tb.sv"\n')
(V/'range_bind.prj').write_text((V/'lm_head_v4_partial_proto.prj').read_text()+'\nsv xil_defaultlib "range_observer.sv"\nsv xil_defaultlib "range_bind.sv"\n')
state=dict(state='EXECUTING',parent_pid=os.getpid(),parent_proc_stat=Path('/proc/self/stat').read_text(),automatic_next_stage=False)
def save():(R/'WORKFLOW.json').write_text(json.dumps(state,indent=2)+'\n')
def run(name,command,limit=120):
 state['phase']=name;save()
 with (R/(name+'.log')).open('w') as out:
  p=subprocess.Popen(['bash','-c','source /tools/Xilinx/Vitis/2022.2/settings64.sh >/dev/null 2>&1; exec '+command],cwd=V,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
  state.update(child_pid=p.pid,child_pgid=os.getpgid(p.pid));save()
  try:code=p.wait(timeout=limit)
  except subprocess.TimeoutExpired:
   os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
   raise AssertionError(name+' timeout')
 return code,(R/(name+'.log')).read_text()
(R/'ACTIVE.lock').write_text(str(os.getpid()));save()
try:
 code,log=run('unit_elaborate','/tools/Xilinx/Vivado/2022.2/bin/xelab xil_defaultlib.range_tb -prj range_unit.prj -debug all -s range_unit_r1');assert code==0
 results=[]
 for mode in range(7):
  code,log=run('mode'+str(mode),'/tools/Xilinx/Vivado/2022.2/bin/xsim range_unit_r1 -testplusarg MODE='+str(mode)+' -runall')
  done=bool(re.search(r'^RANGE_UNIT_DONE mode='+str(mode)+r'$',log,re.M));reject=bool(re.search(r'^Fatal: RANGE_OBSERVER_REJECT ',log,re.M))
  if mode==0:assert code==0 and done and not reject and 'meta_read_bursts=2 meta_write_bursts=1 weight_read_bursts=3' in log
  else:assert reject and not done,(mode,code,log)
  results.append(dict(mode=mode,return_code=code,completed=done,rejected=reject))
 first=next(x.strip() for x in (V/'run_xsim.sh').read_text().splitlines() if x.strip().startswith('/tools/Xilinx/Vivado/2022.2/bin/xelab '))
 command=first.replace('-prj lm_head_v4_partial_proto.prj','-prj range_bind.prj').replace('-s lm_head_v4_partial_proto','-debug all -s range_actual_bind_r1')
 code,log=run('actual_bind_elaborate',command,300);assert code==0 and 'Built simulation snapshot range_actual_bind_r1' in log
 for n,h in plan['source_sha256'].items():assert sha(ROOT/n)==h,n
 (R/'UNIT_RESULT.json').write_text(json.dumps(dict(state='TOOL_PASS_RANGE_UNIT_AND_BIND',cases=results,real_bind='elaboration only; actual M14 NOT_RUN',no_driven_dut_ports=True),indent=2)+'\n')
 state['state']='TOOL_PASS_AWAITING_INDEPENDENT_REVIEW'
except BaseException as e:state.update(state='FAILED_NO_AUTOMATIC_RETRY',error=repr(e))
finally:save();(R/'ACTIVE.lock').unlink(missing_ok=True)
print(json.dumps(state,indent=2))
