"""Static evidence/link checks for the literature and experiment documents."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
from datetime import datetime, timezone, timedelta
import hashlib, json, re, subprocess
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[2]
MOD=ROOT/'module_14_lm_head_v4b'
PAGE=ROOT/'doc/design/V4bValidation.html'
REPORT=MOD/'reports/research_design'

class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids=[]; self.links=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'id' in attrs:self.ids.append(attrs['id'])
        if tag=='a' and 'href' in attrs:self.links.append(attrs['href'])

def main():
    REPORT.mkdir(parents=True,exist_ok=True)
    source=PAGE.read_text(encoding='utf-8')
    page=Page(); page.feed(source)
    assert len(page.ids)==len(set(page.ids)), 'Duplicate DOM id'
    scripts=re.findall(r'<script([^>]*)>(.*?)</script>',source,re.S)
    embedded=json.loads(next(body for attr,body in scripts if 'application/json' in attr))
    plan=json.loads((MOD/'experiments/quantization_study/PLAN.json').read_text(encoding='utf-8'))
    assert plan==embedded['plan']
    assert len(plan['experiments'])==12
    assert all(e['status']=='NOT_RUN' and all(v is None for v in e['results'].values()) for e in plan['experiments'])
    exps={e['id'] for e in plan['experiments']}
    allowed=set(page.ids)|exps
    links=[]
    for href in page.links:
        url=urlsplit(href)
        if url.scheme: continue
        path=(PAGE.parent/unquote(url.path)).resolve() if url.path else PAGE
        # The validation report is the last output written by this command.
        exists=path.exists() or path==REPORT/'VALIDATION.json'
        assert exists, f'Missing link: {href}'
        if not url.path and url.fragment: assert url.fragment in allowed, f'Missing anchor: {href}'
        links.append(href)
    manifest=json.loads((ROOT/'doc/paper/lm_head_quantization/manifest.json').read_text(encoding='utf-8'))
    assert not manifest['errors'] and len(manifest['papers'])==16
    pdfs=[]
    for p in manifest['papers']:
        path=ROOT/'doc/paper/lm_head_quantization'/p['file']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==p['sha256']
        reader=PdfReader(path)
        assert len(reader.pages)==p['pages']
        assert all(x in exps for x in p['experiments'])
        text=reader.pages[0].extract_text() or ''
        assert len(text)>300, p['id']+' first page unreadable'
        pdfs.append(dict(id=p['id'],pages=p['pages'],sha256=p['sha256'],first_page_text=True))
    lock=json.loads((MOD/'baseline/SOURCE_LOCK.json').read_text(encoding='utf-8'))
    for item in lock['files']:
        assert hashlib.sha256((MOD/item['snapshot']).read_bytes()).hexdigest()==item['sha256']
        assert hashlib.sha256((ROOT/item['source']).read_bytes()).hexdigest()==item['sha256']
    for i,(attrs,body) in enumerate(scripts):
        if 'application/json' in attrs: continue
        js=REPORT/f'inline_{i}.js'
        js.write_text(body,encoding='utf-8')
        subprocess.run(['node','--check',str(js)],check=True,capture_output=True)
    # Confirm the exact quote locator used in the notes.
    gptq=PdfReader(ROOT/'doc/paper/lm_head_quantization/Q01_GPTQ_2210.17323v2.pdf')
    assert 'which are kept in full FP16' in gptq.pages[7].extract_text()
    # Assert headline storage numbers independently of the page JavaScript.
    h,v=896,151936
    row=((h//128*(128*4//8+4)+63)//64)*64
    assert row==512 and v*row/1048576==74.1875
    assert (v*row+v*h*2)/1048576==333.84375
    qa_path=REPORT/'QA_REVIEW.json'
    qa=json.loads(qa_path.read_text(encoding='utf-8')) if qa_path.exists() else {}
    page_hash=hashlib.sha256(PAGE.read_bytes()).hexdigest()
    browser_qa=qa.get('browser',{}) if qa.get('page_sha256')==page_hash else {'status':'PENDING'}
    report=dict(status='PASS_STATIC_RESEARCH_CHECKS',
        checked_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),
        page=str(PAGE),page_sha256=hashlib.sha256(PAGE.read_bytes()).hexdigest(),
        embedded_plan_matches=True,experiments=12,all_experiments_not_run=True,
        local_links_checked=len(links),unique_dom_ids=len(page.ids),javascript_syntax='PASS',
        baseline_snapshots_checked=len(lock['files']),original_package_members_checked=len(lock['package_members_checked']),
        pdfs=pdfs,pdf_count=16,pdf_original_sha_and_parse='PASS',gptq_output_layer_locator='physical_page_8',
        storage_formula='PASS',browser_qa=browser_qa,pdf_visual_qa=qa.get('pdf_visual',{'status':'PENDING'}),
        model_gpu_eda_board_runs='NOT_RUN')
    (REPORT/'VALIDATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='pdfs'},ensure_ascii=False))

if __name__=='__main__':main()
