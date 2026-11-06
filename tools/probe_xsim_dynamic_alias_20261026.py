from pathlib import Path
import subprocess,os,signal,json,datetime,hashlib
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
E=ROOT/'.cache/xsim_dynamic_alias_20261026_r1';R=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261026_diagnosis_r1/alias_minimal'
assert not E.exists();E.mkdir();R.mkdir()
src='''`timescale 1ns/1ps
module alias_diag;
logic [7:0] mem[];
longint low_addr=64'h1200, high_addr=64'h20001200;
initial begin
 mem=new[536875552];
 mem[low_addr]=8'h12;
 $display("BEFORE low=%h high=%h",mem[low_addr],mem[high_addr]);
 mem[high_addr]=8'h34;
 $display("AFTER low=%h high=%h size=%0d",mem[low_addr],mem[high_addr],mem.size());
 if(mem[low_addr]===8'h34 && mem[high_addr]===8'h34) $display("XSIM_DYNAMIC_BYTE_ARRAY_ALIAS_512M_REPRODUCED");
 else if(mem[low_addr]===8'h12 && mem[high_addr]===8'h34) $display("NO_ALIAS");
 else $display("UNEXPECTED_ARRAY_RESULT");
 $finish;
end
endmodule
'''
(E/'alias_diag.sv').write_text(src);(R/'alias_diag.sv').write_text(src)
cmd='source /tools/Xilinx/Vitis/2022.2/settings64.sh >/dev/null 2>&1; /tools/Xilinx/Vivado/2022.2/bin/xvlog --sv alias_diag.sv && /tools/Xilinx/Vivado/2022.2/bin/xelab xil_defaultlib.alias_diag -debug all -s alias_diag && /tools/Xilinx/Vivado/2022.2/bin/xsim alias_diag -runall'
state=dict(state='EXECUTING',started=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent_pid=os.getpid(),source_sha256=hashlib.sha256(src.encode()).hexdigest(),no_hls_or_board=True)
(R/'WORKFLOW.json').write_text(json.dumps(state,indent=2)+'\n')
with (R/'probe.log').open('w') as out:
 p=subprocess.Popen(['bash','-c',cmd],cwd=E,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
 state.update(child_pid=p.pid,child_pgid=os.getpgid(p.pid))
 (R/'WORKFLOW.json').write_text(json.dumps(state,indent=2)+'\n')
 try:rc=p.wait(timeout=180)
 except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGTERM);p.wait();rc=p.returncode
state.update(state='FINISHED' if rc==0 else 'FAILED',exit_code=rc,finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
(R/'WORKFLOW.json').write_text(json.dumps(state,indent=2)+'\n')
print((R/'probe.log').read_text())
