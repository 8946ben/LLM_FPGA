"""One finite full-input, five-block observation; never starts full CoSim."""
from pathlib import Path
import json,hashlib,tarfile,shutil,subprocess,datetime,os,signal,time,re
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
E=ROOT/'module_14_lm_head_v4/experiments/sim_memory_bank_20261026';R=ROOT/'module_14_lm_head_v4/reports/sim_memory_bank_20261026_r1'
OLD=ROOT/'.cache/p64_rtl_full_r3/hls/solution1/sim';NEW=ROOT/'.cache/p64_bank_preview_20261026_r1/sim';V=NEW/'verilog'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(): (R/'PREVIEW_WORKFLOW.json').write_text(json.dumps(state,indent=2)+'\n')
archive=ROOT/'bank_preview_entry_20261026.tar.gz'
assert sha(archive)=='06d86a729d2def10a167d9925587899a5e3fed8fa7d67324fa4786f11548edbd'
assert not V.exists() and not (R/'PREVIEW_WORKFLOW.json').exists()
with tarfile.open(archive) as t:
 for member in t.getmembers():
  p=(ROOT/member.name).resolve();assert ROOT in p.parents and member.isfile();data=t.extractfile(member).read()
  if p.exists():assert p.read_bytes()==data
  else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
plan=json.loads((R/'PREVIEW_PLAN.json').read_text());assert json.loads((R/'UNIT_REVIEW.json').read_text())['state']=='PASS_INDEPENDENT_MEMORY_EVENT_REPLAY'
for n,h in plan['source_sha256'].items():assert sha(ROOT/n)==h,n
state=dict(state='PREPARING_FULL_INPUT',started=stamp(),parent_pid=os.getpid(),parent_proc_stat=Path('/proc/self/stat').read_text(),automatic_next_stage=False,board='NOT_RUN',plan_sha256=sha(R/'PREVIEW_PLAN.json'))
(R/'ACTIVE.lock').write_text(str(os.getpid()));save()
def terminate(p):
 try:os.killpg(p.pid,signal.SIGTERM)
 except ProcessLookupError:pass
 try:p.wait(timeout=15)
 except subprocess.TimeoutExpired:
  os.killpg(p.pid,signal.SIGKILL);p.wait()
