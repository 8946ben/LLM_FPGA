"""Derive a debug-only elaboration probe; preserve failed non-debug entry."""
from pathlib import Path
import subprocess,json,datetime,os,signal
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
OLD=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261026_diagnosis_r1'
R=OLD/'r2';R.mkdir(exist_ok=True)
assert not (R/'ELABORATION.json').exists(), 'Do not rerun'
V=ROOT/'.cache/p64_signal_probe_20261026_r1/sim/verilog'
stamp=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
cmd=(V/'run_xsim.sh').read_text().splitlines()[1].strip()
assert cmd.startswith('/tools/Xilinx/Vivado/2022.2/bin/xelab ')
assert cmd.endswith('-s lm_head_v4_partial_proto')
cmd=cmd.replace('-s lm_head_v4_partial_proto','-debug all -s partial_probe_debug_r2')
state=dict(state='ELABORATING_DEBUG_ONLY',started=stamp(),parent_pid=os.getpid(),no_hls_or_rtl_change=True,command=cmd,automatic_next_stage=False)
(R/'ELABORATION.json').write_text(json.dumps(state,indent=2)+'\n')
with (R/'xelab.log').open('w') as out:
 p=subprocess.Popen(['bash','-c','source /tools/Xilinx/Vitis/2022.2/settings64.sh >/dev/null 2>&1; exec '+cmd],cwd=V,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
 state.update(child_pid=p.pid,child_pgid=os.getpgid(p.pid));(R/'ELABORATION.json').write_text(json.dumps(state,indent=2)+'\n')
 try:rc=p.wait(timeout=300)
 except subprocess.TimeoutExpired:
  os.killpg(p.pid,signal.SIGTERM);p.wait();rc=p.returncode
state.update(state='ELABORATED' if rc==0 else 'FAILED',exit_code=rc,finished=stamp());(R/'ELABORATION.json').write_text(json.dumps(state,indent=2)+'\n')
assert rc==0
entry=(ROOT/'run_partial_signal_probe_20261026.py').read_text()
entry=entry.replace("R.mkdir(exist_ok=True)","R=R/'r2'\nR.mkdir(exist_ok=True)")
entry=entry.replace('lm_head_v4_partial_proto -tclbatch signal_probe.tcl','partial_probe_debug_r2 -tclbatch signal_probe.tcl')
entry=entry.replace("'DIAGNOSTIC_RETURNED' if rc==0", "'DIAGNOSTIC_RETURNED' if rc==0 and 'PROBE_STOPPED' in (R/'probe.log').read_text()")
exec(compile(entry,str(ROOT/'run_partial_signal_probe_r2_20261026.py'), 'exec'))
