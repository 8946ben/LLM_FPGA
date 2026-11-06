from pathlib import Path
import json,hashlib,tarfile,shutil,subprocess,os,signal,datetime,csv
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
E=ROOT/'module_14_lm_head_v4/experiments/perf_observer_20261026';R=ROOT/'module_14_lm_head_v4/reports/perf_observer_20261026_r1'
V=ROOT/'.cache/p64_perf_observer_20261026_r1';OLD=ROOT/'.cache/p64_rtl_full_r3/hls/solution1/sim/verilog'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
archive=ROOT/'perf_observer_entry_20261026.tar.gz';assert sha(archive)=='9334f862031b8d5c5e3505f663c3bc4c7154f3b1c5201caf7db1b6e9010a4983'
assert not V.exists()
with tarfile.open(archive) as t:
 for m in t.getmembers():
  p=(ROOT/m.name).resolve();assert ROOT in p.parents and m.isfile();assert not p.exists()
  p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(t.extractfile(m).read())
plan=json.loads((R/'PLAN.json').read_text())
for n,h in plan['source_sha256'].items():assert sha(ROOT/n)==h
shutil.copytree(OLD,V,ignore=shutil.ignore_patterns('*.log','*.wdb','*.vcd','*.jou','*.rpt'))
for p in E.iterdir():shutil.copy2(p,V/p.name)
assert sha(V/'lm_head_v4_partial_proto.v')==plan['top_rtl_sha256']
patch=ROOT/'module_14_lm_head_v4/experiments/sim_memory_bank_20261026/mem_model.sv'
assert sha(patch)=='dbd8c2f56a27aad3aa5264a473f8c3da6728dd3f7f2f691b107d2b009cfeede4'
shutil.copy2(patch,V/'file_agent/mem_model.sv')
(R/'DEPENDENCIES.json').write_text(json.dumps(dict(top_rtl_sha256=sha(V/'lm_head_v4_partial_proto.v'),memory_model_sha256=sha(patch),no_rtl_or_stall_change=True),indent=2)+'\n')
(V/'observer_unit.prj').write_text('sv xil_defaultlib "stage_observer.sv"\nsv xil_defaultlib "observer_tb.sv"\n')
project=(V/'lm_head_v4_partial_proto.prj').read_text()+'\nsv xil_defaultlib "stage_observer.sv"\nsv xil_defaultlib "stage_bind.sv"\n'
(V/'observer_bind.prj').write_text(project)
state=dict(state='EXECUTING',started=stamp(),parent_pid=os.getpid(),parent_proc_stat=Path('/proc/self/stat').read_text(),automatic_next_stage=False,board='NOT_RUN')
def save():(R/'WORKFLOW.json').write_text(json.dumps(state,indent=2)+'\n')
def run(phase,command):
 state['phase']=phase;save()
 with (R/(phase+'.log')).open('w') as out:
  p=subprocess.Popen(['bash','-c','source /tools/Xilinx/Vitis/2022.2/settings64.sh >/dev/null 2>&1; exec '+command],cwd=V,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
  state.update(child_pid=p.pid,child_pgid=os.getpgid(p.pid),command=command);save()
  try:rc=p.wait(timeout=300)
  except subprocess.TimeoutExpired:
   os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
   raise AssertionError('observer timeout: '+phase)
  assert rc==0,(phase,rc)
(R/'ACTIVE.lock').write_text(str(os.getpid()));save()
try:
 run('unit_elaborate','/tools/Xilinx/Vivado/2022.2/bin/xelab xil_defaultlib.observer_tb -prj observer_unit.prj -debug all -s observer_unit_r1')
 run('unit_simulate','/tools/Xilinx/Vivado/2022.2/bin/xsim observer_unit_r1 -testplusarg PROFILE_PATH=unit_profile.csv -runall')
 shutil.copy2(V/'unit_profile.csv',R/'unit_profile.csv')
 with (V/'unit_profile.csv').open() as f:actual=[{k:int(v) for k,v in row.items()} for row in csv.DictReader(f)]
 expected=json.loads((E/'expected_unit.json').read_text());assert len(actual)==len(expected)
 for a,e in zip(actual,expected):
  for k,value in e.items():assert a[k]==value,(a,e,k)
 first=next(x.strip() for x in (V/'run_xsim.sh').read_text().splitlines() if x.strip().startswith('/tools/Xilinx/Vivado/2022.2/bin/xelab '))
 assert first.endswith('-s lm_head_v4_partial_proto')
 command=first.replace('-prj lm_head_v4_partial_proto.prj','-prj observer_bind.prj').replace('-s lm_head_v4_partial_proto','-debug all -s observer_actual_bind_r1')
 run('actual_bind_elaborate',command)
 for n,h in plan['source_sha256'].items():assert sha(ROOT/n)==h,n
 state.update(state='TOOL_PASS_AWAITING_INDEPENDENT_REVIEW',finished=stamp())
except BaseException as e:state.update(state='FAILED_NO_AUTOMATIC_RETRY',error=repr(e),finished=stamp())
finally:save();(R/'ACTIVE.lock').unlink(missing_ok=True)
print(json.dumps(state,indent=2))
