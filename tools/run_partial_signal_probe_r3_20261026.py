from pathlib import Path
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
entry=(ROOT/'run_partial_signal_probe_20261026.py').read_text()
entry=entry.replace("R.mkdir(exist_ok=True)","R=R/'r3'\nR.mkdir(exist_ok=True)")
entry=entry.replace('lm_head_v4_partial_proto -tclbatch signal_probe.tcl','partial_probe_debug_r2 -tclbatch signal_probe.tcl')
entry=entry.replace('log_vcd [get_objects $top/*CLK*]','')
entry=entry.replace('log_vcd [get_objects $top/*clk*]','log_vcd [get_objects $top/ap_clk]')
entry=entry.replace("'DIAGNOSTIC_RETURNED' if rc==0", "'DIAGNOSTIC_RETURNED' if rc==0 and 'PROBE_STOPPED' in (R/'probe.log').read_text()")
exec(compile(entry,str(ROOT/'run_partial_signal_probe_r3_20261026.py'),'exec'))
