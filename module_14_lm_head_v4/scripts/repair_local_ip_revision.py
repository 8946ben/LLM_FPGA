"""Repair only generated v4 run_ippack.tcl; no EDA installation/date edits."""
from pathlib import Path
import hashlib,json,re,time
M=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=(M/'build/candidate_csynth_r2/hls/solution1/impl/ip/run_ippack.tcl').resolve()
    assert p.is_relative_to((M/'build').resolve())
    backup=p.with_suffix('.original.tcl');record=M/'reports/LOCAL_IP_REVISION_REPAIR.json'
    if record.exists():
        d=json.loads(record.read_text());assert sha(p)==d['patched_sha256'];print('LOCAL_IP_REVISION_REPAIR=ALREADY_APPLIED');return
    source=p.read_text(encoding='utf-8');match=re.search(r'^set Revision\s+"([0-9]+)"\r?$',source,re.M)
    assert match and int(match.group(1))>2147483647
    revision=int(time.time());assert 0<revision<=2147483647
    patched=source[:match.start()]+f'set Revision "{revision}"'+source[match.end():]
    assert not backup.exists();backup.write_bytes(p.read_bytes());before=sha(p)
    p.write_text(patched,encoding='utf-8')
    record.write_text(json.dumps(dict(state='APPLIED',original_revision=match.group(1),replacement_revision=revision,
        original_sha256=before,patched_sha256=sha(p),scope='Generated local v4 IP revision metadata only; no kernel, EDA installation or system time change.'),indent=2)+'\n',encoding='utf-8')
    print('LOCAL_IP_REVISION_REPAIR=APPLIED')
if __name__=='__main__':main()
