"""Explicit source bundle for user-requested STHL migration, no secrets."""
from pathlib import Path
import hashlib,json,tarfile
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/partial_hw_20261024_r1';E=M/'experiments/partial_hw_20261024'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    p=R/'remote_bundle.tar.gz';assert not p.exists(),'Preserve previous bundle'
    plan=json.loads((R/'PLAN.json').read_text(encoding='utf-8'));exclude='module_14_lm_head_v4/reports/layout_topk_20261024_r1/assets/tiled_W_B1024.bin'
    files=[ROOT/x for x in plan['source_sha256'] if x!=exclude]+[R/'PLAN.json',E/'remote_run.py']
    for name,h in plan['source_sha256'].items():assert sha(ROOT/name)==h,name
    with tarfile.open(p,'w:gz',compresslevel=1) as tar:
        for file in files:tar.add(file,arcname=file.relative_to(ROOT).as_posix(),recursive=False)
    entry=dict(host='nvidia-Super-Server',ssh_user='zhangben',ssh_port=7626,
        remote_root='/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1',
        archive=p.name,archive_sha256=sha(p),bytes=p.stat().st_size,files=len(files),
        rebuild_exact_tiled_weight=exclude,expected_tiled_sha256=plan['source_sha256'][exclude],
        tool='Vitis_HLS2022.2 Linux; not same tool as local2021.1',
        authorization='User explicitly requested STHL for Vivado due local memory; isolated source transfer and sequential Csim/HLS only',
        source_sha256={str(x.relative_to(ROOT)).replace('\\','/'):sha(x) for x in [Path(__file__),E/'remote_run.py']},
        no_credentials=True,no_board=True,no_installation_or_service_changes=True)
    (R/'REMOTE_TRANSFER.json').write_text(json.dumps(entry,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:entry[k] for k in ['archive','archive_sha256','bytes','files','remote_root']}))
if __name__=='__main__':main()
