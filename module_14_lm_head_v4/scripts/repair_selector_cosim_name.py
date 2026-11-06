"""Rename only a generated simulation block that collides with a vendor task."""
from pathlib import Path
import hashlib,json,shutil
M=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=M/'build/selector_full_cosim_r2/hls/solution1/sim/verilog/AESL_axi_slave_control.v'
    before=p.read_bytes();needle=b'initial begin : read_token\n'
    if needle not in before:needle=b'initial begin : read_token\r\n'
    assert before.count(needle)==1 and b'task read_token;' in before
    backup=p.with_suffix('.original.v.txt');assert not backup.exists();backup.write_bytes(before)
    after=before.replace(needle,needle.replace(b': read_token',b': read_token_output_block'))
    p.write_bytes(after)
    # No synthesizable file or transaction is changed. Hash these for the audit.
    syn=M/'build/selector_full_cosim_r2/hls/solution1/syn/verilog'
    frozen=json.loads((M/'reports/SELECTOR_PRIVATE_IP_MANIFEST.json').read_text(encoding='utf-8'))
    for name,digest in frozen['source_sha256'].items():assert sha(M/name)==digest
    report=dict(state='GENERATED_TESTBENCH_NAME_REPAIRED_NOT_RTL_PASS',
      issue='HLS2021.1 creates initial block read_token for output token and helper task read_token in same module; XSim VRFC10-2934',
      repair='Only initial block label read_token -> read_token_output_block',
      scope='Simulation wrapper only; no task logic, signal, golden trace, HLS source or synthesized RTL edits',
      wrapper=str(p.relative_to(M)),before_sha256=hashlib.sha256(before).hexdigest(),after_sha256=sha(p),
      failed_log='reports/hls_selector_full_cosim_r2_20261021.log',
      generated_synth_rtl_sha256={str(q.relative_to(syn)):sha(q) for q in syn.rglob('*') if q.is_file()},
      frozen_ip_manifest_sha256=sha(M/'reports/SELECTOR_PRIVATE_IP_MANIFEST.json'),
      validation='Pending regenerated XSim elaboration + simulation + original C postcheck; original HLS wrapper failure remains FAIL')
    out=M/'reports/SELECTOR_COSIM_NAME_REPAIR.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('COSIM_NAME_REPAIR=APPLIED generated block label only; RTL validation still pending')
if __name__=='__main__':main()
