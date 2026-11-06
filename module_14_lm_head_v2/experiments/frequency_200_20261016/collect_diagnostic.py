"""Archive first 5ns diagnostic reports and compare against the original 10ns HLS."""
from pathlib import Path
import hashlib,json,re,shutil,xml.etree.ElementTree as ET
module=Path(__file__).resolve().parents[2]
run=module/'build/frequency_200_20261016'
new=run/'lm_head_v2_200_diagnostic/solution1/syn/report'
old=module/'build/lm_head_v2_csynth/solution1/syn/report'
out=module/'reports/frequency_200_20261016'
archive=out/'hls_5ns'
archive.mkdir(exist_ok=True)
log=(run/'csynth_200.log').read_text(encoding='utf-8-sig')
assert 'M14_200_CSYNTH_COMPLETE_NOT_TIMING_ACCEPTANCE' in log
assert not re.search(r'(?m)^ERROR:',log)
shutil.copy2(run/'csynth_200.log',out/'csynth_200.log')
def summarize(path):
    doc=ET.parse(path).getroot()
    return {'target_ns':float(doc.findtext('UserAssignments/TargetClockPeriod')),
      'uncertainty_ns':float(doc.findtext('UserAssignments/ClockUncertainty')),
      'estimated_ns':float(doc.findtext('PerformanceEstimates/SummaryOfTimingAnalysis/EstimatedClockPeriod')),
      'resources':{e.tag:int(e.text) for e in doc.findall('AreaEstimates/Resources/*')},
      'loops':[{e.tag:e.text for e in loop} | {'name':loop.tag} for loop in doc.findall('PerformanceEstimates/SummaryOfLoopLatency/*')],
      'latency':{e.tag:e.text for e in doc.findall('PerformanceEstimates/SummaryOfOverallLatency/*')}}
names=['lm_head_v2','p_anonymous_namespace_dot_product_rows',
 'p_anonymous_namespace_dot_product_rows_Pipeline_dot_word_loop','p_anonymous_namespace_reduce_rows',
 'p_anonymous_namespace_reduce_partials','p_anonymous_namespace_reduce_partials_Pipeline_reduce_16_to_8',
 'p_anonymous_namespace_reduce_partials_Pipeline_reduce_8_to_4','p_anonymous_namespace_reduce_partials_Pipeline_reduce_4_to_2',
 'p_anonymous_namespace_policy_and_argmax_Pipeline_policy_vocab_loop']
comparison={}
for name in names:
    assert (new/(name+'_csynth.xml')).is_file(),name
    for suffix in ['.xml','.rpt']:
        shutil.copy2(new/(name+'_csynth'+suffix),archive/(name+'_csynth'+suffix))
    comparison[name]={'new_5ns':summarize(new/(name+'_csynth.xml')),
                     'old_10ns':summarize(old/(name+'_csynth.xml'))}
baseline=json.loads((out/'baseline.json').read_text(encoding='utf-8'))
for relative,ident in baseline['source_files'].items():
    assert hashlib.sha256((module/relative).read_bytes()).hexdigest()==ident['current_sha256']
fmax=float(re.search(r'Estimated Fmax:\s*([\d.]+) MHz',log).group(1))
result={'date':'2026-10-16','timezone':'Asia/Shanghai','tool':'Vitis HLS 2021.1 build 3247384',
 'state':'CSYNTH_COMPLETED_ESTIMATED_TIMING_NOT_MET','csynth_completed':True,'tool_exit_code':0,
 'target_clock_mhz':200,'period_ns':5,'hls_uncertainty_ns':1.35,'effective_hls_budget_ns':3.65,
 'top_estimated_ns':comparison['lm_head_v2']['new_5ns']['estimated_ns'],'tool_estimated_Fmax_MHz':fmax,
 'estimated_5ns_met':False,'post_route_200MHz_verified':False,'board_access':False,'active_build_job':False,
 'error_lines':0,'warning_lines':len(re.findall(r'(?m)^WARNING:',log)),
 'timing_warning_count':len(re.findall(r'WARNING: \[HLS 200-871\]',log)),
 'ii_violation_warning_count':len(re.findall(r'WARNING: \[HLS 200-880\]',log)),
 'duration':{'csynth_elapsed_seconds':179.085,'total_elapsed_seconds':214.327,
             'cpu_user_seconds':114,'cpu_system_seconds':13,'peak_HLS_allocated_MB':662.630,
             'memory_note':'HLS allocated metric, not RSS or configured limit'},
 'source_unchanged_from_100MHz':True,'process_finished':'2026-10-16T19:25:45+08:00','comparison':comparison,
 'next':'Separate reduction layers/indices or improve local CE distribution while preserving FP32 tree; compare new HLS and full implementation.'}
(out/'diagnostic_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
files=[out/'csynth_200.log',out/'diagnostic_summary.json']+sorted(archive.glob('*'))
(out/'DIAGNOSTIC.sha256').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(out).as_posix()+'\n' for p in files),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='comparison'},ensure_ascii=True))
print(json.dumps(comparison,ensure_ascii=True))
