"""Control-test original generated C postchecker; no RTL or FPGA execution."""
from pathlib import Path
import shutil,subprocess,json,hashlib,datetime,os,struct
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
OLD=ROOT/'.cache/p64_rtl_full_r3/hls/solution1/sim'
B=ROOT/'.cache/p64_postcheck_control_20261026_r1';R=ROOT/'module_14_lm_head_v4/reports/postcheck_control_20261026_r1'
assert not B.exists();B.mkdir();R.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
(B/'sim/wrapc_pc').mkdir(parents=True);(B/'sim/tv/rtldatafile').mkdir(parents=True)
shutil.copy2(OLD/'wrapc_pc/cosim.pc.exe',B/'sim/wrapc_pc/cosim.pc.exe')
fixture=ROOT/'module_14_lm_head_v4/experiments/partial_rtl_20261024/full_fixtures_r3'
F=B/'fixtures';F.mkdir()
for p in fixture.iterdir():
 if p.is_file() and (p.name.startswith('old_chinese.') or p.name=='weight_paths.txt'):shutil.copy2(p,F/p.name)
for p in (OLD/'tv/cdatafile').glob('*autotvout*.dat'):
 shutil.copy2(p,B/'sim/tv/rtldatafile'/p.name.replace('c.','rtl.',1))
state=dict(started=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='C-reference TV used as parser control, never RTL evidence',postchecker_sha256=sha(B/'sim/wrapc_pc/cosim.pc.exe'),automatic_next_stage=False)
(R/'WORKFLOW.json').write_text(json.dumps(state,indent=2)+'\n')
def run(label):
 cmd=['bash','-c','source /tools/Xilinx/Vitis/2022.2/settings64.sh >/dev/null 2>&1; exec ./cosim.pc.exe "$1"','postcheck',str(F)]
 with (R/(label+'.log')).open('w') as out:
  p=subprocess.run(cmd,cwd=B/'sim/wrapc_pc',stdout=out,stderr=subprocess.STDOUT,timeout=180)
 return p.returncode
positive=run('positive')
actual=F/'actual_RTL_full_chinese.bin'
assert positive==0 and actual.exists()
expected=(F/'old_chinese.expected.bin').read_bytes();assert len(expected)==12
expected+=struct.pack('<I',(F/'old_chinese.ids.bin').stat().st_size//4)
for extension in ['dims','preview','keys','ids','raw']:expected+=(F/('old_chinese.'+extension+'.bin')).read_bytes()
assert actual.read_bytes()==expected
shutil.copy2(actual,R/'POSITIVE_C_REFERENCE_ONLY.bin');actual.rename(F/'C_REFERENCE_ONLY_positive.bin')
meta=B/'sim/tv/rtldatafile/rtl.lm_head_v4_partial_proto.autotvout_meta.dat'
before=sha(meta);lines=meta.read_text().splitlines();indices=[i for i,x in enumerate(lines) if x.startswith('0x')]
assert len(indices)==80591
index=indices[1523+37984];original=lines[index];lines[index]='0x{:032x}'.format(int(original,16)^1)
meta.write_text('\n'.join(lines)+'\n')
negative=run('negative_preview_bit')
assert negative!=0 and not actual.exists()
assert 'CSIM_FAIL full preview bits RTL_full_chinese' in (R/'negative_preview_bit.log').read_text()
result=dict(state='PASS_ORIGINAL_POSTCHECK_POSITIVE_AND_NEGATIVE_CONTROLS',positive_return=positive,negative_return=negative,
 positive_equals_frozen_fixture_arrays=True,negative_has_no_new_actual_file=True,negative_mutation='one low bit of first preview raw, scalars unchanged',
 original_meta_sha256=before,mutated_meta_sha256=sha(meta),postchecker_sha256=state['postchecker_sha256'],
 frozen_fixture_array_sha256=hashlib.sha256(expected).hexdigest(),positive_reference_only_sha256=sha(R/'POSITIVE_C_REFERENCE_ONLY.bin'),
 actual_rtl_test=False,automatic_next_stage=False,finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
(R/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
