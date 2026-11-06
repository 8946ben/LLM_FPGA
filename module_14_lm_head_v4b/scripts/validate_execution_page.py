"""Static page/source checks; deliberately does not automate blocked file:// UI."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import hashlib,json,re,subprocess
M=Path(__file__).resolve().parents[1];ROOT=M.parent;O=M/'reports/quantization_20261023_r1';PAGE=ROOT/'doc/design/V4bValidation.html'
class Parser(HTMLParser):
    def __init__(self):super().__init__();self.ids=[];self.hrefs=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='a' and 'href' in a:self.hrefs.append(a['href'])
def main():
    text=PAGE.read_text(encoding='utf-8');p=Parser();p.feed(text);assert len(p.ids)==len(set(p.ids))
    scripts=re.findall(r'<script([^>]*)>(.*?)</script>',text,re.S)
    data=json.loads(next(s for a,s in scripts if 'application/json' in a));experiments=data['plan']['experiments']
    assert len(experiments)==12
    points=list((O/'points').glob('*/RESULT.json'))
    assert data['execution']['completed_quantization_points']==len(points)
    for e in experiments:
        if e['id'] in ['q04','q05','q06','q10','q11','q12']:
            assert e['status']=='NOT_RUN' and all(v is None for v in e['results'].values()),e['id']
    anchors=set(p.ids)|{e['id'] for e in experiments};checked=0
    for href in p.hrefs:
        u=urlsplit(href)
        if u.scheme:continue
        path=(PAGE.parent/unquote(u.path)).resolve() if u.path else PAGE
        assert path.exists() or path==O/'PAGE_VALIDATION.json',href
        if not u.path and u.fragment:assert u.fragment in anchors,href
        checked+=1
    for i,(attrs,body) in enumerate(scripts):
        if 'application/json' in attrs:continue
        js=O/f'page_inline_{i}.js';js.write_text(body,encoding='utf-8')
        subprocess.run(['node','--check',str(js)],check=True,capture_output=True)
    final=O/'FINAL_QUALITY.json'
    if final.exists():
        assert data['execution']['final_quality']==json.loads(final.read_text())['state']
        top=json.loads((M/'PROGRESS.json').read_text(encoding='utf-8'))
        assert top['gpu']=='PASS_PACKED_GPU_REFERENCE' and top['final_quality']==data['execution']['final_quality']
    result=dict(state='PASS_EXECUTION_PAGE_STATIC_CHECKS',page_sha256=hashlib.sha256(PAGE.read_bytes()).hexdigest(),
      completed_quantization_points=len(points),experiment_groups=12,local_links=checked,javascript_syntax='PASS',
      unrun_phases_preserved=True,browser_visual='NOT_RUN_THIS_REVISION',
      browser_limit='Browser URL security policy rejected file:// observation; no workaround attempted. Static file/data/script checks performed.',
      source='The page is a saved snapshot; live status is PROGRESS/QUALITY_SEQUENCE and result JSON.')
    (O/'PAGE_VALIDATION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(result['state'])
if __name__=='__main__':main()
