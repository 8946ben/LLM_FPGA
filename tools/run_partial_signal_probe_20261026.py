from pathlib import Path
import os,sys,subprocess,json,datetime,hashlib,signal
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
V=ROOT/'.cache/p64_signal_probe_20261026_r1/sim/verilog'
R=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261026_diagnosis_r1'
R.mkdir(exist_ok=True)
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(x): (R/'WORKFLOW.json').write_text(json.dumps(x,indent=2)+'\n')
assert not (R/'WORKFLOW.json').exists(), 'Do not rerun or overwrite'
top='/apatb_lm_head_v4_partial_proto_top'
text='''open_vcd signal_probe.vcd
set top /apatb_lm_head_v4_partial_proto_top
puts "CLOCKS [get_objects $top/*clk*] [get_objects $top/*CLK*]"
puts "DUTSCOPES [get_scopes $top/*]"
log_vcd [get_objects $top/*clk*]
log_vcd [get_objects $top/*CLK*]
foreach port {weights_ARVALID weights_ARREADY weights_ARADDR weights_ARLEN weights_RVALID weights_RREADY weights_RDATA weights_RLAST meta_AWVALID meta_AWREADY meta_AWADDR meta_AWLEN meta_WVALID meta_WREADY meta_WDATA meta_WSTRB meta_WLAST} {
 log_vcd [get_objects $top/$port]
}
add_condition -name stop_after_first_preview -notrace {/apatb_lm_head_v4_partial_proto_top/meta_AWVALID == 1 && /apatb_lm_head_v4_partial_proto_top/meta_AWREADY == 1 && /apatb_lm_head_v4_partial_proto_top/meta_AWADDR == 632128} {puts "PROBE_FIRST_PREVIEW_REACHED [current_time]"; stop}
run 5 ms
close_vcd
puts "PROBE_STOPPED [current_time]"
quit
'''
(V/'signal_probe.tcl').write_text(text)
s=dict(state='EXECUTING',started=stamp(),parent_pid=os.getpid(),parent_proc_stat=Path('/proc/self/stat').read_text(),
       isolated_dir=str(V),original_snapshot_reused=True,no_design_or_stall_change=True,
       max_simulation_ms=5,wall_timeout_seconds=1200,automatic_next_stage=False,board='NOT_RUN')
(R/'ACTIVE.lock').write_text(str(os.getpid()))
write(s)
cmd=['bash','-c','source /tools/Xilinx/Vitis/2022.2/settings64.sh >/dev/null 2>&1; exec /tools/Xilinx/Vivado/2022.2/bin/xsim -testplusarg UVM_VERBOSITY=UVM_LOW -testplusarg UVM_TESTNAME=lm_head_v4_partial_proto_test_lib -testplusarg UVM_TIMEOUT=20000000000000 --noieeewarnings lm_head_v4_partial_proto -tclbatch signal_probe.tcl']
try:
 with (R/'probe.log').open('w') as out:
  p=subprocess.Popen(cmd,cwd=V,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
  s.update(child_pid=p.pid,child_pgid=os.getpgid(p.pid),command=cmd);write(s)
  try:rc=p.wait(timeout=1200)
  except subprocess.TimeoutExpired:
   os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(timeout=15)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
   s['timeout']=True;rc=p.returncode
 s.update(state='DIAGNOSTIC_RETURNED' if rc==0 else 'DIAGNOSTIC_ENTRY_OR_TIMEOUT_FAILED',exit_code=rc,finished=stamp())
 if (V/'signal_probe.vcd').exists():
  import shutil
  shutil.copy2(V/'signal_probe.vcd',R/'signal_probe.vcd')
except BaseException as e:
 s.update(state='DIAGNOSTIC_FAILED',error=repr(e),finished=stamp())
 raise
finally:
 write(s);(R/'ACTIVE.lock').unlink(missing_ok=True)
