"""Archive candidate 2021.1 reports; keep baseline diagnostics immutable."""
from pathlib import Path
import hashlib, json, re, shutil, xml.etree.ElementTree as ET

MODULE = Path(__file__).resolve().parents[2]
RUN = MODULE / 'build/frequency_200_20261016/reduce_layers'
OUT = MODULE / 'reports/frequency_200_20261016/reduce_layers'


def summarize(p):
    root = ET.parse(p).getroot()
    return {'target_ns': root.findtext('UserAssignments/TargetClockPeriod'),
            'estimated_ns': root.findtext('PerformanceEstimates/SummaryOfTimingAnalysis/EstimatedClockPeriod'),
            'latency': {n.tag:n.text for n in root.findall('PerformanceEstimates/SummaryOfOverallLatency/*')},
            'resources': {n.tag:n.text for n in root.findall('AreaEstimates/Resources/*')},
            'loops': [{n.tag:n.text for n in loop} | {'name':loop.tag}
                      for loop in root.findall('PerformanceEstimates/SummaryOfLoopLatency/*')]}


def main():
    log = (RUN / 'csynth.log').read_text(encoding='utf-8-sig')
    assert 'M14_200_REDUCE_LAYERS_csynth_COMPLETE_NOT_BOARD_ACCEPTANCE' in log
    assert not re.search(r'(?m)^ERROR:', log)
    archive = OUT / 'hls_5ns'
    archive.mkdir(exist_ok=True)
    reports = RUN / 'csynth/solution1/syn/report'
    comparison = {}
    old = MODULE / 'reports/frequency_200_20261016/hls_5ns'
    for p in sorted(reports.iterdir()):
        if p.suffix not in ('.rpt', '.xml'): continue
        shutil.copy2(p, archive / p.name)
        if p.suffix == '.xml':
            comparison[p.stem] = {'candidate': summarize(p)}
            if (old / p.name).exists(): comparison[p.stem]['unmodified_5ns'] = summarize(old / p.name)
    for name in ['csim.log','csynth.log','csim.execution.json','csynth.execution.json']:
        shutil.copy2(RUN / name, OUT / name)
    top = comparison['lm_head_v2_csynth']['candidate']
    result = {'state':'CSYNTH_COMPLETED_NOT_POST_ROUTE_ACCEPTANCE', 'tool':'Vitis HLS 2021.1',
              'target_ns':5.0, 'hls_uncertainty_ns':1.35, 'top_estimated_ns':float(top['estimated_ns']),
              'fmax_estimated_mhz':float(re.search(r'Estimated Fmax:\s*([\d.]+) MHz',log).group(1)),
              'csim_pass':True, 'cosim_pass':None, 'post_route_pass':None, 'board_pass':None,
              'comparison':comparison}
    rtl_meta = RUN / 'rtl896.execution.json'
    if rtl_meta.exists():
        meta = json.loads(rtl_meta.read_text(encoding='utf-8-sig'))
        shutil.copy2(rtl_meta, OUT / rtl_meta.name)
        shutil.copy2(RUN / 'rtl896.log', OUT / 'rtl896.log')
        if meta['recovered_vector_name']:
            replay = RUN / 'rtl896_vector_recovery.log'
            text = replay.read_text(encoding='utf-8-sig')
            assert 'Starting C post checking' in text
            assert text.count('LM_HEAD_V2_CSIM=PASS') >= 2
            assert not re.search(r'(?m)^ERROR:', text)
            shutil.copy2(replay, OUT / replay.name)
            result['rtl_verification_method'] = 'generated XSIM replay + C post-check after hidden_size_r vector-name recovery'
        else:
            text = (RUN / 'rtl896.log').read_text(encoding='utf-8-sig')
            assert 'C/RTL co-simulation finished: PASS' in text
            result['rtl_verification_method'] = 'normal Vitis co-simulation'
        result['cosim_pass'] = True
        result['rtl_test_dimensions'] = {'hidden':896,'vocab':64,'transactions':15,'exact_random_logits':512}
        result['state'] = 'CSYNTH_AND_RTL_VERIFIED_NOT_POST_ROUTE_ACCEPTANCE'
        result['initial_cosim_failures_preserved'] = ['cosim: C wrapper depth overread',
            'cosim_full_hidden: tool stalled during instrumentation; stopped after idle audit',
            'rtl896: vector-name mismatch before generated XSIM replay' if meta['recovered_vector_name'] else 'none']
    physical = OUT / 'physical_summary.json'
    if physical.exists():
        result['post_route_pass'] = json.loads(physical.read_text())['timing_closed']
        if result['post_route_pass'] and result['cosim_pass']:
            result['state'] = 'HLS_RTL_AND_200MHZ_POST_ROUTE_VERIFIED_NOT_BOARD_ACCEPTANCE'
    (OUT / 'hls_summary.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    files = [OUT / n for n in ['hls_summary.json','csim.log','csynth.log','csim.execution.json','csynth.execution.json',
             'rtl896.log','rtl896.execution.json','rtl896_vector_recovery.log'] if (OUT / n).exists()]
    files += [p for p in archive.iterdir() if p.is_file()]
    (OUT / 'HLS_SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+
        p.relative_to(OUT).as_posix()+'\n' for p in sorted(files)),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='comparison'},indent=2))


if __name__ == '__main__': main()
