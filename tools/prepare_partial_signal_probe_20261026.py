from pathlib import Path
import shutil,subprocess,json,hashlib,datetime
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
OLD=ROOT/'.cache/p64_rtl_full_r3/hls/solution1/sim'
NEW=ROOT/'.cache/p64_signal_probe_20261026_r1/sim'
assert not NEW.exists(), 'Do not overwrite diagnostic run'
NEW.mkdir(parents=True)
shutil.copytree(OLD/'verilog',NEW/'verilog',ignore=shutil.ignore_patterns('*.log','*.wdb','*.jou','*.rpt'))
(NEW/'tv').mkdir();(NEW/'tv/cdatafile').symlink_to(OLD/'tv/cdatafile',target_is_directory=True)
(NEW/'tv/rtldatafile').mkdir()
v=NEW/'verilog'
(v/'probe_help.tcl').write_text('help add_condition\nhelp get_value\nhelp get_objects\nputs "SCOPES [get_scopes /*]"\nputs "OBJECTS [get_objects /apatb_lm_head_v4_partial_proto_top/*weights*]"\nquit\n')
p=subprocess.run(['bash','-c','source /tools/Xilinx/Vitis/2022.2/settings64.sh >/dev/null 2>&1; exec /tools/Xilinx/Vivado/2022.2/bin/xsim lm_head_v4_partial_proto -tclbatch probe_help.tcl'],cwd=v,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
print(p.stdout.decode(errors='replace'))
assert p.returncode==0
