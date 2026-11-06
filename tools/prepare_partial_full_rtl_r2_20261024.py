from pathlib import Path
import hashlib,json,tarfile
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'module_14_lm_head_v4/experiments/partial_rtl_20261024';R=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261024_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (R/'full_r2/PLAN.json').exists();(R/'full_r2').mkdir()
t=(E/'full_cosim.tcl').read_text().replace('p64_rtl_full_r1','p64_rtl_full_r2').replace('open_project $build','cd [file dirname $build]\nopen_project [file tail $build]').replace('full_fixtures]','full_fixtures_r2]')
(E/'full_cosim_r2.tcl').write_text(t,encoding='utf-8')
s=(E/'run_full.py').read_text().replace('partial_rtl_20261024_r1/full_r1','partial_rtl_20261024_r1/full_r2').replace('p64_rtl_full_r1','p64_rtl_full_r2').replace("E/'full_fixtures'","E/'full_fixtures_r2'").replace("E/'full_cosim.tcl'","E/'full_cosim_r2.tcl'")
(E/'run_full_r2.py').write_text(s,encoding='utf-8')
plan=json.loads((R/'full_r1/PLAN.json').read_text());plan.update(parent_plan_sha256=sha(R/'full_r1/PLAN.json'),r1_verdict='HLS open_project rejects absolute project name; failed before C reference/RTL. Clone and failure preserved',revision='Only cd to build parent and open relative project name; same full TB and exact frozen r3 synthesis')
files=[E/'full_cosim_r2.tcl',E/'run_full_r2.py',Path(__file__)]
for p in files:plan['source_sha256'][str(p.relative_to(ROOT)).replace('\\','/')]=sha(p)
(R/'full_r2/PLAN.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
with tarfile.open(R/'full_r2/entry.tar.gz','w:gz') as tar:
    for p in files+[R/'full_r2/PLAN.json']:tar.add(p,arcname=str(p.relative_to(ROOT)).replace('\\','/'))
print('FULL_RTL_R2_ENTRY_FROZEN')
