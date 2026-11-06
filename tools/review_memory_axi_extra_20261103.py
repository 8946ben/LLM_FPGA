"""Reproducible audit of reuse/geometry/monitor-scope controls (r6-r8)."""
import json,csv,datetime
import review_memory_axi_gate_20261103 as a
def main():
 hashes={6:'bc728e6c0ea491b3a53feab49522139be10e3d5d09eee04b863c92cf11751486',7:'5584f8792a65da8ee7568f34e5467fc676462f803e63b4348cb2907bacde1004',8:'6dc4c872d3f8394e7c11dc47e774c875eff94571bcd6530549a72af46d3ce41e'}
 result={};baseline=a.sha(a.M/'reports/memory_axi_gate_20261103_r1/mode_axi/axi_wire.csv')
 for i,h in hashes.items():
  a.extract(i,h);name='memory_axi_gate_20261103_r%d'%i;r,p,w=a.ready(name);e=a.M/'experiments'/name
  compiled=json.loads((r/'COMPILED_SOURCES.json').read_text())
  for stem in ['axi_transfer','axi_state','axi_slave_seq_lib','axi_monitor']:
   if (e/(stem+'.sv')).exists():assert compiled['axivip/'+stem+'.sv']==a.sha(e/(stem+'.sv'))
  wire=r/'mode_axi/axi_wire.csv'
  traffic=a.replay(wire,8194 if i==7 else 1026)
  samples=[[int(x) for x in row] for row in csv.reader((r/'mode_axi/axi_epoch_samples.csv').open())]
  assert [x[0] for x in samples]==list(range(5)) and all(x[-1]==0 for x in samples)
  growth=(samples[-1][2]-samples[0][2])/1024
  if i==8:
   assert a.sha(wire)==baseline
   j=json.loads((e/'MONITOR_CHANGES.json').read_text());source=a.M/'reports/memory_growth_diagnosis_20261103_r1/sources/axivip/axi_monitor.sv';text=(e/'axi_monitor.sv').read_text()
   assert a.sha(source)==j['original_sha256'] and a.sha(e/'axi_monitor.sv')==j['candidate_sha256']
   for before,after in reversed(j['edits']):assert text.count(after)==1;text=text.replace(after,before)
   assert text==source.read_text()
  old=json.loads((r/'INDEPENDENT_REVIEW.json').read_text());assert old['kernel_growth_mib']==growth and old['wire_sha256']==a.sha(wire)
  out=dict(state='PASS_INDEPENDENT_RECHECK',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),control=i,traffic=traffic,growth_mib=growth,wire_equal_original=(a.sha(wire)==baseline),original_review_sha256=a.sha(r/'INDEPENDENT_REVIEW.json'),sources=compiled,adopted=(i==8))
  (r/'INDEPENDENT_RECHECK.json').write_text(json.dumps(out,indent=2)+'\n');result[name]={k:out[k] for k in ['growth_mib','wire_equal_original','adopted']}
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
