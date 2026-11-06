"""Stop owned full-TV diagnostic; run bounded reachable-prefix diagnostic."""
from pathlib import Path
import os,signal,time,json,shutil,hashlib
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
R=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261026_diagnosis_r1'
old=R/'r4';work=json.loads((old/'WORKFLOW.json').read_text())
assert work['state']=='EXECUTING'
pid=work['parent_pid'];saved=work['parent_proc_stat'];now=Path('/proc/{}/stat'.format(pid)).read_text()
assert saved[saved.rindex(')')+2:].split()[19]==now[now.rindex(')')+2:].split()[19]
assert 'run_partial_signal_probe_r4_20261026.py' in Path('/proc/{}/cmdline'.format(pid)).read_bytes().decode().replace('\0',' ')
pgid=work['child_pgid']
members=[]
for p in Path('/proc').iterdir():
 try:
  s=(p/'stat').read_text();v=s[s.rindex(')')+2:].split()
  if v[0]!='Z' and int(v[2])==pgid:members.append(int(p.name))
 except (OSError,ValueError):pass
assert members
# Parent must not launch any following stage; terminate it and only the owned group.
os.kill(pid,signal.SIGTERM);os.killpg(pgid,signal.SIGTERM)
time.sleep(3)
for member in members:
 p=Path('/proc/{}/stat'.format(member))
 if p.exists():
  s=p.read_text();v=s[s.rindex(')')+2:].split()
  if v[0]!='Z' and int(v[2])==pgid:os.kill(member,signal.SIGKILL)
v=ROOT/'.cache/p64_signal_probe_20261026_r1/sim/verilog/signal_probe.vcd'
if v.exists():shutil.copy2(v,old/'signal_probe.vcd')
work.update(state='STOPPED_DURING_FULL_TV_INITIALIZATION',reason='Use separately recorded reachable-prefix diagnostic; not a numerical test failure',owned_group_members_before=members)
(old/'WORKFLOW.json').write_text(json.dumps(work,indent=2)+'\n');(old/'ACTIVE.lock').unlink(missing_ok=True)
OLD=ROOT/'.cache/p64_signal_probe_20261026_r1/sim'
NEW=ROOT/'.cache/p64_signal_probe_20261026_r5/sim'
assert not NEW.exists();NEW.mkdir(parents=True)
shutil.copytree(OLD/'verilog',NEW/'verilog',ignore=shutil.ignore_patterns('*.log','*.vcd','*.wdb','*.jou','*.rpt'))
(NEW/'tv/cdatafile').mkdir(parents=True);(NEW/'tv/rtldatafile').mkdir()
prefix_beats=7*896*128;prefix_sha=None
for p in (OLD/'tv/cdatafile').iterdir():
 if not p.is_file():continue
 target=NEW/'tv/cdatafile'/p.name
 if p.name.endswith('autotvin_weights.dat'):
  with p.open('rb') as source,target.open('wb') as dest:
   dest.write(source.readline());dest.write(source.readline())
   raw=source.read(prefix_beats*35);assert len(raw)==prefix_beats*35
   dest.write(raw);dest.write(b'[[/transaction]]\n[[[/runtime]]]\n')
   prefix_sha=hashlib.sha256(raw).hexdigest()
 else:shutil.copy2(p,target)
(R/'r5').mkdir()
(R/'r5/COMPACT_INPUT_PLAN.json').write_text(json.dumps(dict(prefix_beats=prefix_beats,prefix_tv_payload_sha256=prefix_sha,
 remaining_weights_not_supplied=True,stop_before_unprovided_data=True,original_hw_parameters_unchanged=True,
 scope='Diagnostic first preview only, not full CoSim qualification; must reproduce original returned first word'),indent=2)+'\n')
entry=(ROOT/'run_partial_signal_probe_20261026.py').read_text()
entry=entry.replace("R.mkdir(exist_ok=True)","R=R/'r5'\nR.mkdir(exist_ok=True)")
entry=entry.replace('p64_signal_probe_20261026_r1','p64_signal_probe_20261026_r5')
entry=entry.replace('lm_head_v4_partial_proto -tclbatch signal_probe.tcl','partial_probe_debug_r2 -tclbatch signal_probe.tcl')
entry=entry.replace('log_vcd [get_objects $top/*CLK*]','')
entry=entry.replace('log_vcd [get_objects $top/*clk*]','log_vcd [get_objects $top/ap_clk]')
entry=entry.replace('add_condition -name stop_after_first_preview','add_condition -radix unsigned -name stop_after_first_preview')
entry=entry.replace('run 5 ms', 'add_condition -radix unsigned -name range_guard -notrace {/apatb_lm_head_v4_partial_proto_top/weights_ARVALID == 1 && /apatb_lm_head_v4_partial_proto_top/weights_ARADDR >= 12845056} {puts "PROBE_RANGE_GUARD_FAILURE"; stop}\nrun 5 ms')
entry=entry.replace("'DIAGNOSTIC_RETURNED' if rc==0", "'DIAGNOSTIC_RETURNED' if rc==0 and 'PROBE_FIRST_PREVIEW_REACHED' in (R/'probe.log').read_text() and 'PROBE_RANGE_GUARD_FAILURE' not in (R/'probe.log').read_text()")
exec(compile(entry,str(ROOT/'prepare_run_partial_compact_probe_20261026.py'),'exec'))
