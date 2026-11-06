from pathlib import Path
import hashlib,json,tarfile
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'module_14_lm_head_v4/experiments/partial_rtl_20261024';R=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261024_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (R/'r3/PLAN.json').exists();(R/'r3').mkdir();(E/'r3').mkdir()
s=(E/'radix_tb.sv').read_text().replace('while(!done)','while(done!==1\'b1)')
s=s.replace('string fixtures;','string fixtures;string outputs;')
s=s.replace('KVALUES','KVALUES')
s=s.replace('ks[0]=', 'if(!$value$plusargs("outputs=%s",outputs))$fatal(1,"outputs missing");\nks[0]=',1)
s=s.replace('$display("RADIX_CASE_PASS', '$writememh($sformatf("%s/actual_%02d.hex",outputs,ci),mem.data);\n$display("RADIX_CASE_PASS')
(E/'r3/radix_tb.sv').write_text(s,encoding='utf-8')
runner=(E/'r2/run_selector.py').read_text().replace("partial_rtl_20261024_r1/r2'","partial_rtl_20261024_r1/r3'").replace('p64_rtl_selector_r2','p64_rtl_selector_r3').replace("str(E/'radix_tb.sv')","str(E/'r3/radix_tb.sv')")
runner=runner.replace("'fixtures='+str(E/'fixtures')","'fixtures='+str(E/'fixtures'),'-testplusarg','outputs='+str(R/'actual')")
runner=runner.replace("lock=R/'ACTIVE.lock';","(R/'actual').mkdir();lock=R/'ACTIVE.lock';")
(E/'r3/run_selector.py').write_text(runner,encoding='utf-8')
plan=json.loads((R/'r2/PLAN.json').read_text());plan.update(parent_plan_sha256=sha(R/'r2/PLAN.json'),revision='r3 testbench 4state done wait and complete saved output; DUT/adapter/model/vectors unchanged',r2_verdict='Compile/elaboration passed; testbench X-sensitive while(!done) skipped wait at45ns; no valid kernel result; fail retained')
for p in list((E/'r3').iterdir())+[Path(__file__)]:plan['source_sha256'][str(p.relative_to(ROOT)).replace('\\','/')]=sha(p)
(R/'r3/PLAN.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
with tarfile.open(R/'selector_r3_entry.tar.gz','w:gz') as tar:
    for p in list((E/'r3').iterdir())+[R/'r3/PLAN.json',Path(__file__)]:tar.add(p,arcname=str(p.relative_to(ROOT)).replace('\\','/'))
print('R3_ENTRY_FROZEN')
