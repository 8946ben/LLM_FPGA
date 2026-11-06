"""Build offline d64 PL image;no network/EDA/board operations. Bounded1MiB IO."""
from pathlib import Path
import argparse,json,hashlib,zlib,struct,datetime
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';PS=M/'experiments/d64_board_20261105_r1/ps';R=M/'reports/d64_board_20261105_r1'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--build',action='store_true',required=True);ap.parse_args()
 layout=json.loads((PS/'layout.json').read_text());regions={x['name']:x for x in layout['regions']};out=R/'pl_image_r1';out.mkdir();image=out/'d64_pl_576m.bin'
 fixture_manifest=M/'reports/d64_state_fixtures_20261104_r2/MANIFEST.json';fm=json.loads(fixture_manifest.read_text());scenarios=fm['scenarios'];assert len(scenarios)==12
 fixtures=[]
 for s in scenarios:
  path=ROOT/s['input_path'];assert path.stat().st_size==24368 and sha(path)==s['input_sha256'];fixtures.append((path,s))
 froot=M/'experiments/partial_hw_20261024/fixtures'
 q=json.loads((M/'reports/partial_hw_20261024_r1/CSIM_QUALIFICATION.json').read_text());assert q['state']=='PASS_FULL_CSIM_ARRAYS'
 for case,label in [('old_chinese','A0'),('old_english','B0'),('old_code','old_code'),('old_math','old_math')]:
  rec=next(x for x in q['records'] if x['label']==label);path=froot/(case+'.meta.bin');expected=struct.unpack('<3I',(froot/(case+'.expected.bin')).read_bytes()[:12]);assert expected==(rec['token'],rec['score_bits'],rec['crc'])
  fixtures.append((path,dict(label='timing_'+case,debug=0,capacity=79068,expected=dict(expected_status=0,token=rec['token'],score_bits=rec['score_bits'],crc=rec['crc'],k=rec['k']),mutations=[],input_path=path.relative_to(ROOT).as_posix(),input_sha256=sha(path))))
 weights=json.loads((M/'reports/d64_full_input_preflight_20261102_r2/PLAN.json').read_text())['weight_sha256'];sources={};crcs=[]
 with image.open('xb') as target:
  target.truncate(layout['image_bytes'])
  for (name,expected),tag in zip(weights.items(),['tiled_weight','canonical_weight']):
   source=ROOT/name;size=source.stat().st_size;assert size==regions[tag]['bytes'];target.seek(regions[tag]['offset']);h=hashlib.sha256();crc=0
   with source.open('rb') as f:
    for data in iter(lambda:f.read(1048576),b''):target.write(data);h.update(data);crc=zlib.crc32(data,crc)
   assert h.hexdigest()==expected,(name,h.hexdigest());crcs.append(crc);sources[tag]=dict(path=name,bytes=size,sha256=expected,crc32=f'{crc:08x}',offset=regions[tag]['offset'])
  for i,(path,s) in enumerate(fixtures):target.seek(regions['fixture_bank']['offset']+i*0x6000);target.write(path.read_bytes())
  target.seek(regions['active_metadata']['offset']);target.write(fixtures[0][0].read_bytes())
  target.seek(regions['workspace']['offset']);left=regions['workspace']['bytes']+16
  while left:n=min(left,1048576);target.write(bytes([0xa5])*n);left-=n
  words=[0x43343644,1,0x4d344401,layout['image_bytes'],24368,79068,layout['snapshot_logical_bytes'],12,4,3,30,1000,*crcs,0,0];words[14]=zlib.crc32(struct.pack('<14I',*words[:14]));contract=struct.pack('<16I',*words);target.seek(regions['input_contract']['offset']);target.write(contract)
 chunks=[];digest=hashlib.sha256();crc=0
 with image.open('rb') as f:
  for i in range(layout['image_bytes']//1048576):
   data=f.read(1048576);assert len(data)==1048576;digest.update(data);crc=zlib.crc32(data,crc);chunks.append(dict(offset=i*1048576,bytes=len(data),crc32=f'{zlib.crc32(data):08x}'))
  assert not f.read(1)
 manifest=dict(state='OFFLINE_IMAGE_ONLY_NOT_LOADED_NOT_BOARD',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),image_bytes=layout['image_bytes'],physical_base=layout['physical_base'],layout_path=(PS/'layout.json').relative_to(ROOT).as_posix(),layout_sha256=sha(PS/'layout.json'),image_sha256=digest.hexdigest(),image_crc32=f'{crc:08x}',chunk_bytes=1048576,chunks=chunks,weight_sources=sources,contract_hex=contract.hex(),fixture_manifest_sha256=sha(fixture_manifest),fixtures=[dict(slot=i,**s) for i,(path,s) in enumerate(fixtures)],snapshot_contract='24before/after compact metadata+workspace+endguard images,12persistentDUT scenarios;no intercallreset;physicalAXI trace notprovided',limitations='No matchingbit/XSA/BSP/ELF yet;source andassets only;12RTL regression stoppedbyuser')
 (out/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
 h=['/*GeneratedfromfrozenfixtureandCsimreferences;notnewboardresults.*/','#include <stdint.h>','typedef struct {uint32_t debug,capacity,status,token,score,k,crc,mutation_offset,original,replacement;} d64_case;','static const d64_case d64_cases[16]={']
 for path,s in fixtures:
  ex=s['expected'];mu=next((x for x in s['mutations'] if x['region']=='weights'),None);h.append('{%du,%du,%du,%du,%du,%du,%du,%du,%du,%du},'%(s['debug'],s['capacity'],ex['expected_status'],ex['token'],ex['score_bits'],ex['k'],ex['crc'],mu['offset_bytes'] if mu else 0xffffffff,int.from_bytes(bytes.fromhex(mu['expected_original_hex']),'little') if mu else 0,int.from_bytes(bytes.fromhex(mu['replacement_hex']),'little') if mu else 0))
 h+=['};',f'#define D64_TILED_CRC UINT32_C(0x{crcs[0]:08x})',f'#define D64_CANONICAL_CRC UINT32_C(0x{crcs[1]:08x})'];(PS/'d64_cases.h').write_text('\n'.join(h)+'\n'+'static const uint32_t d64_meta_crc[16]={'+','.join('0x%08xu'%zlib.crc32(path.read_bytes()) for path,scenario in fixtures)+'};\n')
 print(json.dumps(dict(state=manifest['state'],image=str(image),sha256=manifest['image_sha256'],crc32=manifest['image_crc32'],fixtures=len(fixtures))))
if __name__=='__main__':main()
