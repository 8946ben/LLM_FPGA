from pathlib import Path
import subprocess,json,sys
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/dual_board_20261030_r1'
revision=sys.argv[1] if len(sys.argv)>1 else 'r2';assert revision in ['r2','r3']
P=M/'reports/board_v4_20261021/private_package_r1';entry=R/('control_'+revision)/'private_board_entry.tcl'
log=R/('initialization_'+revision+'.log');assert not log.exists()
cmd=[Path('G:/Xilinx/Vitis/2021.1/bin/xsct.bat'),entry,'loader',P/'m14_v4_system_wrapper.bit',P/'psu_init.tcl',P/'m14_v4_arena_loader.elf',P/'m14_v4_single.xsa']
with log.open('x') as f:result=subprocess.run([str(x).replace('\\','/') for x in cmd],stdout=f,stderr=subprocess.STDOUT,timeout=240)
s=log.read_text(errors='replace');success=result.returncode==0 and 'M4_PRIVATE_LOADER_STARTED' in s and 'M4_PRIVATE_BOARD_ERROR:' not in s
(R/('INITIALIZATION_'+revision.upper()+'.json')).write_text(json.dumps(dict(state='LOADER_STARTED' if success else 'FAILED_NO_TRANSFER',returncode=result.returncode,marker_required=True,automatic_next_stage=False),indent=2)+'\n')
print(s[-6000:]);sys.exit(0 if success else 1)
