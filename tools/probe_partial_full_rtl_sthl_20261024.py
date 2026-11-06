from pathlib import Path
import json,os,datetime
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1');R=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261024_r1/full_r3'
w=json.loads((R/'FULL_WORKFLOW.json').read_text());result=dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),state=w['state'],readers=[])
for proc in Path('/proc').iterdir():
    if not proc.name.isdigit():continue
    try:
        s=(proc/'stat').read_text();r=s[s.rindex(')')+2:].split()
        if int(r[2])!=w['child_pgid'] or r[0]=='Z':continue
        for fd in (proc/'fd').iterdir():
            try:
                target=os.readlink(str(fd))
                if 'autotvin_weights.dat' in target:
                    result['readers'].append(dict(pid=int(proc.name),file=target,fdinfo=(proc/'fdinfo'/fd.name).read_text(),total_bytes=Path(target).stat().st_size,cpu_ticks=int(r[11])+int(r[12]),resident_pages=int(r[21])))
            except OSError:pass
    except (OSError,ValueError):pass
log=(R/'cosim.log').read_text(errors='replace');result['log_tail']=log.splitlines()[-5:]
print(json.dumps(result,indent=2))
