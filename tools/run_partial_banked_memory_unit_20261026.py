from pathlib import Path
import json,hashlib,tarfile,shutil,subprocess,datetime,os,signal
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
E=ROOT/'module_14_lm_head_v4/experiments/sim_memory_bank_20261026';R=ROOT/'module_14_lm_head_v4/reports/sim_memory_bank_20261026_r1'
V=ROOT/'.cache/p64_bank_memory_20261026_r1/sim/verilog';OLD=ROOT/'.cache/p64_rtl_full_r3/hls/solution1/sim/verilog'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
archive=ROOT/'bank_memory_entry_20261026.tar.gz'
assert sha(archive)=='0ab01b40c27ee8e3faf02441f67aa57fc314090e2a5a10d400b27a8d2efaae81'
assert not V.exists()
with tarfile.open(archive) as t:
 for m in t.getmembers():
  p=(ROOT/m.name).resolve();assert ROOT in p.parents and m.isfile()
  assert not p.exists()
  p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(t.extractfile(m).read())
plan=json.loads((R/'PLAN.json').read_text())
for n,h in plan['source_sha256'].items():assert sha(ROOT/n)==h
shutil.copytree(OLD,V,ignore=shutil.ignore_patterns('*.log','*.wdb','*.vcd','*.jou','*.rpt'))
assert sha(V/'file_agent/mem_model.sv')==plan['original_model_sha256']
shutil.copy2(E/'mem_model.sv',V/'file_agent/mem_model.sv');shutil.copy2(E/'bank_memory_tb.sv',V/'bank_memory_tb.sv')
unchanged={}
for p in OLD.rglob('*'):
 if p.is_file() and p.suffix in ['.v','.sv'] and p.relative_to(OLD)!=Path('file_agent/mem_model.sv'):
  q=V/p.relative_to(OLD);assert sha(q)==sha(p);unchanged[str(p.relative_to(OLD))]=sha(p)
(R/'RTL_AND_STALL_REUSE.json').write_text(json.dumps(unchanged,indent=2)+'\n')
(V/'bank_memory.prj').write_text('sv xil_defaultlib "file_agent/file_agent_pkg.sv"\nsv xil_defaultlib "bank_memory_tb.sv"\n')
s=dict(state='EXECUTING_UNIT',started=stamp(),parent_pid=os.getpid(),parent_proc_stat=Path('/proc/self/stat').read_text(),automatic_next_stage=False,board='NOT_RUN')
(R/'ACTIVE.lock').write_text(str(os.getpid()))
def save(): (R/'UNIT_WORKFLOW.json').write_text(json.dumps(s,indent=2)+'\n')
save()
try:
 commands=[('elaborate','/tools/Xilinx/Vivado/2022.2/bin/xelab xil_defaultlib.bank_memory_tb -prj bank_memory.prj -L uvm -L xil_defaultlib -i ./file_agent -relax -debug all -s bank_memory_unit_r1'),
           ('simulate','/tools/Xilinx/Vivado/2022.2/bin/xsim bank_memory_unit_r1 -runall')]
 for phase,command in commands:
  s['phase']=phase;save()
  with (R/(phase+'.log')).open('w') as out:
   p=subprocess.Popen(['bash','-c','source /tools/Xilinx/Vitis/2022.2/settings64.sh >/dev/null 2>&1; exec '+command],cwd=V,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
   s.update(child_pid=p.pid,child_pgid=os.getpgid(p.pid),command=command);save()
   try:rc=p.wait(timeout=240)
   except subprocess.TimeoutExpired:
    os.killpg(p.pid,signal.SIGTERM)
    try:p.wait(timeout=10)
    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
    raise AssertionError('unit timeout')
  assert rc==0,(phase,rc)
 log=(R/'simulate.log').read_text()
 assert any(x.startswith('BANK_MEMORY_UNIT_PASS ') for x in log.splitlines()),'Missing actual test PASS'
 assert sha(V/'file_agent/mem_model.sv')==sha(E/'mem_model.sv')
 shutil.copy2(V/'memory_events.csv',R/'memory_events.csv')
 s.update(state='TOOL_PASS_AWAITING_INDEPENDENT_EVENT_REVIEW',finished=stamp())
except BaseException as e:
 s.update(state='FAILED_NO_AUTOMATIC_RETRY',error=repr(e),finished=stamp())
finally:
 save();(R/'ACTIVE.lock').unlink(missing_ok=True)
print(json.dumps(s,indent=2))
