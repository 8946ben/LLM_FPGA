"""Prepare matching standalone BSP/ELF stage only after audited bit/XSA receipt."""
from pathlib import Path
import ast,json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';E=M/'experiments/d64_matching_ps_20261106_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 receipt=M/'reports/d64_bit_xsa_20261106_r1/INDEPENDENT_HARDWARE_REVIEW.json';review=json.loads(receipt.read_text());assert review['state']=='PASS_BIT_XSA_IDENTITY_ONLY_NOT_BOARD';assert not E.exists();E.mkdir()
 shutil.copytree(M/'experiments/d64_board_20261105_r1/ps',E/'ps');shutil.copy2(ROOT/'ref/xemacpsif_physpeed.c',E/'xemacpsif_physpeed.c');shutil.copy2(receipt,E/'INDEPENDENT_HARDWARE_REVIEW.json')
 tcl=r'''set here [file dirname [file normalize [info script]]]
set module [file normalize [file join $here .. ..]]
set workspace [file join $module build d64_matching_ps_20261106_r1 workspace]
set xsa [file join $module reports d64_bit_xsa_20261106_r1 hardware m14_d64_200m.xsa]
set platform_name m14_d64_200m
if {[catch {
 if {[file exists $workspace]} {error "Preserve existing workspace"}
 if {![file isfile $xsa]} {error "Matching audited XSA missing"}
 file mkdir $workspace
 setws $workspace
 platform create -name $platform_name -hw $xsa -proc psu_cortexa53_0 -os standalone
 platform active $platform_name
 domain active standalone_domain
 bsp setlib -name lwip211
 bsp config mem_size 262144
 bsp config tcp_snd_buf 32768
 bsp config tcp_wnd 32768
 bsp config pbuf_pool_size 256
 bsp config memp_n_tcp_seg 512
 bsp write
 bsp regenerate
 set phy_files [glob -nocomplain [file join $workspace $platform_name psu_cortexa53_0 standalone_domain bsp psu_cortexa53_0 libsrc lwip211* src contrib ports xilinx netif xemacpsif_physpeed.c]]
 if {[llength $phy_files] != 1} {error "Expected exactly one generated PHY source"}
 file copy -force [file join $here xemacpsif_physpeed.c] [lindex $phy_files 0]
 platform write
 platform generate
 puts "D64_MATCHING_BSP_RETURNED=PASS_OFFLINE_ONLY"
} message options]} {
 puts stderr "D64_MATCHING_BSP_ERROR: $message"
 if {[dict exists $options -errorinfo]} {puts stderr [dict get $options -errorinfo]}
 exit 1
}
exit 0
'''
 (E/'platform.tcl').write_text(tcl,encoding='utf-8')
 build=r'''
from pathlib import Path
import subprocess,json,hashlib,shutil
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1');M=ROOT/'module_14_lm_head_v4';E=M/'experiments/d64_matching_ps_20261106_r1';R=M/'reports/d64_matching_ps_20261106_r1';B=M/'build/d64_matching_ps_20261106_r1/workspace/m14_d64_200m';BSP=B/'psu_cortexa53_0/standalone_domain/bsp/psu_cortexa53_0';O=R/'software';O.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args):
 p=subprocess.run([str(x) for x in args],capture_output=True);print(p.stdout.decode(errors='replace'),end='');print(p.stderr.decode(errors='replace'),end='');assert p.returncode==0,args;return p.stdout
review=json.loads((E/'INDEPENDENT_HARDWARE_REVIEW.json').read_text());xsa=M/'reports/d64_bit_xsa_20261106_r1/hardware/m14_d64_200m.xsa';assert sha(xsa)==review['xsa_sha256']
assert sha(B/'hw/m14_d64_200m.xsa')==review['xsa_sha256']
for name in ['include/xparameters.h','include/xtime_l.h','lib/libxil.a','lib/liblwip4.a']:assert (BSP/name).is_file(),name
header='xlm_head_v4_partial_proto_hw.h';actual=BSP/'include'/header;export=M/'ip_repo/lm_head_v4_partial_proto_d64_r1/drivers/lm_head_v4_partial_proto_v4_1/src'/header;assert sha(actual)==sha(export)
phy=list(BSP.glob('libsrc/lwip211*/src/contrib/ports/xilinx/netif/xemacpsif_physpeed.c'));assert len(phy)==1 and sha(phy[0])==sha(E/'xemacpsif_physpeed.c')
bin=Path('/tools/Xilinx/Vitis/2022.2/gnu/aarch64/lin/aarch64-none/bin');gcc=bin/'aarch64-none-elf-gcc';plan=json.loads((E/'PLAN.json').read_text());assert all(sha(E/name)==h for name,h in plan['source_sha256'].items())
for kind,sources,libs in [('loader',['loader/main.c','loader/loader_core.c','loader/platform_zynqmp.c'],['-llwip4','-lxil','-lgcc','-lc']),('test',['d64_ps_main.c','d64_control.c','loader/loader_core.c'],['-lxil','-lgcc','-lc'])]:
 objects=[]
 for name in sources:
  obj=O/(kind+'_'+Path(name).stem+'.o');run([gcc,'-std=gnu11','-mcpu=cortex-a53','-Wall','-Wextra','-Werror','-O2','-g','-DARMA53_64','-c','-I'+str(BSP/'include'),'-I'+str(E/'ps'),'-I'+str(E/'ps/loader'),E/'ps'/name,'-o',obj]);objects.append(obj)
 elf=O/('m14_d64_'+kind+'.elf');run([gcc,'-mcpu=cortex-a53','-Wl,-T,'+str(E/'ps/arena_loader.ld'),'-L'+str(BSP/'lib'),'-Wl,-Map='+str(elf.with_suffix('.map')),'-o',elf,*objects,'-Wl,--start-group',*libs,'-Wl,--end-group'])
 assert not run([bin/'aarch64-none-elf-nm','-u',elf]).strip()
 (O/(kind+'_headers.txt')).write_bytes(run([bin/'aarch64-none-elf-readelf','-h','-lW',elf]));run([bin/'aarch64-none-elf-size',elf])
print('D64_MATCHING_ELF_RETURNED=PASS_BUILD_ONLY_NOT_BOARD')
'''
 (E/'build_software.py').write_text(build,encoding='utf-8')
 source=M/'experiments/d64_system_200m_20261106_r4/run_route.py';tree=ast.parse(source.read_text());body=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef))];runner=ast.unparse(ast.Module(body=body,type_ignores=[]))+'\n'
 runner+=r'''
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1');M=ROOT/'module_14_lm_head_v4';E=M/'experiments/d64_matching_ps_20261106_r1';BASE=M/'reports/d64_matching_ps_20261106_r1';R=BASE/'execution';V=ROOT/'.cache/d64_matching_ps_20261106_r1'
assert sys.argv[1:]==['--execute'];plan=json.loads((E/'PLAN.json').read_text());assert all(sha(E/name)==h for name,h in plan['source_sha256'].items());review=json.loads((E/'INDEPENDENT_HARDWARE_REVIEW.json').read_text());assert review['state']=='PASS_BIT_XSA_IDENTITY_ONLY_NOT_BOARD'
assert sha(M/'reports/d64_bit_xsa_20261106_r1/hardware/m14_d64_200m.xsa')==review['xsa_sha256']
old=M/'reports/d64_bit_xsa_20261106_r1/execution';w=json.loads((old/'WORKFLOW.json').read_text());assert w['state']=='BIT_XSA_RETURNED_AWAITING_INDEPENDENT_REVIEW' and not members(w['child_pgid']) and not list((M/'reports').rglob('ACTIVE.lock'))
assert not R.exists() and not V.exists();R.mkdir(parents=True);V.mkdir();os.environ['MAKEFLAGS']='-j2';state=dict(state='PREPARING',started=now(),parent_pid=os.getpid(),parent_proc_stat=Path('/proc/self/stat').read_text(),phases={},scope='Offline matching standalone BSP and strict A53 ELF build only; no board')
(R/'ACTIVE.lock').write_text(str(os.getpid()));save()
try:
 run('bsp','/tools/Xilinx/Vitis/2022.2/bin/xsct '+shlex.quote(str(E/'platform.tcl')),1800)
 assert (R/'bsp/tool.log').read_text().count('D64_MATCHING_BSP_RETURNED=PASS_OFFLINE_ONLY')==1
 run('elf','/home/zhangben/anaconda3/bin/python '+shlex.quote(str(E/'build_software.py')),600)
 assert (R/'elf/tool.log').read_text().count('D64_MATCHING_ELF_RETURNED=PASS_BUILD_ONLY_NOT_BOARD')==1
 state.update(state='BSP_ELF_RETURNED_AWAITING_INDEPENDENT_REVIEW',finished=now())
except BaseException as ex:state.update(state='FAILED_NO_AUTOMATIC_RETRY',error=repr(ex),finished=now())
finally:
 state['process_after']=members(state.get('child_pgid',-1));save()
 if not state['process_after']:(R/'ACTIVE.lock').unlink(missing_ok=True)
print(json.dumps(state,indent=2))
'''
 (E/'run_build.py').write_text(runner,encoding='utf-8')
 plan=dict(scope='Matching XSA offline BSP and ELF only',guards=dict(group_gib=16,min_available_gib=32,bsp_timeout_s=1800,elf_timeout_s=600),source_sha256={str(p.relative_to(E)).replace('\\','/'):sha(p) for p in E.rglob('*') if p.is_file()});(E/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n');print('PREPARED',E)
if __name__=='__main__':main()
