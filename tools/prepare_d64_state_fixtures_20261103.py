"""Prepare actual fixed inputs for post-full state/mode tests, without EDA."""
from pathlib import Path
import json,hashlib,struct,datetime
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4'
NAME='d64_state_fixtures_20261103_r1';E=M/'experiments'/NAME;R=M/'reports'/NAME
F=M/'experiments/partial_hw_20261024/fixtures'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def words(data):assert len(data)%4==0;return struct.unpack('<%dI'%(len(data)//4),data)
def main():
 assert not E.exists() and not R.exists();E.mkdir();R.mkdir()
 qualification=M/'reports/partial_hw_20261024_r1/CSIM_QUALIFICATION.json';q=json.loads(qualification.read_text())
 assert q['state']=='PASS_FULL_CSIM_ARRAYS'
 sources={};refs={}
 for case,label in [('old_chinese','A0'),('old_english','B0'),('zero_hidden','all_ties')]:
  values={}
  for part in ['meta','dims','preview','keys','ids','raw','expected']:
   p=F/(case+'.'+part+'.bin');data=p.read_bytes();sources[str(p.relative_to(ROOT)).replace('\\','/')]=sha(p);values[part]=data
  assert len(values['meta'])==1523*16
  dims=words(values['dims']);ids=words(values['ids']);expected=words(values['expected'])
  assert len(dims)==64 and len(set(dims))==64 and all(x<896 for x in dims)
  assert len(values['preview'])==len(values['keys'])==151936*4
  assert list(ids)==sorted(set(ids)) and 4096<=len(ids)<=4110 and all(x<151936 for x in ids)
  assert len(values['raw'])==len(ids)*4 and len(expected)>=3
  record=next(x for x in q['records'] if x['label']==label)
  assert list(expected[:3])==[record['token'],record['score_bits'],record['crc']] and len(ids)==record['k']
  assembled=struct.pack('<4I',*expected[:3],len(ids))+b''.join(values[n] for n in ['dims','preview','keys','ids','raw'])
  assert hashlib.sha256(assembled).hexdigest()==record['actual_sha256'],case
  refs[case]={'expected_status':0,'token':expected[0],'score_bits':expected[1],'crc':expected[2],'k':len(ids),'debug1_assembled_sha256':record['actual_sha256'],'meta_sha256':sha(F/(case+'.meta.bin'))}
 valid=[('A0_debug','old_chinese',1),('B0_production','old_english',0),('A1_debug','old_chinese',1),('Z0_ties','zero_hidden',1)]
 scenarios=[]
 for label,case,debug in valid:
  scenarios.append(dict(label=label,fixture=case,debug=debug,capacity=79068,expected=refs[case],mutations=[]))
 for label,debug,capacity,offset,width,bits in [
  ('E_capacity',1,79067,None,None,None),('E_flag',2,79068,None,None,None),
  ('E_hidden_nan',1,79068,0,2,0x7fc0),('E_rms_nan',1,79068,1792,4,0x7fc00000),('E_rms_negative',1,79068,1792,4,0xbf800000)]:
  mutations=[] if offset is None else [dict(region='meta',offset_bytes=offset,width_bytes=width,expected_original_hex=(F/'old_chinese.meta.bin').read_bytes()[offset:offset+width].hex(),replacement_hex=bits.to_bytes(width,'little').hex())]
  scenarios.append(dict(label=label,fixture='old_chinese',debug=debug,capacity=capacity,expected=dict(expected_status=1 if offset is None else 2,token=0,score_bits=0,crc=0,k=0,preview_read_beats=0),mutations=mutations,
   access_invariants=dict(weight_reads=0,meta_reads=0 if offset is None else 'metadata only; no fixed-count assumption',workspace_writes=0)))
 # This error requires a genuine full preview traversal; it is not a shortened case.
 dim0=words((F/'old_chinese.dims.bin').read_bytes())[0];address=dim0*128*16
 tiled=M/'reports/layout_topk_20261024_r1/assets/tiled_W_B1024.bin'
 with tiled.open('rb') as h:h.seek(address);original=h.read(2)
 scenarios.append(dict(label='E_preview_nan',fixture='old_chinese',debug=1,capacity=79068,expected=dict(expected_status=2,token=0,score_bits=0,crc=0,k=0,preview_read_beats=0),
  mutations=[dict(region='weights',offset_bytes=address,width_bytes=2,expected_original_hex=original.hex(),replacement_hex='c07f',restore_after=True)],
  access_invariants=dict(canonical_weight_reads=0,notes='Actual preview must encounter selected-channel NaN; do not replace with a fake error or precomputed preview')))
 scenarios.append(dict(label='A2_after_errors',fixture='old_chinese',debug=1,capacity=79068,expected=refs['old_chinese'],mutations=[]))
 cases=E/'cases';cases.mkdir()
 for i,s in enumerate(scenarios):
  data=bytearray((F/(s['fixture']+'.meta.bin')).read_bytes())
  for mutation in s['mutations']:
   if mutation['region']=='meta':
    a=mutation['offset_bytes'];n=mutation['width_bytes'];assert data[a:a+n].hex()==mutation['expected_original_hex'];data[a:a+n]=bytes.fromhex(mutation['replacement_hex'])
  path=cases/('%02d_%s.meta.bin'%(i,s['label']));path.write_bytes(data);s['case_index']=i;s['input_path']=str(path.relative_to(ROOT)).replace('\\','/');s['input_sha256']=sha(path)
 assert scenarios[0]['input_sha256']==scenarios[2]['input_sha256']==scenarios[-1]['input_sha256']
 assert scenarios[0]['input_sha256']!=scenarios[1]['input_sha256']!=scenarios[3]['input_sha256']
 (E/'scenarios.json').write_text(json.dumps(scenarios,indent=2)+'\n')
 weight_plan=M/'reports/d64_full_input_preflight_20261102_r2/PLAN.json';weight_assets={}
 for n,h in json.loads(weight_plan.read_text())['weight_sha256'].items():
  p=ROOT/n;assert sha(p)==h;weight_assets[n]={'sha256':h,'bytes':p.stat().st_size}
 manifest=dict(state='PREPARED_AND_SOURCE_REFERENCE_BOUND_NOT_SIMULATED',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scenarios=scenarios,source_sha256=sources,reference_qualification_sha256=sha(qualification),weight_assets=weight_assets,weight_plan_sha256=sha(weight_plan),
  architecture=dict(H=896,V=151936,d=64,T=4096,B=1024,weight_bytes=545685504,tiled_bytes=273416192,canonical_bytes=272269312,meta_bytes=24368,workspace_beats=79068,logical_meta_bytes=1289456,with_one_end_guard_bytes=1289472),
  execution_contract=['One persistent RTL DUT; no reset between scenarios','Reuse one unchanged loaded weight image, restoring only explicit NaN injection','Overwrite only metadata between calls; workspace persists to expose stale state','Debug0 must write no raw-score region and leave previous raw bytes unchanged','Compare every defined output/preview/key/dim/ID; compare complete raw array for debug1','A0/A1/A2 full arrays/token/score/CRC bit-identical; B and zero/ties checked independently','Each successful call must really traverse preview and exact weights; do not accept cached outputs','Retain extra end guard and check actual AXI bounds','Normal-response model must have a separate explicit identity; it cannot replace current strong-stress full gate'],
  required_before_execution='Current memory_repaired_full_20261103_r1 independent full numeric/FIFO PASS, then qualify any new response model before use',
  timing_scope='Preparatory inputs only. No RTL/native-model execution or performance numbers exist for this suite.',board='NOT_RUN',eda='NOT_RUN',automatic_next_stage=False)
 (R/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
 (R/'RESUME.md').write_text('Prepared inputs only; no EDA started. See MANIFEST.json and ../../experiments/'+NAME+'/scenarios.json. Current strong-stress full RTL keeps running unchanged. Do not launch this suite until that gate has passed and a separate response-model qualification is complete.\n')
 print(json.dumps(dict(state=manifest['state'],cases=len(scenarios),historical_csim_references_reassembled=3,aba_metadata_identical=True,eda='NOT_RUN',manifest=str(R/'MANIFEST.json')),indent=2))
if __name__=='__main__':main()
