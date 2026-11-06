"""Only local generated2026 core_revision overflow, never a general export bypass."""
from pathlib import Path
import hashlib,json,re,time,argparse
M=Path(__file__).resolve().parents[1];R=M/'reports/fusion_exp10_20261023_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--log',default='export_existing_r1.log');args=parser.parse_args();log=(R/args.log).read_text(encoding='utf-8-sig');assert 'core_revision' in log and any(message in log.lower() for message in ['bad lexical cast','invalid argument','out of range'])
    p=M.parent/'.cache/e10/hls/solution1/impl/ip/run_ippack.tcl';s=p.read_text();match=re.search(r'^set Revision\s+"([0-9]+)"\r?$',s,re.M);assert match and int(match[1])>2147483647
    before=p.with_suffix('.original.tcl');assert not before.exists();before.write_bytes(p.read_bytes());revision=int(time.time());assert 0<revision<=2147483647;s=s[:match.start()]+f'set Revision "{revision}"'+s[match.end():];p.write_text(s)
    (R/'LOCAL_IP_REVISION_REPAIR.json').write_text(json.dumps(dict(state='APPLIED_GENERATED_METADATA_ONLY',original_revision=match[1],replacement_revision=revision,original_sha256=sha(before),patched_sha256=sha(p),scope='No numerical source, clock, installation, test labels or synthesized DUT changes',board='NOT_RUN'),indent=2)+'\n');print('LOCAL_SIGNED_REVISION_REPAIR_APPLIED')
if __name__=='__main__':main()
