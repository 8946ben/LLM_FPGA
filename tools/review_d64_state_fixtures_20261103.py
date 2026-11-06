"""Audit fixed-input/control preparation only; never grants RTL qualification."""
from pathlib import Path
import json,struct,hashlib,datetime
from prepare_d64_state_fixtures_20261103 import ROOT,M,E,R,F,sha,words
def main():
 p=R/'MANIFEST.json';manifest=json.loads(p.read_text());control=json.loads((E/'control_sequences.json').read_text())
 assert manifest['state']=='PREPARED_AND_SOURCE_REFERENCE_BOUND_NOT_SIMULATED' and control['state']=='CONTROL_SEQUENCES_PREPARED_NOT_EXECUTED'
 assert control['manifest_sha256']==sha(p) and not (R/'ACTIVE.lock').exists() and not (R/'WORKFLOW.json').exists()
 assert control['board']==control['eda']=='NOT_RUN'
 for n,h in manifest['source_sha256'].items():assert sha(ROOT/n)==h,n
 for n,j in manifest['weight_assets'].items():assert (ROOT/n).stat().st_size==j['bytes'] and sha(ROOT/n)==j['sha256'],n
 scenarios=manifest['scenarios'];assert json.loads((E/'scenarios.json').read_text())==scenarios
 expected_labels=['A0_debug','B0_production','A1_debug','Z0_ties','E_capacity','E_flag','E_hidden_nan','E_rms_nan','E_rms_negative','E_preview_nan','A2_after_errors']
 assert [x['label'] for x in scenarios]==expected_labels
 data=[]
 for i,(s,c) in enumerate(zip(scenarios,control['sequences'],strict=True)):
  f=ROOT/s['input_path'];b=f.read_bytes();assert sha(f)==s['input_sha256'] and len(b)==24368
  assert s['case_index']==c['case_index']==i and s['label']==c['label'];data.append(b)
  assert not c['reset_dut_before_case'] and not c['reload_full_weights'] and c['workspace_persists']
  shadow={w['address']:w['value'] for w in c['parameter_writes']};assert len(shadow)==10
  assert all(w['strobe']==15 for w in c['parameter_writes'])
  # Independent fixed ABI decode from the source register map, not field labels.
  assert shadow[0x10]+(shadow[0x14]<<32)==0
  assert shadow[0x1c]+(shadow[0x20]<<32)==0
  assert shadow[0x28]+(shadow[0x2c]<<32)==273416192
  assert shadow[0x34]+(shadow[0x38]<<32)==24368
  assert shadow[0x40]==s['capacity'] and shadow[0x48]==s['debug']
  assert {x['address']:x['expected'] for x in c['parameter_readbacks']}==shadow
  assert c['start_write']=={'address':0,'value':1,'strobe':15}
  assert c['output_validity_clear_before_start']==c['output_validity_required_after_done']==[0x54,0x64,0x74,0x84,0x94,0xa8]
  assert c['output_reads']=={'status':[0x50],'token':[0x60],'score_bits':[0x70],'candidate_count':[0x80],'output_crc':[0x90],'preview_read_beats':[0xa0,0xa4]}
 assert data[0]==data[2]==data[4]==data[5]==data[9]==data[10]==(F/'old_chinese.meta.bin').read_bytes()
 assert data[1]==(F/'old_english.meta.bin').read_bytes() and data[0]!=data[1]
 assert data[3][:1792]==bytes(1792) and data[3]==(F/'zero_hidden.meta.bin').read_bytes()
 for i,offset,expected in [(6,0,b'\xc0\x7f'),(7,1792,b'\x00\x00\xc0\x7f'),(8,1792,b'\x00\x00\x80\xbf')]:
  assert data[i][offset:offset+len(expected)]==expected
  assert data[i][:offset]==data[0][:offset] and data[i][offset+len(expected):]==data[0][offset+len(expected):]
 assert scenarios[4]['capacity']==79067 and scenarios[4]['expected']['expected_status']==1
 assert scenarios[5]['debug']==2 and scenarios[5]['expected']['expected_status']==1
 for i in [6,7,8,9]:assert scenarios[i]['expected']['expected_status']==2
 injection=scenarios[9]['mutations'];assert len(injection)==1 and injection[0]['region']=='weights' and injection[0]['restore_after'] and injection[0]['replacement_hex']=='c07f'
 dims=words((F/'old_chinese.dims.bin').read_bytes());assert injection[0]['offset_bytes']==dims[0]*2048 and injection[0]['width_bytes']==2
 with (M/'reports/layout_topk_20261024_r1/assets/tiled_W_B1024.bin').open('rb') as f:f.seek(dims[0]*2048);assert f.read(2).hex()==injection[0]['expected_original_hex']
 assert scenarios[9]['access_invariants']['canonical_weight_reads']==0
 for i in [4,5,6,7,8]:assert scenarios[i]['access_invariants']['weight_reads']==scenarios[i]['access_invariants']['workspace_writes']==0
 for i in [4,5]:assert scenarios[i]['access_invariants']['meta_reads']==0
 for i in [4,5,6,7,8,9]:
  v=scenarios[i]['expected'];assert all(v[k]==0 for k in ['token','score_bits','crc','k','preview_read_beats'])
 control_source=M/'reports/memory_growth_diagnosis_20261103_r1/sources/lm_head_v4_partial_proto_control_s_axi.v';assert sha(control_source)==control['control_rtl_sha256']
 proto=M/'experiments/partial_hw_20261024/partial_proto.cpp';source=proto.read_text();assert 'if(capacity_beats<P_WS_BEATS || debug>1) {*status=1;return;}' in source
 assert '*status=0;*token=0;*score_bits=0;*candidate_count=0;*output_crc=0;*preview_read_beats=0;' in source
 out=dict(state='PASS_INDEPENDENT_PREPARED_STATE_FIXTURES_AND_CONTROL_ONLY',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),cases=11,aba_same_bytes=True,weight_assets_bound_bytes=545685504,validity_flags_and_64bit_registers_checked=True,
  manifest_sha256=sha(p),control_sequences_sha256=sha(E/'control_sequences.json'),contract_cpp_sha256=sha(proto),fixture_inputs_sha256={x['label']:x['input_sha256'] for x in scenarios},
  qualifications_not_granted=['No RTL compile/run','No new memory-response model qualification','No full A/B/A/mode/error hardware qualification','No new latency/throughput numbers'],board='NOT_RUN',automatic_next_stage=False)
 (R/'INDEPENDENT_PREPARATION_REVIEW.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
