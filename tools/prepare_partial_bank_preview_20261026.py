"""Freeze finite five-block RTL observation, original full TV and banked model."""
from pathlib import Path
import json,hashlib,tarfile
import numpy as np
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4'
E=M/'experiments/sim_memory_bank_20261026';R=M/'reports/sim_memory_bank_20261026_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert json.loads((R/'UNIT_REVIEW.json').read_text())['state']=='PASS_INDEPENDENT_MEMORY_EVENT_REPLAY'
 assert not (R/'PREVIEW_PLAN.json').exists()
 t=np.memmap(M/'reports/layout_topk_20261024_r1/assets/tiled_W_B1024.bin','u1',mode='r')
 c=np.memmap(ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin','u1',mode='r')
 n=len(t)+len(c);addresses=set()
 for p in range(0,n,1048576):addresses.update([p,min(p+1048575,n-1)])
 for base in [0,len(t),1<<29,n-1,8814592,5*896*1024*2]:
  addresses.update(a for a in range(base-32,base+33) if 0<=a<n)
 # Include complete first/last records and both sides of every real tiled block boundary.
 for tile in range(7):addresses.update(a for a in range(tile*896*1024*2-16,tile*896*1024*2+16) if 0<=a<n)
 checks=[dict(address=a,value=int(t[a]) if a<len(t) else int(c[a-len(t)])) for a in sorted(addresses)]
 (E/'sentinels.json').write_text(json.dumps(checks,indent=2)+'\n')
 lines=['begin : bank_load_preflight','logic [7:0] got;','int err, fd;','fd=$fopen("weights_readback.csv","w");','if(fd==0) `uvm_fatal("bank_preflight","readback file")']
 for item in checks:
  a,v=item['address'],item['value']
  lines.extend([f'err=mem_blk_pages_weights.pages[0].read_one_elem(got,64\'d{a});',
                f'$fwrite(fd,"{a},%02h,%0d\\n",got,err);',
                f'if(err || got !== 8\'h{v:02x}) `uvm_fatal("bank_preflight","byte mismatch at {a}")'])
 lines.extend(['$fclose(fd);',f'$display("BANK_FULL_INPUT_SENTINEL_PASS checked={len(checks)}");','end'])
 (E/'weights_preflight.svh').write_text('\n'.join(lines)+'\n')
 tcl='''open_vcd preview5.vcd
set top /apatb_lm_head_v4_partial_proto_top
log_vcd [get_objects $top/ap_clk]
foreach port {weights_ARVALID weights_ARREADY weights_ARADDR weights_ARLEN weights_RVALID weights_RREADY weights_RDATA weights_RLAST meta_AWVALID meta_AWREADY meta_AWADDR meta_AWLEN meta_WVALID meta_WREADY meta_WDATA meta_WSTRB meta_WLAST} {
 log_vcd [get_objects $top/$port]
}
add_condition -radix unsigned -name stop_after_five_blocks -notrace {/apatb_lm_head_v4_partial_proto_top/weights_ARVALID == 1} {
 set addr [get_value -radix unsigned /apatb_lm_head_v4_partial_proto_top/weights_ARADDR]
 if {$addr >= 9175040} {puts "BANK_PREVIEW5_STOP [current_time]"; stop}
}
run 15 ms
close_vcd
puts "BANK_PREVIEW5_RETURN [current_time]"
quit
'''
 (E/'preview5.tcl').write_text(tcl)
 plan=dict(state='FROZEN_FIVE_BLOCK_BANKED_MEMORY_RTL_ENTRY',unit_review_sha256=sha(R/'UNIT_REVIEW.json'),
  original_full_cosim='partial_rtl_20261024_r1/full_r3 (FAIL preserved)',
  input='Original full34105344-record weights TV, no prefix truncation; stream reconstructed tiled/canonical SHA must match before xsim',
  memory_readback=dict(kind='sentinels, not full model SHA',bytes=len(checks),coverage='Every small-bank endpoint and 512MiB/bundle/overwrite/tile/end boundaries'),
  rtl='All DUT/generated RTL and adapters byte-identical; only simulator memory and readback preflight change',
  stalls='Original generated random_stall callbacks unchanged; no latency/clock/FIFO changes',
  stop='Before first AR beyond tiled block4; independent VCD must contain all5120 raw/key values and40960 reads',
  max_simulation_ms=15,wall_timeout_seconds=7200,full_configuration_qualification=False,automatic_next_stage=False,board='NOT_RUN',
  source_sha256={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in [E/'mem_model.sv',E/'sentinels.json',E/'weights_preflight.svh',E/'preview5.tcl']})
 (R/'PREVIEW_PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
 archive=R/'preview_entry.tar.gz'
 with tarfile.open(archive,'w:gz') as t:
  for p in [E/'sentinels.json',E/'weights_preflight.svh',E/'preview5.tcl',R/'PREVIEW_PLAN.json',R/'UNIT_REVIEW.json']:t.add(p,arcname=str(p.relative_to(ROOT)))
 print(json.dumps(dict(state=plan['state'],sentinels=len(checks),archive=str(archive),sha256=sha(archive))))
if __name__=='__main__':main()
