"""Derive planned control writes from frozen RTL register constants; no hardware I/O."""
from pathlib import Path
import json,re,hashlib,datetime
from prepare_d64_state_fixtures_20261103 import ROOT,M,E,R,sha
def main():
 manifest=json.loads((R/'MANIFEST.json').read_text());assert manifest['state']=='PREPARED_AND_SOURCE_REFERENCE_BOUND_NOT_SIMULATED'
 source=M/'reports/memory_growth_diagnosis_20261103_r1/sources/lm_head_v4_partial_proto_control_s_axi.v';text=source.read_text()
 registers={name:int(number,16) for name,number in re.findall(r'\b(ADDR_[A-Z0-9_]+)\s*=\s*8\x27h([0-9a-fA-F]+)',text)}
 expected={'ADDR_AP_CTRL','ADDR_GIE','ADDR_IER','ADDR_ISR'}
 for field in ['META_OFFSET','TILED_WEIGHT','CANONICAL_WEIGHT','WORKSPACE','CAPACITY_BEATS','DEBUG','STATUS','TOKEN','SCORE_BITS','CANDIDATE_COUNT','OUTPUT_CRC','PREVIEW_READ_BEATS']:
  expected.add('ADDR_'+field+'_DATA_0');expected.add('ADDR_'+field+'_CTRL')
  if field in ['META_OFFSET','TILED_WEIGHT','CANONICAL_WEIGHT','WORKSPACE','PREVIEW_READ_BEATS']:expected.add('ADDR_'+field+'_DATA_1')
 assert set(registers)==expected and len(set(registers.values()))==len(registers) and registers['ADDR_AP_CTRL']==0
 values={'META_OFFSET':0,'TILED_WEIGHT':0,'CANONICAL_WEIGHT':273416192,'WORKSPACE':24368}
 output_fields=['STATUS','TOKEN','SCORE_BITS','CANDIDATE_COUNT','OUTPUT_CRC','PREVIEW_READ_BEATS']
 sequences=[]
 for scenario in manifest['scenarios']:
  writes=[];roundtrip=[]
  for field,value in values.items():
   for index in [0,1]:
    address=registers['ADDR_'+field+'_DATA_'+str(index)];word=(value>>(index*32))&0xffffffff
    writes.append({'address':address,'value':word,'strobe':15,'field':field+'['+str(index)+']'});roundtrip.append({'address':address,'expected':word})
  for field,value in [('CAPACITY_BEATS',scenario['capacity']),('DEBUG',scenario['debug'])]:
   address=registers['ADDR_'+field+'_DATA_0'];writes.append({'address':address,'value':value,'strobe':15,'field':field});roundtrip.append({'address':address,'expected':value})
  outputs={field.lower():[registers['ADDR_'+field+'_DATA_0']]+([registers['ADDR_'+field+'_DATA_1']] if field=='PREVIEW_READ_BEATS' else []) for field in output_fields}
  validity=[registers['ADDR_'+field+'_CTRL'] for field in output_fields]
  sequences.append(dict(case_index=scenario['case_index'],label=scenario['label'],parameter_writes=writes,parameter_readbacks=roundtrip,start_write={'address':0,'value':1,'strobe':15},output_reads=outputs,
   output_validity_clear_before_start=validity,output_validity_required_after_done=validity,
   before_start='Read AP_CTRL and output validity flags to clear stale state; assert start/autorestart clear and idle set. Complete all parameter write/readback handshakes first.',
   completion='Require real start/busy/done for this frame, read actual outputs and then verify done clears on read. Do not accept idle done before a start.',
   reset_dut_before_case=False,reload_full_weights=False,workspace_persists=True))
 out={'state':'CONTROL_SEQUENCES_PREPARED_NOT_EXECUTED','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'manifest_sha256':sha(R/'MANIFEST.json'),'control_rtl_sha256':sha(source),'registers':registers,'sequences':sequences,
  'normal_response_condition':'NOT_IMPLEMENTED_OR_QUALIFIED; these are planned control transactions only','eda':'NOT_RUN','board':'NOT_RUN','automatic_next_stage':False}
 assert len(sequences)==11
 path=E/'control_sequences.json';assert not path.exists();path.write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({'state':out['state'],'cases':len(sequences),'registers':len(registers),'output':str(path)},indent=2))
if __name__=='__main__':main()
