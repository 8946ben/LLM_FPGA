"""Audit raw D64A board readbacks. No board connection or fabricated AXI cycles."""
from pathlib import Path
import argparse,json,struct,hashlib,zlib,math
import numpy as np
REC=struct.Struct('<QQQ10I');META_BYTES=24368;LOGICAL_BYTES=1289472

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--dump',type=Path,required=True);ap.add_argument('--references',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args();d=args.dump;refs=args.references;assert not args.out.exists()
 config=json.loads((refs/'CONFIG.json').read_text());receipt=json.loads((d/'READBACK.json').read_text());assert receipt['state']=='RAW_READ_ONLY_RECEIPT_AWAITING_INDEPENDENT_AUDIT' and receipt['source_image_sha256']==config['image_sha256']
 for name,h in config['reference_sha256'].items():assert digest(refs/name)==h,name
 state=(d/'state_results.bin').read_bytes();assert len(state)==4096;header=struct.unpack_from('<32I',state);assert header[:6]==(0x52343644,1,3,0,12,4132) and header[9]==header[10]==1
 frequency=header[6]|header[7]<<32;assert frequency==config['timer_counts_per_second'] and frequency>0
 def record(data,offset,index,kind,expected):
  start,end,preview,idx,gotkind,rc,status,token,score,k,crc,valid,running=REC.unpack_from(data,offset)
  assert idx==index and gotkind==kind and not rc and not running and valid==63 and end>start
  assert [status,token,score,k,crc]==[expected[x] for x in ['status','token','score','k','crc']]
  if not status:assert preview==1220608 and zlib.crc32(struct.pack('<II',token,score))==crc
  return (end-start)*1000/frequency
 results=[];previous=None
 for i,s in enumerate(config['scenarios']):
  record(state,256+i*64,i,3,config['expected'][i]);before=np.fromfile(d/f'snapshot_{2*i:02}.bin',dtype='<u4');after=np.fromfile(d/f'snapshot_{2*i+1:02}.bin',dtype='<u4');assert len(before)==len(after)==LOGICAL_BYTES//4
  assert np.all(before[-4:]==0xa5a5a5a5) and np.all(after[-4:]==0xa5a5a5a5)
  assert before[:META_BYTES//4].tobytes()==after[:META_BYTES//4].tobytes()==(refs/f'input_{i:02}.bin').read_bytes()
  b=before[META_BYTES//4:-4];a=after[META_BYTES//4:-4]
  if previous is not None:assert np.array_equal(b,previous)
  previous=a.copy();expected=config['expected'][i];k=expected['k'];raw=slice(76997*4,79052*4)
  if expected['status']:
   assert np.array_equal(b[raw],a[raw])
   if i in [5,6,7,8,9]:assert np.array_equal(b,a)
   results.append(dict(case=i,scope='ERROR_SCALARS_AND_OBSERVABLE_WORKSPACE_EFFECTS_ONLY'));continue
  arrays={name:np.fromfile(refs/'arrays'/(s['fixture']+'.'+name+'.bin'),dtype='<u4') for name in ['dims','preview','keys','ids','raw']}
  slices=dict(dims=slice(79052*4,79052*4+64),preview=slice(37984*4,37984*4+151936),keys=slice(0,151936),ids=slice(75969*4,75969*4+k))
  mask=np.zeros(len(a),dtype=bool)
  for name,sl in slices.items():assert np.array_equal(a[sl],arrays[name]),(i,name);mask[sl]=True
  assert np.array_equal(a[75968*4:75969*4],np.array([0x4449344d,0x00040001,k,151936],dtype='<u4'));mask[75968*4:75969*4]=True
  ids_end=75969*4+((k+3)//4)*4;assert np.all(a[75969*4+k:ids_end]==0xffffffff);mask[75969*4+k:ids_end]=True
  if s['debug']:
   pairs=a[76997*4:76997*4+2*k].reshape(k,2);assert np.array_equal(pairs[:,0],arrays['ids']) and np.array_equal(pairs[:,1],arrays['raw'])
   end=76997*4+((k+1)//2)*4;mask[76997*4:end]=True
   if k&1:assert np.all(a[76997*4+2*k:end]==0)
   assembled=np.concatenate([np.array([expected[x] for x in ['token','score','crc','k']],dtype='<u4'),arrays['dims'],arrays['preview'],arrays['keys'],arrays['ids'],arrays['raw']]);assert hashlib.sha256(assembled.tobytes()).hexdigest()==s['expected']['debug1_assembled_sha256']
  else:assert np.array_equal(b[raw],a[raw])
  assert np.array_equal(b[~mask],a[~mask]),(i,'Unexpected workspace write')
  results.append(dict(case=i,scope='DEFINED_ARRAYS_BIT_EXACT_AND_UNTOUCHED_MEMORY_PRESERVED',debug=s['debug'],workspace_sha256=hashlib.sha256(a.tobytes()).hexdigest()))
 assert results[0]['workspace_sha256']==results[2]['workspace_sha256']==results[11]['workspace_sha256']
 data=(d/'timing_records.bin').read_bytes();assert len(data)==4132*64;timing=[]
 for category,label in enumerate(['chinese','english','code','math']):
  measured=[];stable=[]
  for j in range(1033):
   index=category*1033+j;kind=(category<<8)|(0 if j<3 else 1 if j<33 else 2);ms=record(data,index*64,index,kind,config['expected'][12+category])
   if 3<=j<33:measured.append(ms)
   if j>=33:stable.append(ms)
  median=float(np.median(measured));p95=sorted(measured)[math.ceil(.95*len(measured))-1]
  timing.append(dict(category=label,measured_calls=30,stable_calls=1000,median_ms=median,p95_ms=p95,m14_equivalent_outputs_per_second=1000/median))
 out=dict(state='PASS_OBSERVED_BOARD_PAYLOAD_AND_FIXED_INPUT_TIMING_ONLY',image_sha256=config['image_sha256'],cases=results,timing=timing,scope='Raw before/after arrays and returned records; no physical AXI trace/IP-cycle proof; READ_ONLY receipt does not prove fresh upload. Separate original loading ACK/target-CRC/sentinel evidence required.',full_llm_ttft='NOT_MEASURED',whole_llm_token_per_second='NOT_MEASURED')
 args.out.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
