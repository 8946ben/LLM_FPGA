"""Offline contract, script syntax and evidence checks; not browser rendering."""
from pathlib import Path
import json,re,hashlib,subprocess,urllib.parse
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'doc/log_rebuild_20261030';review=json.loads((R/'BUILD_REVIEW.json').read_text(encoding='utf-8'))
def load(path):
    s=path.read_text(encoding='utf-8');return s,json.loads(re.search(r'<script id="dev-log-data" type="application/json">(.*?)</script>',s,re.S)[1])
html,d=load(ROOT/'开发日志.html');_,old=load(Path(review['backup']['file']))
assert hashlib.sha256(Path(review['backup']['file']).read_bytes()).hexdigest()==review['backup']['sha256']
for e in old['entries']:assert next(x for x in d['entries'] if x['id']==e['id'])==e
assert set(old)<=set(d) and len({e['id'] for e in d['entries']})==len(d['entries'])
assert not any(r['lifecycle']=='active' or any(c['state']=='active' for c in r['cells'].values()) for r in d['exploration']['routes'])
assert d['performance']['default_variant']=='board-exp10-aggregate'
assert len(d['task_overview']['rows'])==5
for task in d['task_overview']['rows']:
    for ident in task['route_ids']:
        route=next(r for r in d['exploration']['routes'] if r['id']==ident)
        assert any(t['id']==task['id'] for t in route['task_refs'])
rows=json.loads((ROOT/'module_14_lm_head_v4/reports/dual_board_20261030_r1/BOARD_FIXED_INPUT_SUMMARY.json').read_text())['rows']
for row in rows:
    ident='board-'+('early' if row['variant']=='baseline_hybrid' else 'exp10')+'-'+row['case'];v=next(x for x in d['performance']['variants'] if x['id']==ident)
    assert v['values']['decode']==row['m14_equivalent_outputs_per_s'] and v['values']['a53_median']==row['median_ms'] and v['values']['ttft'] is None
syntax=R/'syntax';syntax.mkdir(exist_ok=True);count=0
for name in review['generated_files']:
    path=Path(name);s=path.read_text(encoding='utf-8')
    assert not re.search(r'<script[^>]+src=|<link[^>]+href=["\']https?://',s,re.I)
    for attrs,body in re.findall(r'<script([^>]*)>(.*?)</script>',s,re.S):
        if 'application/json' in attrs:
            json.loads(body);continue
        p=syntax/f'{path.stem}_{count}.js';p.write_text(body,encoding='utf-8')
        result=subprocess.run(['C:/Program Files/nodejs/node.exe','--check',str(p)],capture_output=True,text=True);assert result.returncode==0,result.stderr;count+=1
missing=[];unsafe=[];checked=set()
def walk(v,prefix=''):
    if isinstance(v,dict):
        if isinstance(v.get('href'),str):
            h=v['href'];u=urllib.parse.urlsplit(h)
            if u.scheme and u.scheme not in ['http','https','file']:unsafe.append((prefix,h))
            elif not u.scheme and u.path:
                target=ROOT/urllib.parse.unquote(u.path.replace('\\','/'));checked.add(str(target))
                if not target.exists():missing.append((prefix,h))
        for k,x in v.items():walk(x,prefix+'/'+k)
    elif isinstance(v,list):
        for i,x in enumerate(v):walk(x,prefix+'/'+str(i))
walk(d);assert not unsafe,unsafe
# Existing evidence references are retained even if historical artifacts are missing.
old_missing=[]
def old_hrefs(v):
    if isinstance(v,dict):
        if 'href' in v:old_missing.append(v['href'])
        for x in v.values():old_hrefs(x)
    elif isinstance(v,list):
        for x in v:old_hrefs(x)
old_hrefs(old);new_missing=[x for x in missing if x[1] not in old_missing];assert not new_missing,new_missing
result=dict(state='PASS_STATIC_HISTORY_DATA_NAV_MAPPING_AND_JS_SYNTAX',historical_entries_preserved=len(old['entries']),entries=len(d['entries']),routes=len(d['exploration']['routes']),tasks=5,syntax_scripts=count,local_evidence_targets=len(checked),historical_missing_references=missing,new_missing_references=new_missing,backup_sha_verified=True,board_values_exact=True,offline_no_external_script_dependencies=True,browser_visual='NOT_RUN_FILE_URL_SECURITY_POLICY',touch_desktop_narrow_checks='NOT_RUN_NO_POLICY_BYPASS',note='Static checks do not prove rendered layout or touch behavior')
(R/'CHECK_REVIEW.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
review['visual']='NOT_RUN_FILE_URL_SECURITY_POLICY';(R/'BUILD_REVIEW.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
