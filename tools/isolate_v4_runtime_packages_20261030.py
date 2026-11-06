from pathlib import Path
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/dual_board_20261030_r1'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
for name,base in [('baseline_hybrid',M),('exp10',M/'experiments/fusion_exp10_20261023')]:
    src=base/'reports/board_v4_20261021/private_package_r1';dst=R/'runtime_packages'/name;assert not dst.exists();dst.mkdir(parents=True)
    expected={}
    for line in (src/'SHA256SUMS.txt').read_text().splitlines():
        if not line.strip():continue
        h,n=line.split('  ',1);assert sha(src/n)==h,n;expected[n]=h;shutil.copy2(src/n,dst/n)
    shutil.copy2(src/'SHA256SUMS.txt',dst/'SHA256SUMS.txt')
    extras=[p for p in src.iterdir() if p.name not in expected and p.name!='SHA256SUMS.txt']
    archived=[]
    if extras:
        evidence=R/'preserved_loadhw_generated'/name;evidence.mkdir(parents=True)
        for p in extras:
            target=evidence/p.name
            assert ROOT in p.resolve().parents and ROOT in target.resolve().parents and not target.exists()
            archived.append(p.name);shutil.move(str(p),str(target))
    (dst.parent/(name+'_COPY_AUDIT.json')).write_text(json.dumps(dict(state='PASS_RUNTIME_COPY_BOUND_FILES_IDENTICAL',bound_files=expected,original_generated_extras_preserved=archived,reason='XSCT loadhw extracts collateral adjacent to XSA; only runtime copies may be used henceforth'),indent=2)+'\n')
print('RUNTIME_COPIES_CREATED_AND_ORIGINAL_EXTRAS_PRESERVED')
