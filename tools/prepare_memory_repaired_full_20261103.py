"""Prepare full generated RTL only after manual independent first-five-block gate."""
from pathlib import Path
import json,hashlib,tarfile,shutil
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';BASE='memory_repaired_preview_20261103_r1';NAME='memory_repaired_full_20261103_r1'
E=M/'experiments'/NAME;R=M/'reports'/NAME
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 gate=M/'reports'/BASE/'INDEPENDENT_REVIEW.json';assert json.loads(gate.read_text())['state']=='PASS_INDEPENDENT_REPAIRED_REAL_DUT_FIRST5'
 E.mkdir();R.mkdir();source=M/'experiments'/BASE
 for p in source.iterdir():
  if p.is_file() and p.name not in ['run_startup.py','preview5.tcl']:shutil.copy2(p,E/p.name)
 shutil.copy2(gate,E/'gate_preview.json')
 runner=(source/'run_startup.py').read_text().replace(BASE,NAME)
 runner=runner.replace('Remote bounded initialization/prefix runner. No C postcheck or full call.','One full generated RTL call and unchanged C postcheck, after independent gates.')
 runner=runner.replace("full_m14='NOT_RUN'", "full_m14='ONE_ORIGINAL_OLD_CHINESE_DEBUG1_CALL'")
 runner=runner.replace("for name in ['memory_probe_pkg.sv','preview5.tcl']", "for name in ['memory_probe_pkg.sv']")
 runner=runner.replace('-tclbatch preview5.tcl','-tclbatch startup.tcl')
 runner=runner.replace("  assert sum(re.fullmatch(r'BANK_PREVIEW5_STOP \\d+ ps',x) is not None for x in lines)==1", "  assert any(re.fullmatch(r'LMH_RANGE_GUARD_SUMMARY meta_read_bursts=\\d+ meta_write_bursts=\\d+ weight_read_bursts=\\d+',x) for x in lines)")
 before="  for name in ['memory_phases.csv','weights_readback.csv','stage_profile.csv','preview5.vcd']:shutil.copy2(V/name,R/name)"
 after='''  returned=list((NEW/'tv/rtldatafile').glob('*autotvout*.dat'));assert len(returned)==7
  for returned_file in returned:assert returned_file.stat().st_size>0 and '[[[/runtime]]]' in returned_file.read_text(),returned_file.name
  wrapped=NEW/'wrapc_pc';wrapped.mkdir();shutil.copy2(OLD.parent/'wrapc_pc/cosim.pc.exe',wrapped/'cosim.pc.exe')
  assert sha(wrapped/'cosim.pc.exe')==fullplan['postchecker_sha256']
  fixtures=R/'fixtures';fixtures.mkdir();original_fixtures=M/'experiments/partial_rtl_20261024/full_fixtures_r3'
  for fixture in original_fixtures.iterdir():
   if fixture.is_file() and (fixture.name.startswith('old_chinese.') or fixture.name=='weight_paths.txt'):shutil.copy2(fixture,fixtures/fixture.name)
  assert not (fixtures/'actual_RTL_full_chinese.bin').exists()
  # C postcheck uses the unchanged generated executable and new raw returned TV.
  saved_dir=V;V=wrapped
  try:run('c_postcheck','./cosim.pc.exe "'+str(fixtures)+'"',180)
  finally:V=saved_dir
  assert 'PARTIAL_FULL_RTL_REFERENCE_PASS calls=1 full_arrays=1' in (R/'c_postcheck.log').read_text()
  shutil.copy2(fixtures/'actual_RTL_full_chinese.bin',R/'actual_RTL_full_chinese.bin')
  (R/'returned_tv').mkdir()
  for returned_file in returned:shutil.copy2(returned_file,R/'returned_tv'/returned_file.name)
  for name in ['memory_phases.csv','weights_readback.csv','stage_profile.csv']:shutil.copy2(V/name,R/name)'''
 assert runner.count(before)==1;runner=runner.replace(before,after)
 # V is captured by run(); declare it global before the first V access in main.
 runner=runner.replace('def main():\n', 'def main():\n global V\n',1)
 runner=runner.replace('TOOL_PASS_FIRST5_MEMORY_REPAIRED_AWAITING_INDEPENDENT_REVIEW','GENERATED_XSIM_AND_C_POSTCHECK_PASS_AWAITING_NUMERIC_AND_FIFO_REVIEW')
 runner=runner.replace("  for status in V.glob('chan_status*.csv'):shutil.copy2(status,R/status.name)", "  for status in V.glob('chan_status*.csv'):shutil.copy2(status,R/status.name)\n  for artifact in V.glob('*.rpt'):shutil.copy2(artifact,R/artifact.name)")
 # Avoid dropping completed arrays/profile if a later checker fails; originals remain in cache.
 compile(runner,'full_runner.py','exec');(E/'run_startup.py').write_text(runner)
 plan=json.loads((M/'reports'/BASE/'PLAN.json').read_text());plan['gate_reviews']['gate_preview.json']={'sha256':sha(E/'gate_preview.json'),'state':'PASS_INDEPENDENT_REPAIRED_REAL_DUT_FIRST5'}
 plan.update(state='FROZEN_REPAIRED_MEMORY_FULL_GENERATED_RTL',source_sha256={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in E.iterdir() if p.is_file()},
  guards={'initial_available_gib':96,'running_available_gib':32,'group_rss_gib':64,'elaborate_seconds':300,'simulate_seconds':172800},
  full_m14='ONE_ORIGINAL_OLD_CHINESE_DEBUG1_CALL',c_postcheck='UNCHANGED_GENERATED_EXECUTABLE',official_cosim_formatter='NOT_RUN',
  scope='One original full old_chinese/d64/T4096/B1024/dual weights/debug1; frozen compute RTL/FP32/finite FIFO/random latency classes; reviewed verification support fixes. New RNG identity due2000-polling. No automatic ABA/perf/implementation/board.',
  resource_budget={'gate_read_beats':131104,'gate_kernel_growth_mib':1918.0703125,'expected_preview_weight_beats':1220608,'expected_candidate_weight_beats':4109*112,'simple_weight_only_growth_gib':1918.0703125/1024*(1220608+4109*112)/131104,'notes':'Finite-gate extrapolation only, excludes metadata/other phases, not a theoretical upper bound;64GiB guard is below historical128GiB and is never auto-raised'})
 (R/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
 with tarfile.open(R/'entry.tar.gz','w:gz') as t:
  for p in list(E.iterdir())+[R/'PLAN.json']:t.add(p,arcname=str(p.relative_to(ROOT)))
 template=(ROOT/'tools/bootstrap_memory_repaired_preview_20261103.py').read_text().replace(BASE,NAME).replace(sha(M/'reports'/BASE/'entry.tar.gz'),sha(R/'entry.tar.gz'))
 (ROOT/'tools/bootstrap_memory_repaired_full_20261103.py').write_text(template)
 print(json.dumps({'archive':str(R/'entry.tar.gz'),'sha256':sha(R/'entry.tar.gz'),'resource_budget':plan['resource_budget']}))
if __name__=='__main__':main()
