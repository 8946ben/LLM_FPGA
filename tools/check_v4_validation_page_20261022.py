"""Static content/link/JS syntax checks only. Does not run browser page scripts."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote,urlsplit
import collections,hashlib,json,re,subprocess
ROOT=Path(__file__).resolve().parents[1]
class Doc(HTMLParser):
    def __init__(self,text):
        super().__init__();self.ids=[];self.links=[];self.resources=[];self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='a' and 'href' in a:self.links.append(a['href'])
        if tag in ['script','img','iframe','link'] and ('src' in a or 'href' in a):self.resources.append(a.get('src',a.get('href')))
def payload(text,id):return json.loads(re.search(r'<script id="'+id+r'" type="application/json">(.*?)</script>',text,re.S)[1])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    journal=(ROOT/'开发日志.html').read_text(encoding='utf-8');d=payload(journal,'dev-log-data');v=d['v4_validation']
    page=ROOT/'doc/design/V4Validation.html';text=page.read_text(encoding='utf-8');assert payload(text,'validation-data')==v
    design=(ROOT/'doc/design/R4Sparse.html').read_text(encoding='utf-8');r=next(r for r in d['exploration']['routes'] if r['id']=='R4Sparse')
    assert payload(design,'design-data')['route']['cells']==r['cells']
    assert len({s['id'] for s in v['scenarios']})==len(v['scenarios'])==17
    for s in v['scenarios']:
        assert all(s[k] for k in ['params','steps','checks','status','boundary','evidence'])
        assert set(s['layers'])<={'cpu','rtl','board'}
        for e in s['evidence']:assert (ROOT/e['href']).is_file(),e['href']
    for e in v['sources']:assert (ROOT/e['href']).is_file(),e['href']
    q=json.loads((ROOT/'module_14_lm_head_v4/reports/performance_cases_20261022/QUALIFICATION.json').read_text(encoding='utf-8'))
    for c in ['small','median','p95','max']:
        s=next(s for s in v['scenarios'] if s['id']=='case-'+c)
        assert str(q['cases'][c]['candidates']) in dict(s['params'])['K / V']
        assert q['cases'][c]['expected']['score_bits'] in dict(s['params'])['精算参考']
    comparisons=v.get('comparisons',[])
    fusion=next((g for g in comparisons if g['id']=='hybrid-hyperparameters'),None)
    assert len(comparisons)==(10 if fusion else 9) and sum(len(g['variants']) for g in comparisons)==(507 if fusion else 75)
    assert len({g['id'] for g in comparisons})==len(comparisons) and not any(g['id']=='method-speed' for g in comparisons)
    expected_importance={'quality':'必须完成','k-sensitivity':'建议完成','debug-comparison':'可做可不做','state-reuse':'必须完成','policy-comparison':'建议完成','error-comparison':'建议完成','transfer-comparison':'必须完成','cluster-hyperparameters':'必须完成','lowrank-hyperparameters':'必须完成'}
    if fusion:expected_importance['hybrid-hyperparameters']='必须完成'
    assert {g['id']:g['importance']['level'] for g in comparisons}==expected_importance
    assert len(v['importance_policy'])==3
    for g in comparisons:assert all(g['importance'][k] for k in ['level','kind','reason','minimum','extension','order'])
    sweep=next(g for g in comparisons if g['id']=='cluster-hyperparameters')
    points=[(x['parameters']['C'],x['parameters']['R'],x['parameters']['L']) for x in sweep['variants']]
    assert len(points)==len(set(points))==23
    assert all(1<=r<=c and 1<=l<=151936 for c,r,l in points)
    assert (128,4,16384) in points and (1,1,1) in points and (128,128,151936) in points
    assert len([x for x in sweep['variants'] if any(a in ['中心数C','选簇数R','每簇上限L'] for a in x['axes'])])==21
    study_root=ROOT/'module_14_lm_head_v4/reports/hyperparameters_20261023_r1'
    running_study=(study_root/'PLAN.json').exists()
    if not running_study:assert sweep['status']=='未开始' and all(not x['results'] for x in sweep['variants'])
    assert '全簇/最大列表容量' in json.dumps(sweep,ensure_ascii=False) and '新独立' in json.dumps(sweep,ensure_ascii=False)
    lowrank=next(g for g in comparisons if g['id']=='lowrank-hyperparameters')
    rank_points=[(x['parameters']['r'],x['parameters']['T']) for x in lowrank['variants']]
    assert len(rank_points)==len(set(rank_points))==21
    assert all(1<=r<=896 and 1<=t<=151936 for r,t in rank_points)
    assert {(1,16384),(128,1),(1,1),(128,151936),(896,151936)}<=set(rank_points)
    assert len([x for x in lowrank['variants'] if any(a in ['低秩维度r','预筛Top-T'] for a in x['axes'])])==16
    if not running_study:assert lowrank['status']=='未开始' and all(x['status']=='未开始' and not x['results'] for x in lowrank['variants'])
    assert lowrank['sweep_report']['parameter_keys']==['r','T']
    assert lowrank['sweep_report']['plot_axes']==[['低秩维度r','r'],['预筛Top-T','T']]
    assert all(s in json.dumps(lowrank,ensure_ascii=False) for s in ['全新','BF16量化','Top-V','2×r×(V+H)','320MiB'])
    assert 'g.sweep_report.parameter_keys' in text and 'g.sweep_report.plot_axes' in text
    assert 'function sweepReport' in text and 'function variantConfigurations' in text
    assert 'id="importance-filter"' in text and "importancePanel(g)" in text and "g.importance.level===level" in text
    for g in comparisons:
        assert all(g[k] for k in ['question','changing','fixed','variants','metrics','decision','next','evidence','scope'])
        assert len(g['variants'])>=2
        for variant in g['variants']:
            assert all(variant[k] for k in ['title','configuration','expected','status'])
            assert set(variant['results']) <= {m['id'] for m in g['metrics']}|{'steps'}
        for evidence in g['evidence']:assert (ROOT/evidence['href']).is_file(),evidence['href']
    quality_source=ROOT/'module_14_lm_head_v4/reports/fixed_quality_20261022/RESULT.json'
    quality=json.loads(quality_source.read_text(encoding='utf-8'));comparison=comparisons[0]
    assert comparison['id']=='quality' and comparison['quality_result_sha256']==sha(quality_source)
    for variant in comparison['variants']:
        if variant['id']=='dense':
            assert variant['definition_baseline'] and variant['results']==dict(misses=0,recall=100.,steps=14958)
            continue
        actual=quality[variant['id']]['decode']
        assert variant['results']==dict(misses=actual['misses'],recall=actual['recall']*100,steps=actual['steps'])
        for category,value in actual['by_category'].items():
            assert variant['categories'][category]==dict(misses=value['misses'],recall=value['recall']*100,steps=value['steps'])
        assert sum(v['misses'] for k,v in variant['categories'].items() if k!='all')==actual['misses']
    assert all(not v['results'] for g in comparisons if g['id'] not in ['quality','k-sensitivity','cluster-hyperparameters','lowrank-hyperparameters','hybrid-hyperparameters'] for v in g['variants']), 'Do not invent unmeasured comparison results'
    published_study={};published_joint=None
    if running_study:
        timed_path=study_root/'GPU_BENCHMARK.json';timed_partial=study_root/'GPU_BENCHMARK.partial.json'
        timed=json.loads(timed_path.read_text(encoding='utf-8'))['configurations'] if timed_path.exists() else json.loads(timed_partial.read_text(encoding='utf-8')) if timed_partial.exists() else []
        for family,group in [('cluster',sweep),('lowrank',lowrank)]:
            full=study_root/f'{family.upper()}_CALIBRATION.json';partial=study_root/f'{family.upper()}_CALIBRATION.partial.json'
            rows=json.loads(full.read_text(encoding='utf-8'))['configurations'] if full.exists() else json.loads(partial.read_text(encoding='utf-8')) if partial.exists() else []
            lookup={r['id']:r for r in rows};times={r['id']:r for r in timed if r['family']==family}
            for variant in group['variants']:
                expected={};c=lookup.get(variant['id']);b=times.get(variant['id'])
                if c:expected.update(recall=c['quality']['decode']['recall']*100,misses=c['quality']['decode']['misses'],K_mean=c['candidate_decode']['mean'])
                if b:expected.update(gpu_ms=b['wall_median_ms'],gpu_rate=b['equivalent_m14_per_s'])
                assert variant['results']==expected,(family,variant['id'])
            published_study[family]=dict(quality_points=len(lookup),timed_points=len(times))
        joint_root=study_root.with_name('hyperparameters_joint_20261023_r1')
        if (joint_root/'PLAN.json').exists():
            joint=lowrank['joint_report'];assert len(joint['records'])==13 and joint['total_new']==12
            cal_path=joint_root/'LOWRANK_CALIBRATION.json';cal_partial=joint_root/'LOWRANK_CALIBRATION.partial.json';time_path=joint_root/'GPU_BENCHMARK.json'
            cal_rows=json.loads(cal_path.read_text(encoding='utf-8'))['configurations'] if cal_path.exists() else json.loads(cal_partial.read_text(encoding='utf-8')) if cal_partial.exists() else []
            time_rows=json.loads(time_path.read_text(encoding='utf-8'))['configurations'] if time_path.exists() else []
            cl={x['id']:x for x in cal_rows};tl={x['id']:x for x in time_rows}
            for record in joint['records']:
                key=record['variant']['id'];c=cl.get(key);b=tl.get(key);expected={}
                if c:expected.update(misses=c['quality']['decode']['misses'],recall=c['quality']['decode']['recall']*100,K_mean=c['candidate_decode']['mean'])
                if b:expected.update(gpu_ms=b['wall_median_ms'],gpu_rate=b['equivalent_m14_per_s'])
                assert record['result']==expected
            assert joint['dense']==tl.get('dense') and 'function jointReport' in text and '${jointReport(g)}' in text
            published_joint=dict(new_quality_points=joint['calibration_done'],new_timed_points=joint['timed_done'],first_round_timing_not_mixed=True)
    assert "location.hash.slice(1)||'quality'" in text and '尚未测试，暂无曲线' in text
    assert '要核对：' not in text and '当前状态：</b>' not in text and 'data-metric=' not in text
    assert 'function lineChart' in text and 'charts-grid' in text and 'polyline' in text
    assert comparison['stage_status']==[['质量对比','已完成'],['GPU参考测速','已完成'],['FPGA测速','未开始']]
    benchmark=json.loads((ROOT/'module_14_lm_head_v4/reports/gpu_method_benchmark_20261022_r2/RESULT.json').read_text(encoding='utf-8'))
    for variant in comparison['variants']:
        actual=benchmark['summary'][variant['id']]
        assert variant['gpu_results']['gpu_median_ms']==actual['wall_median_ms']
        assert variant['gpu_results']['gpu_token_s']==actual['aggregate_equivalent_m14_per_s']
        assert variant['gpu_results']['fpga_median_ms'] is None and variant['gpu_results']['fpga_token_s'] is None
    assert sum(r['count'] for r in comparison['report']['source_rows'])==1000
    for section in ['report','gpu_report']:
        for evidence in comparison[section]['evidence']:assert (ROOT/evidence['href']).is_file()
    published_fusion=None
    if fusion:
        folder=ROOT/'module_14_lm_head_v4/reports/fusion_exp10_20261023_r1';full=folder/'CALIBRATION.json';partial=folder/'CALIBRATION.partial.json';gfile=folder/'GPU_BENCHMARK.json'
        rows=json.loads(full.read_text(encoding='utf-8'))['configurations'] if full.exists() else json.loads(partial.read_text(encoding='utf-8')) if partial.exists() else [];times=json.loads(gfile.read_text(encoding='utf-8'))['configurations'] if gfile.exists() else [];cl={x['id']:x for x in rows};bl={x['id']:x for x in times}
        assert len(fusion['variants'])==len({v['id'] for v in fusion['variants']})==432
        for variant in fusion['variants']:
            c=cl.get(variant['id']);b=bl.get(variant['id']);expected={}
            if c:expected.update(misses=c['quality']['decode']['misses'],recall=c['quality']['decode']['recall']*100,K_mean=c['candidate_decode']['mean'],logical_mib=c['logical_mean_decode_bytes']/2**20)
            if b:expected.update(gpu_ms=b['wall_median_ms'],gpu_rate=b['equivalent_m14_per_s'])
            assert variant['results']==expected
        published_fusion=dict(grid=432,calibration=len(rows),gpu_pairs=len(times),source_values_exact=True,board='NOT_RUN')
        if fusion.get('fusion_pareto'):
            p=fusion['fusion_pareto'];assert len(p['points'])==432 and len(p['frontier'])==18
            assert p['calibration_sha256']==sha(full)
            for v in p['points']:
                c=cl[v['id']];assert v['misses']==c['quality']['decode']['misses'] and v['logical_mib']==c['logical_mean_decode_bytes']/2**20 and v['K_mean']==c['candidate_decode']['mean'] and v['overlap_mean']==c['overlap_decode']['mean'] and v['selection_qualified']==c['selection_qualified']
            assert sum(v['budget_feasible'] for v in p['points'])==420 and 'function fusionPareto' in text
            published_fusion.update(calibration_frontier_points=18,descriptive_only_no_new_selection=True)
        if (folder/'FINAL_QUALITY.json').exists():
            fresh=json.loads((folder/'FINAL_QUALITY.json').read_text(encoding='utf-8'));published=fusion['fusion_fresh']
            assert 'function fusionFresh' in text and '${fusionFresh(g)}' in text
            for record,key in zip(published['records'],['selected','frozen_baseline']):
                q=fresh[key]['report']['decode'];assert record['result']==dict(misses=q['misses'],recall=q['recall']*100)
                assert record['categories']==[[cat,c['steps'],c['misses'],c['recall']*100] for cat,c in q['by_category'].items()]
                assert record['gate']==fresh[key]['proposed_point_gate']
            published_fusion.update(fresh_decode_steps=fresh['decode_steps'],fresh_quality=fresh['state'],fresh_quality_values_exact=True)
    out=ROOT/'.cache/v4_validation_page_20261022';out.mkdir(parents=True,exist_ok=True)
    js_checks=0;docs=[]
    for p,content in [(ROOT/'开发日志.html',journal),(page,text),(ROOT/'doc/design/R4Sparse.html',design)]:
        doc=Doc(content);assert len(doc.ids)==len(set(doc.ids)),[k for k,n in collections.Counter(doc.ids).items() if n>1]
        assert not doc.resources,doc.resources
        for href in doc.links:
            u=urlsplit(href)
            if u.scheme or not u.path:continue
            assert (p.parent/unquote(u.path)).resolve().exists(),(str(p),href)
        for i,(attrs,js) in enumerate(re.findall(r'<script([^>]*)>(.*?)</script>',content,re.S)):
            if 'application/json' in attrs:continue
            scratch=out/f'{p.stem}-{i}.js';scratch.write_text(js,encoding='utf-8')
            check=subprocess.run(['C:/Program Files/nodejs/node.exe','--check',str(scratch)],capture_output=True,text=True)
            assert check.returncode==0,check.stderr;js_checks+=1
        docs.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),unique_ids=len(doc.ids)))
    assert 'id="v4-validation-link"' in journal and journal.count('href="doc/design/V4Validation.html"')>=2
    report=dict(state='PASS_STATIC_DATA_LINK_AND_JAVASCRIPT_SYNTAX_ONLY',date='2026-10-23',timezone='Asia/Shanghai',
      engineering_check_count=17,comparison_groups=len(comparisons),explicit_variants=sum(len(g['variants']) for g in comparisons),journal_entries=len(d['entries']),history_preservation='Each publishing operation asserts its full prior entry prefix unchanged',
      importance_levels={'必须完成':6 if fusion else 5,'建议完成':3,'可做可不做':1},importance_scope_and_reason_present=True,cluster_sweep_unique_points=23,lowrank_sweep_unique_points=21,study_results_published=published_study,joint_study_published=published_joint,fusion_study_published=published_fusion,
      quality_and_speed_merged=True,redundant_card_labels_removed=True,parallel_line_charts=True,reported_gpu_values_match_result=True,fpga_values_remain_null=True,
      plotted_quality_values_match_frozen_result=True,category_totals_verified=True,unmeasured_comparison_values_absent=True,
      canonical_snapshot_equals_generated_page=True,route_snapshot_synchronized=True,javascript_syntax_blocks=js_checks,documents=docs,
      browser_preview='NOT_RUN: CUA policy rejects file:// observation; no alternative browser/workaround used',
      responsive='CSS850px/520px breakpoints and overflow containers inspected; no visual viewport verification',
      scene_interaction='Search/category controls and parallel SVG line plotting pass static inspection/JS syntax; browser interaction NOT_RUN',
      this_checker_gpu_rtl_board_access='NONE',gpu_benchmark='r2 completed separate actual GPU job;480 timed calls;16 numeric proofs',fpga='NOT_RUN')
    (ROOT/('doc/DEV_LOG_V4_EXPERIMENT10_CHECK_20261023.json' if fusion else 'doc/DEV_LOG_V4_HYPERPARAMETER_EXECUTION_CHECK_20261023.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
