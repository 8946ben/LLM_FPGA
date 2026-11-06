
from pathlib import Path
import subprocess,json,hashlib,shutil
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1');M=ROOT/'module_14_lm_head_v4';E=M/'experiments/d64_matching_ps_20261106_r5';R=M/'reports/d64_matching_ps_20261106_r5';B=M/'build/d64_matching_ps_20261106_r5';candidates=list((B/'bsp').rglob('include/xparameters.h'));assert len(candidates)==1,candidates;BSP=candidates[0].parent.parent;O=R/'software';O.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args):
 p=subprocess.run([str(x) for x in args],capture_output=True);print(p.stdout.decode(errors='replace'),end='');print(p.stderr.decode(errors='replace'),end='');assert p.returncode==0,args;return p.stdout
review=json.loads((E/'INDEPENDENT_HARDWARE_REVIEW.json').read_text());xsa=M/'reports/d64_bit_xsa_20261106_r1/hardware/m14_d64_200m.xsa';assert sha(xsa)==review['xsa_sha256']
assert sha(B/'hw/m14_d64_200m.xsa')==review['xsa_sha256']
assert (BSP/'include/xparameters.h').is_file()
header='xlm_head_v4_partial_proto_hw.h';actual=BSP/'libsrc/lm_head_v4_partial_proto_v4_1/src'/header;export=M/'ip_repo/lm_head_v4_partial_proto_d64_r1/drivers/lm_head_v4_partial_proto_v4_1/src'/header;assert sha(actual)==sha(export)
phy=list(BSP.glob('libsrc/lwip211*/src/contrib/ports/xilinx/netif/xemacpsif_physpeed.c'));assert len(phy)==1;shutil.copyfile(E/'xemacpsif_physpeed.c',phy[0]);assert sha(phy[0])==sha(E/'xemacpsif_physpeed.c')
make=(B/'bsp/Makefile') if (B/'bsp/Makefile').is_file() else BSP/'Makefile';assert make.is_file();
for target in ['include','seq_libs','par_libs','archive']:run(['make','-C',make.parent,'-j2',target])
assert sha(BSP/'include'/header)==sha(export)
assert (BSP/'include/xtime_l.h').is_file()
for name in ['lib/libxil.a','lib/liblwip4.a']:assert (BSP/name).is_file(),name
bin=Path('/tools/Xilinx/Vitis/2022.2/gnu/aarch64/lin/aarch64-none/bin');gcc=bin/'aarch64-none-elf-gcc';plan=json.loads((E/'PLAN.json').read_text());assert all(sha(E/name)==h for name,h in plan['source_sha256'].items())
for kind,sources,libs in [('loader',['loader/main.c','loader/loader_core.c','loader/platform_zynqmp.c'],['-llwip4','-lxil','-lgcc','-lc']),('test',['d64_ps_main.c','d64_control.c','loader/loader_core.c'],['-lxil','-lgcc','-lc'])]:
 objects=[]
 for name in sources:
  obj=O/(kind+'_'+Path(name).stem+'.o');run([gcc,'-std=gnu11','-mcpu=cortex-a53','-Wall','-Wextra','-Werror','-O2','-g','-DARMA53_64','-c','-I'+str(BSP/'include'),'-I'+str(BSP/'include/lwip'),'-I'+str(E/'ps'),'-I'+str(E/'ps/loader'),E/'ps'/name,'-o',obj]);objects.append(obj)
 elf=O/('m14_d64_'+kind+'.elf');run([gcc,'-mcpu=cortex-a53','-Wl,-T,'+str(E/'ps/arena_loader.ld'),'-L'+str(BSP/'lib'),'-Wl,-Map='+str(elf.with_suffix('.map')),'-o',elf,*objects,'-Wl,--start-group',*libs,'-Wl,--end-group'])
 assert not run([bin/'aarch64-none-elf-nm','-u',elf]).strip()
 (O/(kind+'_headers.txt')).write_bytes(run([bin/'aarch64-none-elf-readelf','-h','-lW',elf]));run([bin/'aarch64-none-elf-size',elf])
print('D64_MATCHING_ELF_RETURNED=PASS_BUILD_ONLY_NOT_BOARD')
