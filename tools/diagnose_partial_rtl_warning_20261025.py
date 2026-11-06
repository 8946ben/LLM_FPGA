"""Read-only inspection of the existing CoSim; no signaling or new EDA."""
from pathlib import Path
import datetime,hashlib,json,re,tarfile
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
R=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261024_r1/full_r3';S=ROOT/'.cache/p64_rtl_full_r3/hls/solution1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    out=R/'diagnostics/20261025_dsp_r1';assert not out.exists();out.mkdir(parents=True)
    work=json.loads((R/'FULL_WORKFLOW.json').read_text());data=(R/'cosim.log').read_bytes();text=data.decode(errors='replace')
    warnings=list(re.finditer(r'Warning: OPMODE Input Warning[^\n]*\nTime:\s*(\d+)\s*ps[^\n]*Process:\s*(\S+)[^\n]*',text))
    severe=[line for line in text.splitlines() if re.search(r'UVM_ERROR|UVM_FATAL|ERROR:|CSIM_FAIL|[Dd]eadlock detected',line)]
    scopes={name:sum(name in m.group(0) for m in warnings) for name in ['dot_product_rows','reduce_rows']}
    progress=re.findall(r'RTL Simulation\s*:\s*(\d+)\s*/\s*(\d+)\s*\[([\d.]+)%\]\s*@\s*"(\d+)"',text)
    returned={p.name:p.stat().st_size for p in (S/'sim/tv/rtldatafile').glob('*') if p.is_file()}
    source=Path('/tools/Xilinx/Vivado/2022.2/data/vhdl/src/unisims/primitive/DSP48E1.vhd');lines=source.read_text().splitlines()
    excerpt='\n'.join(f'{i+1}: {lines[i]}' for a,b in [(1866,1890),(3437,3478)] for i in range(a,b))+'\n'
    (out/'DSP48E1_warning_excerpt.txt').write_text(excerpt)
    (out/'warning_samples.log').write_text('\n'.join(m.group(0) for m in warnings[:4]+warnings[-4:])+'\n')
    (out/'workflow_snapshot.json').write_bytes((R/'FULL_WORKFLOW.json').read_bytes())
    reuse=json.loads((R/'SYNTHESIS_REUSE.json').read_text())
    for n,h in reuse['files'].items():assert sha(Path(reuse['original'])/n)==h,n
    now=datetime.datetime.now(datetime.timezone.utc)
    report=dict(state='RUNNING_WITH_DSP_WARNINGS_UNRESOLVED',observed_at_china=now.astimezone(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
        workflow_state=work['state'],active_lock=(R/'ACTIVE.lock').exists(),log_bytes=len(data),log_snapshot_sha256=hashlib.sha256(data).hexdigest(),
        completed_transactions=int(progress[-1][0]) if progress else None,total_transactions=int(progress[-1][1]) if progress else None,
        last_periodic_sim_time_ms=int(progress[-1][3])/1e9 if progress else None,
        opmode_warning_count=text.count('Warning: OPMODE Input Warning'),parsed_warning_count=len(warnings),
        first_warning_sim_time_ms=int(warnings[0].group(1))/1e9 if warnings else None,last_warning_sim_time_ms=int(warnings[-1].group(1))/1e9 if warnings else None,
        warning_scope_counts=scopes,severe_error_lines=severe[:20],severe_error_line_count=len(severe),returned_file_bytes=returned,
        interpretation='Warnings appear on candidate exact dot-product and reduction paths; this is more activity evidence than clock advancement, but not valid-data or correctness proof.',
        primitive_warning='Invalid OPMODE/CARRYINSEL case sets output_x_sig and emits severity Warning. Whether it overlaps an accepted valid result is unverified.',
        verdict='Cannot certify normal operation or harmless warnings; no final arrays/FIFO report/PASS yet. Preserve all warnings and test conditions.',
        primitive_sha256=sha(source),frozen_synthesis_files_verified=len(reuse['files']),observer_sha256=sha(Path(__file__)),board='NOT_RUN',automatic_next_stage=False)
    (out/'WARNING_DIAGNOSIS.json').write_text(json.dumps(report,indent=2)+'\n')
    archive=ROOT/'full_rtl_dsp_diagnostic_20261025_r1.tar.gz'
    with tarfile.open(archive,'w:gz') as tar:
        for p in out.iterdir():tar.add(p,arcname=str(p.relative_to(ROOT)))
    print(json.dumps(dict(state=report['state'],warning_count=report['opmode_warning_count'],last_warning_ms=report['last_warning_sim_time_ms'],severe_errors=report['severe_error_line_count'],archive_sha256=sha(archive),bytes=archive.stat().st_size)))
if __name__=='__main__':main()
