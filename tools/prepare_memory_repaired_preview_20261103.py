"""Freeze one real-DUT first-five-block gate after reviewed memory fixes."""
from pathlib import Path
import json,hashlib,tarfile,shutil
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';NAME='memory_repaired_preview_20261103_r1'
E=M/'experiments'/NAME;R=M/'reports'/NAME
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 E.mkdir();R.mkdir();base=M/'experiments/memory_full_startup_20261103_r1';axi=M/'experiments/memory_axi_gate_20261103_r8'
 for n in ['reference_model.sv','lm_head_v4_partial_proto_subsys_test_sequence_lib.sv','memory_probe_pkg.sv']:shutil.copy2(base/n,E/n)
 shutil.copy2(M/'experiments/memory_burst_model_20261103_r3/mem_model.sv',E/'mem_model.sv')
 for n in ['axi_state.sv','axi_transfer.sv','axi_slave_seq_lib.sv','axi_monitor.sv']:shutil.copy2(axi/n,E/n)
 shutil.copy2(M/'experiments/fifo_rle_monitor_20261103_r1/df_fifo_monitor.svh',E/'df_fifo_monitor.svh')
 shutil.copy2(M/'experiments/sim_memory_bank_20261026/preview5.tcl',E/'preview5.tcl')
 changes=json.loads((base/'CHANGES.json').read_text());p=E/'axi_state.sv';text=p.read_text()
 for before,after in changes['axi_state']['edits']:assert text.count(before)==1;text=text.replace(before,after)
 p.write_text(text)
 changes['axi_state']['edits']=json.loads((axi/'STATE_CHANGES.json').read_text())['edits']+changes['axi_state']['edits']
 changes['mem_model']['edits']+=json.loads((M/'experiments/memory_burst_model_20261103_r3/MODEL_CHANGES.json').read_text())['edits']
 for field,n,target in [('axi_transfer','TRANSFER_CHANGES.json','axivip/axi_transfer.sv'),('axi_monitor','MONITOR_CHANGES.json','axivip/axi_monitor.sv')]:
  j=json.loads((axi/n).read_text());changes[field]={'original':target,'original_sha256':j['original_sha256'],'edits':j['edits']}
 j=json.loads((axi/'SEQUENCE_CHANGES.json').read_text());changes['axi_slave_seq_lib']={'original':'axivip/axi_slave_seq_lib.sv','original_sha256':j['original_sha256'],'edits':[[a,b] for a,b,count in j['edits']],'occurrences':2}
 j=json.loads((M/'experiments/fifo_rle_monitor_20261103_r1/MONITOR_CHANGES.json').read_text());changes['fifo_monitor']={'original':'df_fifo_monitor.svh','original_sha256':j['original_sha256'],'edits':j['edits']}
 (E/'CHANGES.json').write_text(json.dumps(changes,indent=2)+'\n')
 gates={'input':'memory_burst_full_input_20261103_r1','axi':'memory_axi_gate_20261103_r8','fifo':'fifo_rle_monitor_20261103_r1','control':'memory_control_regression_20261103_r1'}
 reviews={}
 for label,name in gates.items():
  path=M/'reports'/name/'INDEPENDENT_REVIEW.json';data=json.loads(path.read_text());assert data['state'].startswith('PASS_')
  dest=E/('gate_'+label+'.json');shutil.copy2(path,dest);reviews[dest.name]={'sha256':sha(dest),'state':data['state']}
 assert json.loads((E/'gate_input.json').read_text())['model_sha256']==sha(E/'mem_model.sv')
 assert json.loads((E/'gate_axi.json').read_text())['monitor_sha256']==sha(E/'axi_monitor.sv')
 assert json.loads((E/'gate_fifo.json').read_text())['monitor_sha256']==sha(E/'df_fifo_monitor.svh')
 runner=(ROOT/'tools/run_memory_full_startup_20261103.py').read_text().replace('memory_full_startup_20261103_r1',NAME)
 before="plan=json.loads((R/'PLAN.json').read_text());guard=plan['guards']"
 after=before+"\n for n,j in plan['gate_reviews'].items():\n  assert sha(E/n)==j['sha256'] and json.loads((E/n).read_text())['state']==j['state'],n"
 assert runner.count(before)==1;runner=runner.replace(before,after)
 runner=runner.replace("'mem_model.sv':'file_agent/mem_model.sv','axi_state.sv':'axivip/axi_state.sv',", "'mem_model.sv':'file_agent/mem_model.sv','axi_state.sv':'axivip/axi_state.sv',\n   'axi_transfer.sv':'axivip/axi_transfer.sv','axi_slave_seq_lib.sv':'axivip/axi_slave_seq_lib.sv','axi_monitor.sv':'axivip/axi_monitor.sv','df_fifo_monitor.svh':'df_fifo_monitor.svh',")
 runner=runner.replace("for name in ['memory_probe_pkg.sv','memory_prefix.sv']", "for name in ['memory_probe_pkg.sv','preview5.tcl']")
 runner=runner.replace('assert len(unchanged)==119','assert len(unchanged)==116')
 runner=runner.replace("+'\\nsv xil_defaultlib \"memory_prefix.sv\"\\n'", "+'\\n'")
 runner=runner.replace("-tclbatch startup.tcl'", "-tclbatch preview5.tcl'")
 runner=runner.replace("assert sum(x.startswith('MEMORY_PREFIX_PASS cycles=20000 ') for x in lines)==1", "assert sum(re.fullmatch(r'BANK_PREVIEW5_STOP \\d+ ps',x) is not None for x in lines)==1")
 runner=runner.replace("for name in ['memory_phases.csv','weights_readback.csv','stage_profile.csv']", "for name in ['memory_phases.csv','weights_readback.csv','stage_profile.csv','preview5.vcd']")
 runner=runner.replace('TOOL_PASS_FINITE_PREFIX_AWAITING_INDEPENDENT_REVIEW','TOOL_PASS_FIRST5_MEMORY_REPAIRED_AWAITING_INDEPENDENT_REVIEW')
 runner=runner.replace('GROUP_RSS_OVER_64GIB','GROUP_RSS_OVER_LIMIT')
 # Preserve variable-sized trace files only after the simulator returns.
 runner=runner.replace("  assert sha(tv)==fullplan['full_tv_sha256']\n  for p,h in fullplan", "  for trace in V.glob('*.rle'):shutil.copy2(trace,R/trace.name)\n  for status in V.glob('chan_status*.csv'):shutil.copy2(status,R/status.name)\n  assert sha(tv)==fullplan['full_tv_sha256']\n  for p,h in fullplan")
 compile(runner,'preview_runner.py','exec');(E/'run_startup.py').write_text(runner)
 original=json.loads((M/'reports/memory_full_startup_20261103_r1/PLAN.json').read_text())
 plan=dict(state='FROZEN_REPAIRED_MEMORY_REAL_DUT_FIRST5',source_sha256={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in E.iterdir() if p.is_file()},baseline_sources=original['baseline_sources'],gate_reviews=reviews,
  guards={'initial_available_gib':96,'running_available_gib':32,'group_rss_gib':32,'elaborate_seconds':300,'simulate_seconds':7200},
  scope='Original full weights and compute RTL/FP32/finite FIFO/random latency classes; only reviewed verification-model repairs, MASTER guard and 2000-cycle polling; RNG identity distinct from historical20-cycle polling. Stop at first AR for tile6, not full M14.',
  full_m14='NOT_RUN',c_postcheck='NOT_RUN',board='NOT_RUN',automatic_next_stage=False)
 (R/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
 with tarfile.open(R/'entry.tar.gz','w:gz') as t:
  for p in list(E.iterdir())+[R/'PLAN.json']:t.add(p,arcname=str(p.relative_to(ROOT)))
 template=(ROOT/'tools/bootstrap_memory_full_startup_20261103.py').read_text().replace('memory_full_startup_20261103_r1',NAME).replace(sha(M/'reports/memory_full_startup_20261103_r1/entry.tar.gz'),sha(R/'entry.tar.gz'))
 (ROOT/'tools/bootstrap_memory_repaired_preview_20261103.py').write_text(template)
 print(json.dumps({'archive':str(R/'entry.tar.gz'),'sha256':sha(R/'entry.tar.gz'),'guards':plan['guards']}))
if __name__=='__main__':main()
