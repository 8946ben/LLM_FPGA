"""Audit saved preparation outputs and refresh resumable status; file IO only."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,struct,sys,zlib
M=Path(__file__).resolve().parents[1];sys.path.insert(0,str(M/'standalone'))
from selector_ps_mailbox import prepare_request

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

now=datetime.now(timezone(timedelta(hours=8))).isoformat()
root=M/'reports/performance_cases_20261022';cases={}
for case in ['small','median','p95','max']:
    out=root/case;g=read(out/'GOLDEN_RESULT.json');meta=read(out/'arena/MANIFEST.json');pre=read(out/'arena/HOST_PREFLIGHT.json')
    assert pre['state']=='PASS_HOST_PREFLIGHT_TARGET_NOT_RUN'
    assert pre['image_sha256']==meta['image_digest']['sha256'] and pre['manifest_sha256']==sha(out/'arena/MANIFEST.json')
    for name,h in g['files'].items():assert sha(out/name)==h,name
    ids=[v[0] for v in struct.iter_unpack('<I',(out/'candidate_ids.u32.bin').read_bytes())]
    assert len(ids)==g['candidates'] and all(a<b for a,b in zip(ids,ids[1:]))
    records=(out/'candidate_records.bin').read_bytes();policy=list(struct.iter_unpack('<f',(out/'policy_scores.f32.bin').read_bytes()))
    assert [v[0] for v in struct.iter_unpack('<If',records)]==ids
    assert len(policy)==len(ids) and f'{zlib.crc32(records):08x}'==g['candidate_records_crc32']
    slot=min(range(len(ids)),key=lambda i:(-policy[i][0],ids[i]))
    bits=struct.unpack('<I',struct.pack('<f',policy[slot][0]))[0]
    expected=dict(token=ids[slot],score_bits=f'0x{bits:08x}',crc32=f'{zlib.crc32(struct.pack("<II",ids[slot],bits)):08x}')
    assert expected==g['expected']==meta['expected']==g['expected_dense']
    request=out/'arena/request.bin'
    with request.open('xb') as f:f.write(prepare_request(meta))
    cases[case]=dict(candidates=len(ids),records=len(records)//8,expected=expected,request_sha256=sha(request),preflight_sha256=sha(out/'arena/HOST_PREFLIGHT.json'))
save(root/'QUALIFICATION.json',dict(state='PASS_OFFLINE_GOLDENS_IMAGES_REQUESTS_NOT_TARGET',updated=now,cases=cases,hardware_access='NONE',
    scope='Saved output identity/sorted IDs/record CRC/policy tie-break/dense result and independent host image preflight; no new RTL or target calls',
    campaign_binding='NEW_K_CASE_CONTROLLER_BINDING_PENDING',requested_counts_not_executed=dict(warmup=3,timing=30,stability=1000)))
q=read(M/'reports/fixed_quality_20261022/RESULT.json')
assert q['state']=='PASS_PROPOSED_INDEPENDENT_POINT_RECALL_GATE'
p=read(M/'PROGRESS.json');p.update(updated=now,stage='P5_OFFLINE_PREPARATION_FRESH_QUALITY_POINT_GATE_PASS_BOARD_DEFERRED',
  active_work='NONE: GPU workflow exit0 and four CPU golden/image/preflight preparations complete; no EDA/board execution started',
  next='Offline new-K campaign binding and multi-step/debug/error-path preparation. User explicitly deferred board; no FPGA connection/probe/operation until new arrangement.')
p['milestones']['P4']='PASS_OFFLINE: repaired-wrapper full RTL,200MHz system, matching BSP/two ELFs/internal package; fresh fixed-arithmetic independent proposed point recall gate PASS. Target/release pending'
p['milestones']['P5']='DEFERRED_BY_USER: 暂不上板，继续离线准备; no target operations'
p['fresh_quality'].update(state=q['state'],result='reports/fixed_quality_20261022/RESULT.json',review='reports/fixed_quality_20261022/INDEPENDENT_REVIEW.json',
  decode_steps=14958,exclusions=0,misses={name:q[name]['decode']['misses'] for name in ['route','lowrank','hybrid']},candidate_decode=q['candidate_decode'],
  limitations='Frozen GPU arithmetic coverage model, not complete new RTL replay/free generation/lossless/board acceptance; exact dedup only')
p['performance_cases']=dict(state='PASS_OFFLINE_GOLDENS_IMAGES_REQUESTS_NOT_TARGET',report='reports/performance_cases_20261022/QUALIFICATION.json',candidates={c:v['candidates'] for c,v in cases.items()},campaign_binding='PENDING')
if 'integrated_selector' in p:
    p['integrated_selector'].update(rtl='PASS_OFFLINE_REPAIRED_WRAPPER_FULL_TRACE_AND_ORIGINAL_C_POSTCHECK; official wrapper failure retained',system='PASS_OFFLINE_SYSTEM200MHZ_AUDIT')
if 'rtl_observed_progress' in p:p['rtl_observed_progress']['interpretation']='HISTORICAL_ONLY_SUPERSEDED_BY_QUALIFIED_RTL_RESULT; no active simulator'
if 'local_offline_sequence' in p:p['local_offline_sequence'].update(state='HISTORICAL_STOPPED_DO_NOT_RESTART',pid=None,session=None)
for path in ['reports/fixed_quality_20261022/RESULT.json','reports/fixed_quality_20261022/INDEPENDENT_REVIEW.json','reports/performance_cases_20261022/QUALIFICATION.json']:
    if path not in p['evidence']:p['evidence'].append(path)
save(M/'PROGRESS.json',p)
a=read(M/'reports/PERFORMANCE_ASSESSMENT_20261022.json');a['updated']=now
a['quality']['independent_revised_quality']=q['state'];a['quality']['fresh_fixed_arithmetic']=dict(groups=1000,decode_steps=14958,
    methods={name:q[name]['decode'] for name in ['route','lowrank','hybrid']},candidate_decode=q['candidate_decode'],source='reports/fixed_quality_20261022/RESULT.json',
    limits='Proposed overall/category point threshold only; not full new RTL replay or lossless/free-generation/board acceptance')
a['performance_case_preparation']='reports/performance_cases_20261022/QUALIFICATION.json'
a['board_authorization']='DEFERRED_BY_USER_CONTINUE_OFFLINE'
save(M/'reports/PERFORMANCE_ASSESSMENT_20261022.json',a)
print('OFFLINE_K_CASE_QUALIFICATION=PASS; four goldens/images/requests, no target access')
