"""Independentofflineasset/ABI audit. Neverconnectsboard orclaimsRTL/FPGApass."""
from pathlib import Path
import hashlib,json,zlib,struct,datetime
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/d64_board_20261105_r1';PS=M/'experiments/d64_board_20261105_r1/ps'
def digest_region(f,off,n):
 f.seek(off);h=hashlib.sha256();crc=0
 while n:
  data=f.read(min(n,1048576));assert data;n-=len(data);h.update(data);crc=zlib.crc32(data,crc)
 return h.hexdigest(),crc
layout=json.loads((PS/'layout.json').read_text());manifest=json.loads((R/'pl_image_r1/MANIFEST.json').read_text());image=R/'pl_image_r1/d64_pl_576m.bin'
assert image.stat().st_size==manifest['image_bytes']==layout['image_bytes']==576*1048576
assert manifest['layout_sha256']==hashlib.sha256((PS/'layout.json').read_bytes()).hexdigest()
regions={x['name']:x for x in layout['regions']};ordered=sorted(regions.values(),key=lambda x:x['offset'])
for i,x in enumerate(ordered):
 assert x['offset']%16==0 and x['bytes']%16==0 and x['offset']+x['bytes']<=layout['image_bytes']<=layout['physical_ddr_bytes']
 if i:assert ordered[i-1]['offset']+ordered[i-1]['bytes']<=x['offset']
audit={}
with image.open('rb') as f:
 h,crc=digest_region(f,0,image.stat().st_size);assert h==manifest['image_sha256'] and f'{crc:08x}'==manifest['image_crc32']
 for name in ['tiled_weight','canonical_weight']:
  region=regions[name];h,crc=digest_region(f,region['offset'],region['bytes']);ref=manifest['weight_sources'][name];assert h==ref['sha256'] and f'{crc:08x}'==ref['crc32'];audit[name]=dict(bytes=region['bytes'],sha256=h,crc32=f'{crc:08x}')
 assert audit['canonical_weight']['sha256']=='4e96b0df6d274768cbb7e72404011853d23349999b658dc2f4dfb3c431ea223f'
 assert len(manifest['fixtures'])==16
 for row in manifest['fixtures']:
  f.seek(regions['fixture_bank']['offset']+row['slot']*0x6000);data=f.read(24368);assert hashlib.sha256(data).hexdigest()==row['input_sha256'];assert data==(ROOT/row['input_path']).read_bytes()
 f.seek(regions['active_metadata']['offset']);assert f.read(24368)==(ROOT/manifest['fixtures'][0]['input_path']).read_bytes()
 f.seek(regions['workspace']['offset']);remaining=regions['workspace']['bytes']+16
 while remaining:
  n=min(remaining,1048576);assert f.read(n)==bytes([0xa5])*n;remaining-=n
 for name in ['snapshots','state_results','timing_records']:
  f.seek(regions[name]['offset']);remaining=regions[name]['bytes']
  while remaining:
   n=min(remaining,1048576);assert f.read(n)==bytes(n);remaining-=n
 f.seek(regions['input_contract']['offset']);contract=f.read(64);v=struct.unpack('<16I',contract);assert v[:12]==(0x43343644,1,0x4d344401,576*1048576,24368,79068,1289472,12,4,3,30,1000);assert zlib.crc32(contract[:56])==v[14] and contract.hex()==manifest['contract_hex']
# CrosschecktheCSRprofileagainstactualHLSexportedregistermetadata,notoldselectorABI.
export=json.loads((R/'EXPORT_INDEPENDENT_REVIEW.json').read_text());csr=layout['csr'];reg=export['registers']
for key,name in {'meta':'meta_offset_1','tiled_weight':'tiled_weight_1','canonical_weight':'canonical_weight_1','workspace':'workspace_1','capacity_beats':'capacity_beats','debug':'debug','status':'status','status_valid':'status_ctrl','token':'token','token_valid':'token_ctrl','score_bits':'score_bits','score_valid':'score_bits_ctrl','candidate_count':'candidate_count','candidate_valid':'candidate_count_ctrl','crc':'output_crc','crc_valid':'output_crc_ctrl','preview_read_beats':'preview_read_beats_1','preview_valid':'preview_read_beats_ctrl'}.items():assert csr[key]==reg[name]
proto=(M/'experiments/partial_hw_20261024/partial_proto.hpp').read_text()
for term in ['P_H=896','P_V=151936','P_D=64','P_T=4096','P_META_BEATS=1523','P_WS_BEATS=79068','P_SCORES=76997','P_DIMS=79052']:assert term in proto
host=json.loads((R/'host_ps_r2/RESULT.json').read_text());assert host['state']=='PASS_HOST_CONTROL_LOADER_ONLY'
for path,h in host['source_sha256'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h,path
result=dict(state='PASS_OFFLINE_IMAGE_ABI_AND_HOST_CONTROL_LOADER_ONLY',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),image_bytes=image.stat().st_size,image_sha256=manifest['image_sha256'],image_crc32=manifest['image_crc32'],weight_image_regions=audit,fixture_slots=16,full_persistent_state_scenarios_planned=12,performance_call_plan='4categories*(3warmup+30timed+1000stable)',csr_fields_matched_actual_export=len(csr),host_tests='15mockMMIO andprotocolCRC/bounds/read_only/partialACK',signature='0x4D344401',board='NOT_RUN',system_200mhz='BLOCKED_SYNTHESIS_LICENSE_NOT_ROUTED',bit_xsa_bsp_elf='NOT_GENERATED',rtl_full12='INCOMPLETE_USER_STOPPED',source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in PS.rglob('*') if p.is_file()})
(R/'OFFLINE_PREPARATION_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['state','image_bytes','image_sha256','fixture_slots','csr_fields_matched_actual_export','board','system_200mhz','bit_xsa_bsp_elf']},indent=2))
