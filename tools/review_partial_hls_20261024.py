"""Inspect real 2022.2 synthesis XML/log/RTL ports, not a speed benchmark."""
from pathlib import Path
import hashlib,json,re,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'module_14_lm_head_v4/reports/partial_hw_20261024_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def textdict(node):return {x.tag:x.text for x in node} if node is not None else {}
def main():
    global R
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--revision',choices=['r1','r2','r3'],default='r1');args=parser.parse_args()
    if args.revision!='r1':R=R/args.revision
    base=R/'remote_hls';log=base/'csynth.log';content=log.read_text(encoding='utf-8',errors='replace')
    assert 'PARTIAL_PROTO_csynth=PASS' in content,'Wrapper return0 is not sufficient'
    reports=base/'syn/report';xmls=sorted(reports.glob('*_csynth.xml'));assert xmls
    units=[]
    for p in xmls:
        x=ET.parse(p).getroot();loops=[]
        for n in x.findall('.//LoopLatency'):loops.append(textdict(n))
        units.append(dict(unit=p.stem[:-7] if p.stem.endswith('_csynth') else p.stem,
            assignments=textdict(x.find('UserAssignments')),timing=textdict(x.find('PerformanceEstimates/SummaryOfTimingAnalysis')),
            latency=textdict(x.find('PerformanceEstimates/SummaryOfOverallLatency')),loops=loops,
            resources=textdict(x.find('AreaEstimates/Resources')),available=textdict(x.find('AreaEstimates/AvailableResources')),sha256=sha(p)))
    top=next(x for x in units if x['unit']=='lm_head_v4_partial_proto');assert top['assignments']['Part']=='xczu9eg-ffvb1156-2-i'
    root=ET.parse(reports/'lm_head_v4_partial_proto_csynth.xml').getroot();ports=[textdict(n) for n in root.findall('InterfaceSummary/RtlPorts')]
    axi={p['name']:int(p['Bits']) for p in ports if p.get('name','').startswith('m_axi_') and p.get('name','').endswith(('_ARADDR','_AWADDR','_RDATA','_WDATA'))}
    assert axi,'Need generated RTL port evidence'
    resources={k:int(v) for k,v in top['resources'].items()};capacity={k:int(v) for k,v in top['available'].items()}
    fits=all(v<=capacity[k] for k,v in resources.items());estimate=float(top['timing']['EstimatedClockPeriod']);period=float(top['assignments']['TargetClockPeriod']);uncertainty=float(top['assignments']['ClockUncertainty'])
    budget=period-uncertainty;clock_estimate_pass=estimate<=budget+0.0005
    relevant=[u for u in units if any(key in u['unit'] for key in ['select_channels','partial_preview','preview_beat','emit_preview','radix','candidate_lane','dot_product','reduce_rows','candidate_dataflow'])]
    warnings=[line for line in content.splitlines() if any(k in line for k in ['WARNING:','Unable to enforce','burst read','burst write','Burst read','Burst write'])]
    pipelines=[dict(target_ii=int(a),achieved_ii=int(b),depth=int(c),loop=d) for a,b,c,d in re.findall(r'Target II = (\d+), Final II = (\d+), Depth = (\d+), loop \'([^\']+)\'',content)]
    result=dict(state='HLS_SYNTHESIS_COMPLETE_REQUIRES_RTL_QUALIFICATION',tool='Vitis_HLS2022.2_Linux_STHL',
        generated_axi_port_widths=axi,top=top,stage_units=relevant,all_units=units,resources_fit_device=fits,
        resource_percent={k:100*v/capacity[k] if capacity[k] else (0 if v==0 else None) for k,v in resources.items()},
        estimate_ns=estimate,period_ns=period,uncertainty_ns=uncertainty,internal_budget_ns=budget,estimate_within_internal_budget=clock_estimate_pass,
        warnings_and_burst_inference=warnings,log_sha256=sha(log),review_script_sha256=sha(Path(__file__)),
        pipeline_results=pipelines,
        claims=dict(real_200MHz_STA='NOT_RUN',RTL='NOT_RUN',board='NOT_RUN',decode_speed='NOT_MEASURED',TTFT='NOT_MEASURED'),
        limitations=['CSim unbounded software streams do not prove bounded FIFO liveness. Exact dataflow now shares two top AXI masters; RTL must verify arbitration/backpressure.',
            'Prototype always writes full raw preview workspace; production traffic differs from stageB minimum. Source read-beat counter is scheduled count, not measured AXI.',
            'Undefined overall latency stays undefined; no FPGA token/s inferred from GPU, XML or scalar multiplication counts.',
            '2022.2 results do not replace or inherit old2021.1 implementation qualification.'])
    (R/'HLS_QUALIFICATION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(resources=resources,clock_estimate_ns=estimate,budget_ns=budget,ports=axi,units=len(units),top_latency=top['latency'])))
if __name__=='__main__':main()
