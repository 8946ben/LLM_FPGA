from pathlib import Path
import hashlib,json,tarfile
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'module_14_lm_head_v4/experiments/partial_rtl_20261024';R=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261024_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (R/'full_r3/PLAN.json').exists();(R/'full_r3').mkdir()
t=(E/'full_cosim_r2.tcl').read_text().replace('p64_rtl_full_r2','p64_rtl_full_r3').replace('full_fixtures_r2','full_fixtures_r3')
t='\n'.join(line for line in t.splitlines() if not line.startswith('remove_files') and not line.startswith('add_files -tb'))+'\n'
(E/'full_cosim_r3.tcl').write_text(t,encoding='utf-8')
s=(E/'run_full_r2.py').read_text().replace('partial_rtl_20261024_r1/full_r2','partial_rtl_20261024_r1/full_r3').replace('p64_rtl_full_r2','p64_rtl_full_r3').replace('full_fixtures_r2','full_fixtures_r3').replace('full_cosim_r2.tcl','full_cosim_r3.tcl')
anchor="    old={str(p.relative_to(before)):sha(p) for p in (before/'solution1/syn/verilog').glob('*') if p.is_file()}"
assert anchor in s
s=s.replace(anchor,"""    app=after/'hls.app';app_before=app.read_text()
    previous=str(ROOT/'module_14_lm_head_v4/experiments/partial_hw_20261024/proto_tb.cpp')
    replacement=str(E/'full_tb.cpp');assert app_before.count(previous)==1
    app_after=app_before.replace(previous,replacement);app.write_text(app_after)
    write(R/'PROJECT_TESTBENCH_REBIND.json',dict(state='ONE_TB_PATH_ONLY',before_sha256=hashlib.sha256(app_before.encode()).hexdigest(),after_sha256=sha(app),old_path=previous,new_path=replacement,design_files_and_flags_unchanged=True))
"""+anchor)
(E/'run_full_r3.py').write_text(s,encoding='utf-8')
plan=json.loads((R/'full_r2/PLAN.json').read_text());plan.update(parent_plan_sha256=sha(R/'full_r2/PLAN.json'),r2_verdict='Tool project open succeeded; installed2022.2 has no remove_files command; failed before C reference/RTL; actual command table inspected',revision='Clone project app replaces one tb filename only; no unsupported remove_files/add_files; no synthesis/source/FIFO change')
files=[E/'full_cosim_r3.tcl',E/'run_full_r3.py',Path(__file__)]
for p in files:plan['source_sha256'][str(p.relative_to(ROOT)).replace('\\','/')]=sha(p)
(R/'full_r3/PLAN.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
with tarfile.open(R/'full_r3/entry.tar.gz','w:gz') as tar:
    for p in files+[R/'full_r3/PLAN.json']:tar.add(p,arcname=str(p.relative_to(ROOT)).replace('\\','/'))
print('FULL_RTL_R3_ENTRY_FROZEN')
