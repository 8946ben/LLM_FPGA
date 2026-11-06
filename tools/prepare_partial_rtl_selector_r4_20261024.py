from pathlib import Path
import hashlib,json,tarfile
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'module_14_lm_head_v4/experiments/partial_rtl_20261024';R=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261024_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (R/'r4/PLAN.json').exists();(R/'r4').mkdir();(E/'r4').mkdir()
s=(E/'r3/radix_tb.sv').read_text().replace('@(negedge clk);start=1;cycles=0;','@(negedge clk);start=1;cycles=0;\n// The generated submodule asserts done while idle; sample only after start propagates.\n@(negedge clk);')
(E/'r4/radix_tb.sv').write_text(s,encoding='utf-8')
s=(E/'r3/run_selector.py').read_text().replace("partial_rtl_20261024_r1/r3'","partial_rtl_20261024_r1/r4'").replace('p64_rtl_selector_r3','p64_rtl_selector_r4').replace("E/'r3/radix_tb.sv'","E/'r4/radix_tb.sv'")
(E/'r4/run_selector.py').write_text(s,encoding='utf-8')
plan=json.loads((R/'r3/PLAN.json').read_text());plan.update(parent_plan_sha256=sha(R/'r3/PLAN.json'),revision='r4 testbench accepts idle-high ap_done semantics; no DUT/model/vector change',r3_verdict='TB sampled idle-high done in same delta as start assertion; source line1140 proves done high while idle; 45ns failure is not kernel failure')
for p in list((E/'r4').iterdir())+[Path(__file__)]:plan['source_sha256'][str(p.relative_to(ROOT)).replace('\\','/')]=sha(p)
(R/'r4/PLAN.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
with tarfile.open(R/'selector_r4_entry.tar.gz','w:gz') as tar:
    for p in list((E/'r4').iterdir())+[R/'r4/PLAN.json',Path(__file__)]:tar.add(p,arcname=str(p.relative_to(ROOT)).replace('\\','/'))
print('R4_ENTRY_FROZEN')
