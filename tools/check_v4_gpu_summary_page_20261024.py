"""Static page/data/link/JS checks. Does not overwrite old experiment reports."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import collections,csv,hashlib,json,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'module_14_lm_head_v4/reports/gpu_summary_20261024_r1'
class Doc(HTMLParser):
    def __init__(self,text):super().__init__();self.ids=[];self.links=[];self.resources=[];self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='a' and 'href' in a:self.links.append(a['href'])
        if tag in ['script','img','iframe','link'] and ('src' in a or 'href' in a):self.resources.append(a.get('src',a.get('href')))
def payload(text,id):return json.loads(re.search(r'<script id="'+id+r'" type="application/json">(.*?)</script>',text,re.S)[1])
def main():
    global R
    if len(sys.argv)>1:R=ROOT/sys.argv[1]
    page=ROOT/'doc/design/V4Validation.html';text=page.read_text(encoding='utf-8');doc=Doc(text)
    assert len(doc.ids)==len(set(doc.ids)),collections.Counter(doc.ids)
    assert not doc.resources
    for href in doc.links:
        u=urlsplit(href)
        if u.scheme or not u.path:continue
        assert (page.parent/unquote(u.path)).resolve().exists(),href
    journal=(ROOT/'开发日志.html').read_text(encoding='utf-8');assert payload(text,'validation-data')==payload(journal,'dev-log-data')['v4_validation']
    summary=payload(text,'gpu-summary-data');expected=json.loads((R/'SUMMARY_DATA.json').read_text(encoding='utf-8'));assert summary==expected
    assert text.index('id="gpu-summary"')<text.index('id="experiments"')
    total=557 if summary.get('new_research') else 489;assert len(summary['points'])==total
    assert len(list(csv.DictReader((R/'SUMMARY.csv').read_text(encoding='utf-8-sig').splitlines())))==total
    scratch=ROOT/'.cache/gpu_summary_page_20261024';scratch.mkdir(exist_ok=True);count=0
    for i,(attrs,js) in enumerate(re.findall(r'<script([^>]*)>(.*?)</script>',text,re.S)):
        if 'application/json' in attrs:continue
        p=scratch/f'page-{i}.js';p.write_text(js,encoding='utf-8')
        proc=subprocess.run(['C:/Program Files/nodejs/node.exe','--check',str(p)],capture_output=True,text=True);assert proc.returncode==0,proc.stderr;count+=1
    assert json.loads((R/'UI_LOGIC_REVIEW.json').read_text(encoding='utf-8'))['state']=='PASS_EMBEDDED_DATA_AND_FUNCTIONAL_UI_LOGIC_DOM_DOUBLE'
    result=dict(state='PASS_STATIC_PAGE_PAYLOAD_LINKS_INLINE_JS_AND_CSV',date='2026-10-24',timezone='Asia/Shanghai',points=total,panel_above_experiments=True,old_validation_payload_matches_journal=True,duplicate_ids=0,external_resources=0,all_local_links_exist=True,javascript_blocks_checked=count,dom_logic='PASS_SEPARATE_DOM_DOUBLE_TEST',browser_visual='NOT_RUN',page_sha256=hashlib.sha256(page.read_bytes()).hexdigest(),scope='Does not run browser, GPU, EDA or board')
    (R/'PAGE_REVIEW.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
