"""Extract existing 100 MHz evidence for a 200 MHz diagnostic; no EDA/board calls."""
from pathlib import Path
import hashlib,json,re

module=Path(__file__).resolve().parents[2]
root=module.parent
report=module/'reports/board_build/post_route_timing_summary.rpt'
timing=report.read_text(encoding='utf-8')
slack=float(re.search(r'Slack \(MET\)\s*:\s*([\d.]+)ns',timing).group(1))
period=float(re.search(r'Requirement:\s*([\d.]+)ns',timing).group(1))
delay=re.search(r'Data Path Delay:\s*([\d.]+)ns\s+\(logic ([\d.]+)ns .*?route ([\d.]+)ns',timing)
assert delay, 'Missing data/logic/route timing fields in baseline report'
nets=[{'fanout':int(f),'delay_ns':float(d)} for f,d in re.findall(r'net \(fo=(\d+), routed\)\s+([\d.]+)',timing)]
dominant=max(nets,key=lambda n:n['delay_ns'])
meta=json.loads((module/'reports/20261010_ACCEPTANCE_METADATA.json').read_text(encoding='utf-8'))
ms=meta['strict_summary']['performance']['ip_ms_median']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source_files=['src/lm_head_v2.cpp','include/lm_head_v2.hpp','drivers/lm_head_v2_driver.h','drivers/lm_head_v2_mmio.c']
accepted=root/'deliverables/20261010_M14_V2_r1/M14_V2_20261010_r1/module_14_lm_head_v2'
identities={relative:{'current_sha256':sha(module/relative),'accepted_sha256':sha(accepted/relative)} for relative in source_files}
assert all(v['current_sha256']==v['accepted_sha256'] for v in identities.values())
tools=[r'G:\Xilinx\Vitis_HLS\2021.1\bin\vitis_hls.bat',r'G:\Xilinx\Vivado\2021.1\bin\vivado.bat']
tool_paths=[{'path':p,'exists':Path(p).is_file()} for p in tools]
tools_available=all(p['exists'] for p in tool_paths)
result={'date':'2026-10-16','timezone':'Asia/Shanghai','scope':'independent M14; 200 MHz analysis; no full-model integration',
 'state':'BASELINE_EXTRACTED_TOOLS_AVAILABLE' if tools_available else 'BASELINE_EXTRACTED_AWAITING_TOOLS','target_clock_mhz':200,'target_period_ns':5,
 'source_files':identities,'production_sources_match_accepted':True,
 'baseline':{'clock_mhz':100,'period_ns':period,'WNS_ns':slack,'data_path_ns':float(delay[1]),
             'logic_ns':float(delay[2]),'route_ns':float(delay[3]),'dominant_net':dominant,'ip_median_ms':ms,
             'timing_report':report.relative_to(root).as_posix(),'timing_report_sha256':sha(report)},
 'estimates_not_measurements':{'WNS_200_fixed_path_ns':round(slack+5-period,6),
    'ip_ms_if_same_cycles':ms/2,'weight_only_no_bubble_min_ms':272269312/(16*200000000)*1000,
    'weight_bandwidth_required_GB_s':272269312/(ms/2/1000)/1e9,'axi_128bit_200MHz_peak_GB_s':3.2},
 'diagnostic':{'clock_period_ns':5,'hls_uncertainty_ns':1.35,'input_source':'unchanged production C++/header',
               'HLS_executed':False,'RTL_cosim_executed':False,'Vivado_executed':False,'board_access':False,
               'active_build_job':False,'existing_build_overwrite':False},
 'tool_environment':{'paths':tool_paths,'currently_available':tools_available,
                     'initial_probe_missing_20261016':True,'user_response':'会恢复 G: 工具盘；后续路径已实测可见' if tools_available else '会恢复 G: 工具盘；尚不可见'},
 'implementation_hypotheses':[
    {'id':'A','change':'5ns HLS scheduling and physical optimization with unchanged arithmetic','status':'not run'},
    {'id':'A2','change':'placement-aware replication/localization of high-fanout CE drivers','status':'not implemented'},
    {'id':'B','change':'compare reduction-side local control/staging or lane-banked storage','status':'not implemented'}],
 'unchanged_contract':['H8/V1','16-slot interleave','FP32 separate multiply/add rounding','adjacent final lane tree','canonical BF16 inputs'],
 'host_followups':['clock/build identity','PL0/HP2/SmartConnect/reset','ip_seconds_100mhz conversion','matching bit/XSA/psu_init/ELF','strict checker and real wall timer']}
out=module/'reports/frequency_200_20261016/baseline.json'
diagnostic=out.parent/'diagnostic_summary.json'
if diagnostic.is_file():
    current=json.loads(diagnostic.read_text(encoding='utf-8'))
    result['state']='BASELINE_AND_FIRST_DIAGNOSTIC_CAPTURED'
    result['diagnostic'].update(HLS_executed=current['csynth_completed'],HLS_completed=current['csynth_completed'],
        estimated_5ns_met=current['estimated_5ns_met'],result='diagnostic_summary.json',active_build_job=False)
    result['implementation_hypotheses'][0]['status']='HLS diagnostic completed; estimate below target; physical implementation not run'
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=True))
