"""Read the existing CoSim only; no launch, signaling, or simulation changes."""
from pathlib import Path
import datetime,hashlib,json,os,re,tarfile
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
R=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261024_r1/full_r3'
S=ROOT/'.cache/p64_rtl_full_r3/hls/solution1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def statfields(s):return s[s.rindex(')')+2:].split()
def main():
    obs=R/'observations/20261025_r3';assert not obs.exists();obs.mkdir(parents=True)
    work=json.loads((R/'FULL_WORKFLOW.json').read_text());log=(R/'cosim.log').read_bytes()
    (obs/'cosim_snapshot.log').write_bytes(log);(obs/'workflow_snapshot.json').write_bytes((R/'FULL_WORKFLOW.json').read_bytes())
    progress=re.findall(r'RTL Simulation\s*:\s*(\d+)\s*/\s*(\d+)\s*\[([\d.]+)%\]\s*@\s*"(\d+)"',log.decode(errors='replace'))
    last=progress[-1] if progress else None
    started=datetime.datetime.fromisoformat(work['started']);now=datetime.datetime.now(datetime.timezone.utc)
    parent=Path('/proc')/str(work['parent_pid']);parent_birth_matches=False
    if parent.exists():parent_birth_matches=statfields((parent/'stat').read_text())[19]==statfields(work['parent_proc_stat'])[19]
    owned=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            fields=statfields((p/'stat').read_text())
            if int(fields[2])==work['child_pgid'] and fields[0]!='Z':
                owned.append(dict(pid=int(p.name),cpu_ticks=int(fields[11])+int(fields[12]),rss_bytes=int(fields[21])*os.sysconf('SC_PAGE_SIZE'),cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
        except (OSError,ValueError):pass
    files=['sim/verilog/lm_head_v4_partial_proto_subsystem/lm_head_v4_partial_proto_env.sv','sim/verilog/axivip/axi_slave_seq_lib.sv','sim/verilog/axivip/axi_cfg.sv','sim/verilog/axivip/axi_type.sv','sim/verilog/svtb/lm_head_v4_partial_proto_subsys_test_sequence_lib.sv']
    model={}
    for name in files:
        p=S/name;q=obs/Path(name).name;q.write_bytes(p.read_bytes());model[name]=sha(p)
    env=(S/files[0]).read_text();assert env.count('delay inside {[0:256]}')>=10
    slave=(S/files[1]).read_text();assert 'cfg.clatency.get_rdata_lat()' in slave
    cfg=(S/files[2]).read_text();assert 'read_latency_mode= CHANNEL_FIRST' in cfg
    # NO_DELAY in the old sequence field does not bypass the overridden clatency callbacks.
    reuse=json.loads((R/'SYNTHESIS_REUSE.json').read_text())
    for name,h in reuse['files'].items():assert sha(Path(reuse['original'])/name)==h,name
    snapshot=dict(state='OBSERVED_EXISTING_COSIM_NO_RESTART',workflow_state=work['state'],observed_at_utc=now.isoformat(),observed_at_china=now.astimezone(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
        workflow_elapsed_wall_seconds=(now-started).total_seconds(),parent_birth_matches=parent_birth_matches,active_lock=(R/'ACTIVE.lock').exists(),owned_processes=owned,
        last_progress=None if not last else dict(completed_transactions=int(last[0]),total_transactions=int(last[1]),latency_vs_estimate_percent=float(last[2]),simulation_time_ps=int(last[3]),simulation_time_ms=int(last[3])/1e9),
        pressure_model=dict(master_bundles=['meta','weights'],random_delay_min_cycles=0,random_delay_max_cycles=256,
            channels=['write_address','write_data','write_response','read_address','read_data'],read_write_latency_mode='CHANNEL_FIRST default, no generated override found',
            delay_distribution='0:=8, 0:=1, 256:=1, [0:256]:/2',active_callback='axi_slave_sequence -> cfg.clatency.get_*_lat -> overridden axi_latency_meta/weights',
            note='The obsolete sequence isusr_delay=NO_DELAY field does not disable these clatency callbacks. Actual stall totals await final monitor reports.'),
        frozen_synthesis_files_verified=len(reuse['files']),model_source_sha256=model,log_snapshot_sha256=sha(obs/'cosim_snapshot.log'),observer_sha256=sha(Path(__file__)),
        qualification='PENDING; no RTL PASS, final arrays or FIFO report yet',automatic_next_stage=False,board='NOT_RUN')
    (obs/'RUNTIME_SNAPSHOT.json').write_text(json.dumps(snapshot,indent=2)+'\n')
    archive=ROOT/'full_rtl_observation_20261025_r3.tar.gz'
    with tarfile.open(archive,'w:gz') as tar:
        for p in obs.iterdir():tar.add(p,arcname=str(p.relative_to(ROOT)))
    print(json.dumps(dict(state=snapshot['state'],progress=snapshot['last_progress'],wall_seconds=snapshot['workflow_elapsed_wall_seconds'],archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive))))
if __name__=='__main__':main()
