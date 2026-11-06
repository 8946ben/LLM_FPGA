"""Publish evidence-backed snapshots for experiments8/9, never launch work."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import copy,json,re,sys
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'module_14_lm_head_v4/reports/hyperparameters_20261023_r1'
def read(p):return json.loads(p.read_text(encoding='utf-8')) if p.exists() else None
def main():
    path=ROOT/'开发日志.html';text=path.read_text(encoding='utf-8');m=re.search(r'(<script id="dev-log-data" type="application/json">)(.*?)(</script>)',text,re.S);d=json.loads(m[2]);old=copy.deepcopy(d['entries']);v=d['v4_validation'];progress=read(R/'PROGRESS.json');assert progress
    bench=read(R/'GPU_BENCHMARK.json') or dict(configurations=read(R/'GPU_BENCHMARK.partial.json') or [])
    final=read(R/'RESULT.json');review=read(R/'INDEPENDENT_REVIEW.json') or read(R/'CALIBRATION_REVIEW.json');snapshot=datetime.now(timezone(timedelta(hours=8))).isoformat();counts={}
    for family,id in [('cluster','cluster-hyperparameters'),('lowrank','lowrank-hyperparameters')]:
        g=next(g for g in v['comparisons'] if g['id']==id);cal=read(R/f'{family.upper()}_CALIBRATION.json');rows=(cal or dict(configurations=read(R/f'{family.upper()}_CALIBRATION.partial.json') or []))['configurations'];lookup={r['id']:r for r in rows};blookup={r['id']:r for r in bench['configurations'] if r['family']==family}
        done=len(lookup);timed=len(blookup);counts[family]=dict(calibration=done,timed=timed,total=len(g['variants']))
        g['status']='部分完成' if done else ('待验证' if progress['stage'].startswith('STOPPED') else '进行中')
        g['stage_status']=[['参数与算术准备','已完成' if (R/'NUMERIC_PROOF.json').exists() else '进行中'],['首轮校准',f'{done}/{len(g["variants"])}完成'],['GPU参考测速',f'{timed}/{len(g["variants"])}完成'],['新独立测试/FPGA','未开始']]
        for variant in g['variants']:
            c=lookup.get(variant['id']);b=blookup.get(variant['id']);variant['status']='校准/GPU完成，独立测试待做' if c and b else '校准已完成，GPU待测' if c else '待运行'
            if c:variant['results']['recall']=c['quality']['decode']['recall']*100;variant['results']['misses']=c['quality']['decode']['misses'];variant['results']['K_mean']=c['candidate_decode']['mean'];variant['expected']='已按本轮校准集统计漏选/整体及分类召回和真实K；新独立问题及FPGA未做。'
            if b:variant['results']['gpu_ms']=b['wall_median_ms'];variant['results']['gpu_rate']=b['equivalent_m14_per_s']
        if not any(x['id']=='misses' for x in g['metrics']):g['metrics'].insert(0,dict(id='misses',label='校准decode漏选次数',unit='次',digits=0,direction='越少越好',scope='同一320问题/4775decode，校准选型不代表新独立认证'))
        if not any(x['id']=='gpu_rate' for x in g['metrics']):g['metrics'].append(dict(id='gpu_rate',label='GPU参考等效M14输出率',unit='次/s',digits=2,direction='越高越好',scope='同一4校准夹具，非整网decode或FPGA预测'))
        if not any(x['id']=='K_mean' for x in g['metrics']):g['metrics'].append(dict(id='K_mean',label='decode真实候选数均值',unit='行',digits=2,direction='质量约束下评估',scope='并入14特殊ID的实际并集，不用上界代替'))
        for metric in g['metrics']:
            if metric['id']=='recall':metric['scope']='已完成点来自校准320问题/4775decode；非新独立测试'
            elif metric['id']=='gpu_ms':metric['scope']='同轮4个固定校准输入，3 warmup+30测量/输入/配置；完整GPU参考调用'
        g['decision']=f'首轮{len(g["variants"])}配置：校准完成{done}点，GPU参考测速完成{timed}点；当前阶段{progress["stage"]}。新独立测试、联合搜索及FPGA均未开始。图中空项为未测，已有原实验1结果不改。'
        g['next']='完成首轮后按校准质量与真实GPU成本确定可行区域，再冻结有限联合点；两路线锁定后才使用全新最终问题组。当前不上板。'
        if review:
            if family=='cluster':
                bound=review['cluster_training_support_bound'];g['sweep_report']['findings']=[['训练支持集的上界',f'全训练raw_top256/winner加特殊ID仅覆盖{bound["unique_global_ids"]}词；全簇/最大列表仍有{bound["decode_irreducible_misses"]}次decode漏选，中文召回99.8333%。'],['当前门槛判定','本轮23点均未通过“整体及每类≥99.9%”校准门槛。该训练投票配方下，纯列表候选都包含于同一个支持集，仅增C/R/L不能补回这两个缺失词。'],['增大L的实际效果','固定C128/R4：L16384→32768→65536，漏选均15；K均值18898.38→19085.50→19085.50，实际正票列表饱和，并不是配置容量都被用满。'],['适用范围','这是该训练配方/有限校准组的支持集边界；增加候选来源、改变训练配方或显式dense fallback是另一项方法变化，不由本实验证明。']]
                g['decision']='仅聚类首轮23点均未达到分项99.9%校准门槛；全簇/全正票列表仍漏2个中文dense赢家，已通过训练支持集独立核对。需要新候选来源或改训练配方，不能靠继续增C/R/L消除这类漏选。'
            else:
                g['sweep_report']['findings']=[['固定Top16384改变rank','r128/256/512/896的decode漏选分别84/34/9/0次；本轮观察到改善，不把它解释为任意rank必然单调。'],['固定rank128改变Top-T','T16384/32768/65536/151936的漏选分别84/34/11/0。Top-V为全精算控制，有额外低秩预览成本。'],['通过拟议校准点门槛的首轮配置','r896/T16384，以及r128/T=V、r896/T=V两种全词表端点；尚未完成联合搜索或新独立测试。'],['资源限制','r896因子273874944B，再加原始W272269312B共546144256B（约520.84MiB），超出现320MiB arena。数学上可行不等于当前FPGA包可以运行。']]
                g['decision']='仅低秩首轮中，稀疏点r896/T16384在4775decode零漏选；r128/T16384漏84，r512/T16384漏9。r896需要约261.2MiB因子，其速度与容量代价须结合本轮GPU结果判断；不是新独立认证或可直接部署配置。'
            dense=next((b for b in bench['configurations'] if b['family']=='dense'),None)
            if dense:g['sweep_report']['findings'].append(['同轮dense GPU对照',f'中位{dense["wall_median_ms"]:.3f}ms，等效{dense["equivalent_m14_per_s"]:.2f}次/s；同一4夹具/30轮，仅M14 Eager参考，不是整体LLM decode。'])
        g['sweep_report']['scan_count']=g['sweep_report']['scan_count'].split('实际执行快照')[0].split('本次只设计计划')[0].split('本次只完成计划')[0].rstrip()+f' 实际执行快照：校准{done}点、GPU{timed}点；详见本轮原始证据。'
        if 'source_report' not in g['sweep_report']:g['sweep_report']['source_report']='训练hidden_v1/train1500，校准hidden_v1/calibration320/4775decode；全部tensor SHA和问题组去重通过。公开来源与采集设置见本轮README和PLAN，未读取新最终测试标签。'
        g['fixed']=[x for x in g['fixed'] if '本次只' not in x]
        base='module_14_lm_head_v4/reports/hyperparameters_20261023_r1/'
        for label,name in [('本轮数据/算术/计时条件','README.md'),('执行前冻结计划与SHA','PLAN.json'),('真实阶段快照','PROGRESS.json'),('隔离源文件身份审计','SOURCE_AUDIT.json')]:
            if not any(e['href']==base+name for e in g['evidence']):g['evidence'].append(dict(label=label,href=base+name))
        for label,name in [('完整CPU/GPU数值证明','NUMERIC_PROOF.json'),('本组全部校准结果',f'{family.upper()}_CALIBRATION.json'),('GPU完整流水计时与原始记录','GPU_BENCHMARK.json')]:
            if (R/name).exists() and not any(e['href']==base+name for e in g['evidence']):g['evidence'].append(dict(label=label,href=base+name))
        for label,name in [('逐步数组与支持集上界复核','CALIBRATION_REVIEW.json'),('全部数值及计时独立复核','INDEPENDENT_REVIEW.json'),('GPU执行前计时口径','GPU_TIMING_PLAN.json'),('两组实验完整结果报告','STUDY_RESULT.md')]:
            if (R/name).exists() and not any(e['href']==base+name for e in g['evidence']):g['evidence'].append(dict(label=label,href=base+name))
    joint_root=R.with_name('hyperparameters_joint_20261023_r1');jp=read(joint_root/'PLAN.json');joint_progress=read(joint_root/'PROGRESS.json');joint_final=read(joint_root/'RESULT.json')
    if jp:
        g=next(x for x in v['comparisons'] if x['id']=='lowrank-hyperparameters');jc=read(joint_root/'LOWRANK_CALIBRATION.json') or dict(configurations=read(joint_root/'LOWRANK_CALIBRATION.partial.json') or []);jb=read(joint_root/'GPU_BENCHMARK.json') or dict(configurations=[]);cl={x['id']:x for x in jc['configurations']};bl={x['id']:x for x in jb['configurations']};records=[]
        for config in jp['configurations']:
            c=cl.get(config['id']);b=bl.get(config['id']);result={}
            if c:result.update(misses=c['quality']['decode']['misses'],recall=c['quality']['decode']['recall']*100,K_mean=c['candidate_decode']['mean'])
            if b:result.update(gpu_ms=b['wall_median_ms'],gpu_rate=b['equivalent_m14_per_s'])
            p=config['parameters'];records.append(dict(variant=dict(title=f'r{p["r"]} / Top-T{p["T"]}'+('（原基线控制）' if config['id']=='r128_T16384' else ''),short_label=f'T={p["T"]}',parameters=p,id=config['id']),result=result))
        new_done=sum(x['id']!='r128_T16384' for x in jc['configurations']);new_timed=sum(x['id'] not in ['dense','r128_T16384'] for x in jb['configurations']);g['joint_report']=dict(title='有限联合扩展：12个新(r,T)点＋原基线及dense控制',description='首轮单参完成后冻结12点，仍只用同一校准集。因子和算术不变，质量与首轮可核对；本段GPU数值来自独立的同轮交错计时，不与首轮GPU曲线混连。',records=records,calibration_done=new_done,timed_done=new_timed,total_new=12,dense=bl.get('dense'),state=joint_progress['stage'] if joint_progress else '待运行')
        joint_review=read(joint_root/'INDEPENDENT_REVIEW.json')
        if joint_review:
            fastest=joint_review['fastest_feasible_joint_point'];dense=joint_review['dense_control'];g['joint_report']['findings']=[['门槛与最快合格联合点',f'整体及每类≥99.9%校准点门槛。最快合格联合点{fastest["id"]}：decode漏{fastest["misses"]}次，GPU中位{fastest["gpu_median_ms"]:.3f}ms、{fastest["gpu_equivalent_m14_per_s"]:.2f}次/s。'],['与本段dense的关系',f'本段dense中位{dense["wall_median_ms"]:.3f}ms、{dense["equivalent_m14_per_s"]:.2f}次/s。已扫描合格单方案没有在本GPU参考实现中胜过同轮dense；不能外推FPGA。'],['整体通过不等于分项通过','r256/T65536整体只漏3次，但英文漏2/1175，英文召回99.8298%；r512/T65536的2次漏选也均为英文。因此二者均未达到各类99.9%的门槛。'],['满rank与小Top-T','r896/Top1漏9次，Top256零漏选；后者仍有全V×896预览成本，因子加W超过现arena。'],['结论边界','只完成了有限校准搜索和四输入Eager GPU测速。未用新独立问题、未跑新RTL/FPGA；不据此更新冻结生产参数。']]
            g['decision']=f'首轮21点及12联合点已完成校准/GPU参考。最快通过拟议校准门槛的联合点{fastest["id"]}仍慢于同轮dense（{fastest["gpu_median_ms"]:.3f}ms vs {dense["wall_median_ms"]:.3f}ms）。当前有限扫描未找到同时满足校准门槛和本GPU参考速度优势的单方案；不改冻结生产实现。'
            g['next']='先评审训练词表支持集与全词表低秩预览的成本，决定是否改变候选来源/方法；若继续选型，须另锁配置并保留新最终问题组。GPU结果不能替代FPGA性能判断。'
        g['stage_status'].append(['有限联合扩展',f'校准{new_done}/12，GPU{new_timed}/12'])
        base='module_14_lm_head_v4/reports/hyperparameters_joint_20261023_r1/'
        for label,name in [('12点执行前锁定计划','PLAN.json'),('联合校准逐点结果','LOWRANK_CALIBRATION.json'),('联合点同轮GPU计时','GPU_BENCHMARK.json'),('联合点数值/计时复核','INDEPENDENT_REVIEW.json')]:
            if (joint_root/name).exists() and not any(e['href']==base+name for e in g['evidence']):g['evidence'].append(dict(label=label,href=base+name))
    entry_id='20261023-v4-hyperparameter-first-round' if final else '20261023-v4-hyperparameter-start'
    if not any(e['id']==entry_id for e in d['entries']):
        d['entries'].append(dict(id=entry_id,date='2026-10-23',title='实验8/9首轮校准与GPU参考测速完成' if final else '启动实验8/9：隔离配方、扩展主基与可变形状数值资格',status='已验证' if final else '进行中',importance='重要成果',summary=f'本轮只进行离线研究：聚类{counts["cluster"]["calibration"]}/23校准、低秩{counts["lowrank"]["calibration"]}/21校准；GPU分别{counts["cluster"]["timed"]}/23和{counts["lowrank"]["timed"]}/21。新独立测试/FPGA未做。',attempt='按冻结23+21配置，训练集拟合聚类、canonical W构造因子，仅用校准集选型。',problem='原聚类参考训练函数名变化导致两次预检导入失败；原文件保留。',solution='恢复到隔离副本并核对历史配方SHA，保留失败日志；原中心长列表前缀及扩展主基前128维复现。',verification='依据本轮PLAN/PROGRESS及真实完成结果；所有新增rank/中心数四夹具CPU/GPU全数组位证明，计时前候选/raw/token/score/CRC证明。未测步骤不宣称完成。',next='先完成校准与GPU参考，再锁有限联合点及新独立最终组。',tags=['v4','实验8','实验9','GPU','校准'],related=['20261023-v4-lowrank-hyperparameter-study-plan','20261022-v4-cluster-hyperparameter-study-plan'],evidence=[dict(label='实验8',href='doc/design/V4Validation.html#cluster-hyperparameters'),dict(label='实验9',href='doc/design/V4Validation.html#lowrank-hyperparameters'),dict(label='本轮真实状态',href='module_14_lm_head_v4/reports/hyperparameters_20261023_r1/PROGRESS.json')]))
    if joint_final and not any(e['id']=='20261023-v4-hyperparameter-joint-complete' for e in d['entries']):
        d['entries'].append(dict(id='20261023-v4-hyperparameter-joint-complete',date='2026-10-23',title='低秩12联合点完成：合格校准点尚无同轮GPU速度优势',status='已验证',importance='重要成果',summary='首轮44配置与12新联合点完成；合计7080次GPU计时。仅聚类受99369词训练支持集限制；低秩最快合格联合点r256/T98304零漏选，但18.617ms慢于同轮dense15.111ms。',attempt='固定12联合点，不改因子/算术，只用原校准集；保留原r128/T16384与dense控制，56组完整流水位证明后1680次交错计时。',problem='整体召回达到99.9%仍可能有分项不达标；更高rank和更大Top-T能减少漏选，却可能抵消速度和容量收益。',solution='分别画各rank下Top-T质量/速度，分开首轮与联合轮计时，并用原始观测/逐步hits/K和支持集独立复核。',verification='校准320问题/4775decode；首轮5400+联合1680计时及180+56完整流水数值证明通过；新独立测试、RTL与板卡未做。',next='保持生产冻结，先评审是否改变候选来源/方法及低秩预览成本；后续新配置仍需新独立问题与硬件资格。',tags=['v4','实验8','实验9','联合校准','GPU'],related=['20261023-v4-hyperparameter-first-round'],evidence=[dict(label='实验9联合曲线',href='doc/design/V4Validation.html#lowrank-hyperparameters'),dict(label='联合数值/计时复核',href='module_14_lm_head_v4/reports/hyperparameters_joint_20261023_r1/INDEPENDENT_REVIEW.json')]))
    assert d['entries'][:len(old)]==old
    v['updated']=snapshot;d['project']['updated']='2026-10-23';d['project']['phase']='v4实验8/9首轮校准及GPU参考已完成；联合搜索/新独立测试/FPGA待做。' if final else f'v4实验8/9离线执行中：{progress["stage"]}；不操作板卡。'
    for todo in d['todos']:
        if '核心研究实验9' in todo.get('text',''):todo.update(text='实验9首轮21点校准完成；GPU参考进度见实验页。下一步校准边界联合搜索、新问题锁定；不上板。',status='待验证')
        elif '核心研究实验8' in todo.get('text',''):todo.update(text='实验8首轮23点校准完成；核对训练支持集上界并完成GPU参考。新问题与FPGA未做。',status='待验证')
    d['presentation']['checks']='保留全部历史；实验8/9按本轮真实校准与GPU证据更新，FPGA空值。浏览器视觉预览未运行。'
    p=ROOT/'module_14_lm_head_v4/PROGRESS.json';pd=read(p);pd['updated']=snapshot;pd['hyperparameter_studies']=dict(state=progress['stage'],report='reports/hyperparameters_20261023_r1/PROGRESS.json',pid=progress['pid'],snapshot=snapshot,counts=counts,independent_test='NOT_RUN',board='NOT_RUN');pd['active_work']='NONE: first-round calibration/GPU benchmark completed' if final else f'Experiments8/9 {progress["stage"]}; verify actual run progress before continuing';pd['stage']='P6_HYPERPARAMETER_FIRST_ROUND_COMPLETE' if final else 'P6_HYPERPARAMETER_OFFLINE_RESEARCH';pd['next']='Review first-round bounds/Pareto, lock limited joint calibration search and fresh final problem groups. No FPGA operations.'
    for key in ['planned_cluster_hyperparameter_study','planned_lowrank_hyperparameter_study']:pd[key]['state']='FIRST_ROUND_CALIBRATION_GPU_COMPLETE' if final else 'STARTED_SEE_LIVE_REPORT'
    if jp:
        pd['hyperparameter_joint_study']=dict(state=joint_progress['stage'] if joint_progress else '待运行',report='reports/hyperparameters_joint_20261023_r1/PROGRESS.json',new_configurations=12,independent_test='NOT_RUN',board='NOT_RUN');pd['active_work']='NONE: first-round and joint calibration/GPU completed' if joint_final else 'Experiment9 locked12-point joint calibration/GPU in progress; check actual report';d['project']['phase']='v4实验8/9首轮44点及低秩12联合点校准/GPU完成；新独立测试与FPGA待做。' if joint_final else 'v4首轮44点完成，低秩12联合点继续离线校准/GPU；不上板。';pd['stage']='P6_HYPERPARAMETER_JOINT_COMPLETE' if joint_final else 'P6_HYPERPARAMETER_JOINT_RESEARCH'
        if joint_final:
            pd['planned_lowrank_hyperparameter_study']['state']='FIRST_ROUND_AND_JOINT_CALIBRATION_GPU_COMPLETE';pd['next']='Review fixed train-vote support bound and full-V preview cost before any new method/selection; no unbounded sweep, opened-test reuse or FPGA operations.'
            for todo in d['todos']:
                if todo.get('text','').startswith('实验9首轮'):todo.update(text='实验9：21首轮+12联合点校准/GPU已完成；有限扫描中合格单方案仍慢于同轮dense，后续先评审新方法，未做独立/硬件认证。',status='已验证')
                elif todo.get('text','').startswith('实验8首轮'):todo.update(text='实验8：23点校准/GPU及训练支持集上界复核完成；本投票配方仅调C/R/L无法通过分项门槛，未打开新独立测试。',status='已验证')
    p.write_text(json.dumps(pd,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    text=text[:m.start(2)]+'\n'+json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False).replace('<',r'\u003c')+'\n'+text[m.end(2):];path.write_text(text,encoding='utf-8')
    sys.path.insert(0,str(ROOT/'tools'));import render_v4_validation;render_v4_validation.render()
    print(json.dumps(dict(state=progress['stage'],counts=counts,history_entries=len(d['entries'])),ensure_ascii=False))
if __name__=='__main__':main()
