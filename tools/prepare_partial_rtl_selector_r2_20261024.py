from pathlib import Path
import hashlib,json,tarfile
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'module_14_lm_head_v4/experiments/partial_rtl_20261024';R=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261024_r1'
RTL=ROOT/'module_14_lm_head_v4/reports/partial_hw_20261024_r1/r3/remote_hls/syn/verilog'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (R/'r2/PLAN.json').exists();(R/'r2').mkdir();(E/'r2').mkdir()
extra=[RTL/'lm_head_v4_partial_proto_flow_control_loop_pipe_sequential_init.v',RTL/'lm_head_v4_partial_proto_mux_42_32_1_1.v']
files=(E/'radix_sources.txt').read_text()+''.join(str(p.relative_to(ROOT)).replace('\\','/')+'\n' for p in extra)
(E/'r2/radix_sources.txt').write_text(files,encoding='utf-8')
s=(E/'run_selector.py').read_text().replace('parents[3]','parents[4]').replace('E=Path(__file__).resolve().parent;','E=Path(__file__).resolve().parents[1];').replace("reports/partial_rtl_20261024_r1'","reports/partial_rtl_20261024_r1/r2'").replace("(E/'radix_sources.txt')","(E/'r2/radix_sources.txt')").replace('p64_rtl_selector_r1','p64_rtl_selector_r2')
(E/'r2/run_selector.py').write_text(s,encoding='utf-8')
plan=json.loads((R/'PLAN.json').read_text());plan.update(parent_plan_sha256=sha(R/'PLAN.json'),revision='r2 test-entry dependency closure only; frozen DUT/adapter/test vectors/model unchanged',r1_verdict='Compile passed; elaboration missing two generated dependency modules; no RTL execution')
for p in extra+list((E/'r2').iterdir())+[Path(__file__)]:plan['source_sha256'][str(p.relative_to(ROOT)).replace('\\','/')]=sha(p)
(R/'r2/PLAN.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
with tarfile.open(R/'selector_r2_entry.tar.gz','w:gz') as tar:
    for p in list((E/'r2').iterdir())+[R/'r2/PLAN.json',Path(__file__)]:tar.add(p,arcname=str(p.relative_to(ROOT)).replace('\\','/'))
print('R2_ENTRY_FROZEN')
