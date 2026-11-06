"""Counterfactual reconstruction of every original full-CoSim preview bit."""
from pathlib import Path
import json,hashlib,re
import numpy as np
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4'
R=M/'reports/partial_rtl_20261026_diagnosis_r1';F=M/'experiments/partial_hw_20261024/fixtures'
FULL=M/'reports/partial_rtl_20261024_r1/full_r3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 t=np.memmap(M/'reports/layout_topk_20261024_r1/assets/tiled_W_B1024.bin','<u2',mode='r')
 c=np.memmap(ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin','<u2',mode='r')
 boundary=1<<29;overlap=t.nbytes+c.nbytes-boundary
 assert overlap==8814592 and overlap%(1024*2)==0
 prefix=t[:5*896*1024].copy();prefix[:overlap//2]=c[-overlap//2:]
 dims=np.fromfile(F/'old_chinese.dims.bin','<u4')
 h=(np.fromfile(F/'old_chinese.meta.bin','<u2')[:896].astype('u4')<<16).view('f4')
 actual=np.fromfile(FULL/'RTL_RETURNED_WORKSPACE.u32.bin','<u4')[37984*4:37984*4+151936]
 expected=np.fromfile(F/'old_chinese.preview.bin','<u4');reconstructed=[]
 for tile in range(149):
  weights=(prefix[tile*896*1024:(tile+1)*896*1024] if tile<5 else t[tile*896*1024:(tile+1)*896*1024]).reshape(896,1024)
  data=(weights[dims,:].T.astype('u4')<<16).view('f4')
  p=np.multiply(data,h[dims],dtype='f4')
  while p.shape[1]>1:p=np.add(p[:,::2],p[:,1::2],dtype='f4')
  reconstructed.extend(p[:,0].view('u4')[:min(1024,151936-tile*1024)])
 reconstructed=np.array(reconstructed,dtype='<u4')
 assert np.array_equal(actual,reconstructed)
 assert np.count_nonzero(actual!=expected)==5120
 reconstructed.tofile(R/'RECONSTRUCTED_ALIASED_PREVIEW.u32.bin')
 trace=json.loads((R/'r6/AXI_TRACE_REVIEW.json').read_text());assert trace['read_beats']==8192 and trace['input_mismatches']==0
 writes=[w for w in trace['last_writes'] if w['address']==(1523+37984)*16];assert len(writes)==1
 first=np.array([(int(writes[0]['data'],16)>>(32*j))&0xffffffff for j in range(4)],dtype='<u4')
 assert np.array_equal(first,expected[:4]) and not np.array_equal(first,actual[:4])
 alias_log=(R/'alias_minimal/r2.log').read_text()
 assert 'BEFORE low=12 high=12' in alias_log and 'AFTER low=34 high=34' in alias_log
 assert 'XSIM_DYNAMIC_BYTE_ARRAY_ALIAS_512M_REPRODUCED' in alias_log
 process=json.loads((R/'PROCESS_AFTER.json').read_text());assert process['owned_process_group_members']==[] and not process['active_locks']
 proof=dict(state='CONFIRMED_XSIM_2022_2_DYNAMIC_BYTE_ARRAY_ALIAS_ROOT_CAUSE',
  cause='Generated CoSim byte-array memory aliases addresses separated by 2^29 bytes in this XSIM 2022.2 installation; canonical tail overwrites tiled prefix',
  simulator='Vivado XSIM 2022.2 SW Build 3671981',
  model_source='file_agent/mem_model.sv: logic[WIDTH-1:0] mem[]; reference model instantiates byte memory for weights',
  tiled_bytes=t.nbytes,canonical_bytes=c.nbytes,combined_bytes=t.nbytes+c.nbytes,combined_mib=(t.nbytes+c.nbytes)/(1<<20),
  alias_period_bytes=boundary,overwritten_tiled_prefix_bytes=overlap,
  overwritten_complete_tiles=4,overwritten_channels_in_tile4=720,
  selected_channels_affected_in_tile4=int(np.count_nonzero(dims<720)),
  all_preview_values_compared=151936,aliased_reconstruction_mismatches=0,
  original_reference_mismatches=5120,reconstructed_sha256=sha(R/'RECONSTRUCTED_ALIASED_PREVIEW.u32.bin'),
  minimal_simulation=dict(low_address='0x1200',high_address='0x20001200',before_low='0x12',before_high='0x12',after_low='0x34',after_high='0x34',source_sha256=sha(R/'alias_minimal/alias_diag.sv'),log_sha256=sha(R/'alias_minimal/r2.log')),
  finite_prefix_control=dict(original_rtl_reused=True,original_stalls_reused=True,first_tile_read_beats=8192,axi_read_data_mismatches=0,ar_bursts=64,first_four_preview_bits_match_reference=True,original_failure_first_four_bits_reproduced=False,
    note='Prefix input intentionally avoids aliasing; it is a causal control, not reproduction or full RTL qualification'),
  downstream_review_sha256=sha(R/'STAGE_CHAIN_REVIEW.json'),process_after_sha256=sha(R/'PROCESS_AFTER.json'),
  original_full_cosim_status='FAIL_PRESERVED; caused by corrupted simulated input; no passing qualification issued',
  design_source_changed=False,parameters_changed=False,board='NOT_RUN',automatic_next_stage=False,
  next_step='Isolate a banked CoSim memory model with small per-bank arrays; validate boundary non-aliasing and preview blocks before a complete qualification; do not change HLS numeric logic')
 (R/'ROOT_CAUSE_REVIEW.json').write_text(json.dumps(proof,indent=2)+'\n')
 print(json.dumps(proof,indent=2))
if __name__=='__main__':main()
