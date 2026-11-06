"""Independent consistency checks for costs, stage observations and both pages."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import collections,hashlib,json,math,statistics,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/sparse_methods_20261024_r1';B=R/'benchmark'
sys.path.insert(0,str(M))
from reference.quality_data import load_split
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Doc(HTMLParser):
    def __init__(self,text):super().__init__();self.ids=[];self.links=[];self.resources=[];self.feed(text)
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if 'id' in d:self.ids.append(d['id'])
        if tag=='a':self.links.append(d.get('href',''))
        if tag in ['script','link','img','iframe'] and ('src' in d or 'href' in d):self.resources.append(d.get('src',d.get('href')))
def main():
    V,H=151936,896;bench=read(B/'RESULT.json');analysis=read(R/'ANALYSIS.json');final=read(R/'RESULT.json');profile=read(R/'STAGE_PROFILE.json');entry=read(R/'STAGE_PROFILE_ENTRY.json');cal=load_split(M/'data/hidden_v1/calibration')
    assert analysis['result_sha256']==final['benchmark_sha256']==sha(B/'RESULT.json')
    assert analysis['script_sha256']==sha(ROOT/'tools/analyze_v4_sparse_methods_20261024.py')
    assert final['selector_review_sha256']==sha(R/'SELECTOR_REVIEW.json')
    assert entry['source_sha256']==sha(M/'scripts/profile_sparse_methods_20261024.py')
    assert entry['benchmark_sha256']==sha(B/'RESULT.json')
    byid={p['id']:p for p in bench['configurations']};assert len(analysis['rows'])==557
    for c in analysis['rows']:
        p=byid[c['id']];a=p['parameters'];mode=p['mode'];k=p['candidate_decode']['mean'];extra=0
        if mode=='cluster':extra=a['C']*H
        elif mode=='lowrank':extra=a['r']*(H+V)
        elif mode=='hybrid':extra=a['C']*H+a['r']*(H+V)
        elif mode=='partial':extra=V*a['d']+(H if a['choice']=='dynamic' else 0)
        elif mode in ['affinity','learned']:extra=a['C']*H
        elif mode=='lsh':extra=8*a['b']*H
        assert c['selector_multiplication_terms']==extra and c['exact_multiplication_terms']==k*H
        assert c['total_multiplication_terms']==extra+k*H
        assert c['logical_weight_read_bytes']==2*k*H
        assert c['logical_main_read_bytes']==c['logical_weight_read_bytes']+c['logical_preview_read_bytes']+c['logical_list_read_bytes']
        assert c['exceeds320MiB_before_common_buffers']==(c['stored_weight_and_index_lower_bound_bytes']>320*2**20)
        if mode=='partial':
            assert c['logical_preview_read_bytes']==2*V*a['d']
            assert c['stored_weight_and_index_lower_bound_bytes']>=2*V*H+2*V*(H if a['choice']=='dynamic' else a['d'])
        if 'list_entries_array' in c:
            path=R/c['list_entries_array'];assert sha(path)==c['list_entries_array_sha256']
            with np.load(path) as z:e=z['list_entries']
            assert c['list_entries_mean']==float(e[cal['decode']].mean()) and c['logical_list_read_bytes']==4*c['list_entries_mean']
    raw=read(R/'STAGE_PROFILE_RAW.json');assert len(raw)==profile['measurements']==2880
    assert profile['raw_sha256']==sha(R/'STAGE_PROFILE_RAW.json')
    proof={(r['id'],r['case']):r for r in read(B/'GPU_NUMERIC_PROOF.json')['records']}
    for p in profile['records']:
        rows=[x for x in raw if x['id']==p['id']];assert len(rows)==40
        assert collections.Counter((x['case'],x['round']) for x in rows)=={(c,i):1 for c in ['chinese','english','code','math'] for i in range(10)}
        assert p['selector_mean_ms']==statistics.mean(x['selector_wall_ms'] for x in rows)
        assert p['exact_policy_return_mean_ms']==statistics.mean(x['exact_policy_return_wall_ms'] for x in rows)
        for x in rows:
            assert math.isfinite(x['selector_wall_ms']) and x['selector_wall_ms']>=0 and math.isfinite(x['exact_policy_return_wall_ms']) and x['exact_policy_return_wall_ms']>0
            for k in ['token','score_bits','crc','k']:assert x[k]==proof[x['id'],x['case']][k]
    for file in ['V4Validation.html','V4SparseMethods.html']:
        p=ROOT/'doc/design'/file;text=p.read_text(encoding='utf-8');doc=Doc(text);assert len(doc.ids)==len(set(doc.ids)),file
        assert not doc.resources
        for h in doc.links:
            u=urlsplit(h)
            if u.scheme or not u.path:continue
            assert (p.parent/unquote(u.path)).resolve().exists(),(file,h)
        if file=='V4SparseMethods.html':
            assert {'partial','affinity','learned','lsh','costs','all-results'}<=set(doc.ids)
            assert '519.31' in text and '66,840' in text
    review=dict(state='PASS_COST_FORMULAS_STAGE2880_OUTPUTS_AND_TWO_STATIC_REPORTS',configurations=557,new_configs=68,cost_formulas_verified=557,stage_calls_verified=2880,selector_review_sha256=sha(R/'SELECTOR_REVIEW.json'),analysis_sha256=sha(R/'ANALYSIS.json'),report_sha256=sha(ROOT/'doc/design/V4SparseMethods.html'),main_page_sha256=sha(ROOT/'doc/design/V4Validation.html'),browser_visual='NOT_RUN',gpu_this_checker='NONE',hardware='NOT_RUN')
    (R/'REPORT_REVIEW.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(review,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
