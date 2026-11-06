"""Resume after wrapper-only expected-header size assertion; reuse positive run."""
from pathlib import Path
import json,hashlib,struct,shutil,subprocess,datetime
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
B=ROOT/'.cache/p64_postcheck_control_20261026_r1';F=B/'fixtures';R=ROOT/'module_14_lm_head_v4/reports/postcheck_control_20261026_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (R/'RESULT.json').exists()
assert 'PARTIAL_FULL_RTL_REFERENCE_PASS calls=1 full_arrays=1' in (R/'positive.log').read_text()
actual=F/'actual_RTL_full_chinese.bin';header=(F/'old_chinese.expected.bin').read_bytes()
assert len(header)==16 and struct.unpack('<4I',header)[3]==(F/'old_chinese.ids.bin').stat().st_size//4
expected=header
for ext in ['dims','preview','keys','ids','raw']:expected+=(F/('old_chinese.'+ext+'.bin')).read_bytes()
assert actual.read_bytes()==expected
(R/'PRESERVED_ENTRY_FAILURE.json').write_text(json.dumps(dict(scope='wrapper metadata assertion only after positive C control passed',expected_header_bytes=16,old_wrapper_assumed=12,positive_run_not_repeated=True),indent=2)+'\n')
shutil.copy2(actual,R/'POSITIVE_C_REFERENCE_ONLY.bin');actual.rename(F/'C_REFERENCE_ONLY_positive.bin')
meta=B/'sim/tv/rtldatafile/rtl.lm_head_v4_partial_proto.autotvout_meta.dat'
before=sha(meta);lines=meta.read_text().splitlines();indices=[i for i,x in enumerate(lines) if x.startswith('0x')];assert len(indices)==80591
idx=indices[1523+37984];lines[idx]='0x{:032x}'.format(int(lines[idx],16)^1);meta.write_text('\n'.join(lines)+'\n')
with (R/'negative_preview_bit.log').open('w') as out:
 p=subprocess.run(['bash','-c','source /tools/Xilinx/Vitis/2022.2/settings64.sh >/dev/null 2>&1; exec ./cosim.pc.exe "$1"','postcheck',str(F)],cwd=B/'sim/wrapc_pc',stdout=out,stderr=subprocess.STDOUT,timeout=180)
assert p.returncode!=0 and not actual.exists()
assert 'CSIM_FAIL full preview bits RTL_full_chinese' in (R/'negative_preview_bit.log').read_text()
result=dict(state='PASS_ORIGINAL_POSTCHECK_POSITIVE_AND_NEGATIVE_CONTROLS',positive_pass_marker=True,negative_return=p.returncode,
 positive_equals_frozen_fixture_arrays=True,negative_has_no_new_actual_file=True,negative_mutation='one first-preview raw low bit; scalars unchanged',
 original_meta_sha256=before,mutated_meta_sha256=sha(meta),postchecker_sha256=sha(B/'sim/wrapc_pc/cosim.pc.exe'),
 frozen_fixture_array_sha256=hashlib.sha256(expected).hexdigest(),positive_reference_only_sha256=sha(R/'POSITIVE_C_REFERENCE_ONLY.bin'),
 actual_rtl_test=False,automatic_next_stage=False,finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
(R/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