def tool(phase,command,timeout):
 state.update(state='EXECUTING_'+phase.upper(),phase=phase);save()
 with (R/(phase+'.log')).open('w') as out:
  p=subprocess.Popen(['bash','-c','source /tools/Xilinx/Vitis/2022.2/settings64.sh >/dev/null 2>&1; exec '+command],cwd=V,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
  state.update(child_pid=p.pid,child_pgid=os.getpgid(p.pid),command=command);save();start=time.monotonic()
  while p.poll() is None:
   try:p.wait(timeout=10)
   except subprocess.TimeoutExpired:pass
   info=dict((line.split(':')[0],int(line.split()[1])) for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith(('MemAvailable:','MemTotal:')))
   if time.monotonic()-start>timeout or info['MemAvailable']<8*1024*1024:
    terminate(p);raise AssertionError('time/resource guard: '+phase)
  assert p.returncode==0,(phase,p.returncode)
try:
 # Stream-decode the entire original TV before invoking the heavy simulator.
 tv=OLD/'tv/cdatafile/c.lm_head_v4_partial_proto.autotvin_weights.dat'
 rawsha=sha(tv);digests=[]
 with tv.open('rb') as source:
  assert source.readline().strip()==b'[[[runtime]]]';assert source.readline().strip()==b'[[transaction]]           0'
  for name,count,expected in [('tiled',17088512,'62aed05d6a0a17c092541dde5a9d7e47cd23bcdf59c01d2a294d9de8a500c57e'),('canonical',17016832,'4e96b0df6d274768cbb7e72404011853d23349999b658dc2f4dfb3c431ea223f')]:
   h=hashlib.sha256();remaining=count
   while remaining:
    n=min(remaining,65536);block=source.read(n*35);assert len(block)==n*35
    records=block.splitlines();assert len(records)==n
    h.update(b''.join(int(x,16).to_bytes(16,'little') for x in records));remaining-=n
   assert h.hexdigest()==expected,name;digests.append(dict(name=name,beats=count,sha256=h.hexdigest()))
  assert source.read()==b'[[/transaction]]\n[[[/runtime]]]\n'
 (R/'FULL_TV_INPUT_REVIEW.json').write_text(json.dumps(dict(state='PASS_FULL_ORIGINAL_TV_RECONSTRUCTION_SHA',tv_sha256=rawsha,parts=digests,total_beats=34105344),indent=2)+'\n')
 shutil.copytree(OLD/'verilog',V,ignore=shutil.ignore_patterns('*.log','*.wdb','*.vcd','*.jou','*.rpt'))
 shutil.copy2(E/'mem_model.sv',V/'file_agent/mem_model.sv')
 reference=V/'lm_head_v4_partial_proto_subsystem/lm_head_v4_partial_proto_reference_model.sv'
 text=reference.read_text();needle='        mem_blk_pages_weights.tvinload_pagechk_atinit(fpath, 34105344*((128+7)/8), 0);'
 assert text.count(needle)==1
 reference.write_text(text.replace(needle,needle+'\n'+(E/'weights_preflight.svh').read_text()))
 unchanged={}
 for p in (OLD/'verilog').rglob('*'):
  rel=p.relative_to(OLD/'verilog')
  if p.is_file() and p.suffix in ['.v','.sv'] and rel not in [Path('file_agent/mem_model.sv'),reference.relative_to(V)]:
   assert sha(p)==sha(V/rel),str(rel);unchanged[str(rel)]=sha(p)
 (R/'PREVIEW_RTL_AND_STALL_REUSE.json').write_text(json.dumps(unchanged,indent=2)+'\n')
 (NEW/'tv').mkdir();(NEW/'tv/cdatafile').symlink_to(OLD/'tv/cdatafile',target_is_directory=True);(NEW/'tv/rtldatafile').mkdir()
 shutil.copy2(E/'preview5.tcl',V/'preview5.tcl')
 first=next(x.strip() for x in (V/'run_xsim.sh').read_text().splitlines() if x.strip().startswith('/tools/Xilinx/Vivado/2022.2/bin/xelab '))
 assert first.endswith('-s lm_head_v4_partial_proto')
 tool('preview_elaborate',first.replace('-s lm_head_v4_partial_proto','-debug all -s bank_preview5_r1'),300)
 tool('preview_simulate','/tools/Xilinx/Vivado/2022.2/bin/xsim -testplusarg UVM_VERBOSITY=UVM_LOW -testplusarg UVM_TESTNAME=lm_head_v4_partial_proto_test_lib -testplusarg UVM_TIMEOUT=20000000000000 --noieeewarnings bank_preview5_r1 -tclbatch preview5.tcl',7200)
 log=(R/'preview_simulate.log').read_text()
 assert re.search(r'^BANK_FULL_INPUT_SENTINEL_PASS checked=1522$',log,re.M)
 assert re.search(r'^BANK_PREVIEW5_STOP \d+ ps$',log,re.M)
 assert not re.search(r'^(?:UVM_FATAL|ERROR:)',log,re.M)
 shutil.copy2(V/'weights_readback.csv',R/'weights_readback.csv');shutil.copy2(V/'preview5.vcd',R/'preview5.vcd')
 assert sha(tv)==rawsha
 state.update(state='SEGMENT_RETURNED_AWAITING_INDEPENDENT_VCD_REVIEW',finished=stamp())
except BaseException as e:
 state.update(state='FAILED_NO_AUTOMATIC_RETRY',error=repr(e),finished=stamp())
 if (V/'preview5.vcd').exists():shutil.copy2(V/'preview5.vcd',R/'preview5_partial.vcd')
finally:
 save();(R/'ACTIVE.lock').unlink(missing_ok=True)
print(json.dumps(state,indent=2))
