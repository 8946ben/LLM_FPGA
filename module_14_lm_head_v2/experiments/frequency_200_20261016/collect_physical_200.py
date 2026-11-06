"""Audit routed reports, retaining timing failures and warning counts honestly."""
from pathlib import Path
import hashlib, json, re, shutil

MODULE = Path(__file__).resolve().parents[2]
ROOT = MODULE / 'reports/frequency_200_20261016/reduce_layers'
OUT = ROOT / 'physical_200'
LAUNCH = MODULE / 'build/frequency_200_20261016/reduce_layers/vivado_launch'


def main():
    text = (OUT / 'post_route_timing.rpt').read_text(encoding='utf-8-sig')
    lines = text.splitlines()
    header = next(i for i,s in enumerate(lines) if 'WNS(ns)' in s and 'WPWS(ns)' in s)
    values = next(s.split() for s in lines[header+1:header+6]
                  if re.match(r'^\s*-?\d+\.\d+\s', s))
    assert len(values) == 12, values
    counts = {}
    for name in ['no_clock','constant_clock','unconstrained_internal_endpoints','multiple_clock',
                 'generated_clocks','loops','latch_loops']:
        match = re.search(r'checking '+name+r' \((\d+)\)', text)
        counts[name] = int(match.group(1)) if match else None
    clock = re.search(r'^clk_pl_0\s+\{[^}]+\}\s+([\d.]+)\s+([\d.]+)',text,re.M)
    assert clock, 'Expected PL clock absent'
    drc = (OUT / 'post_route_drc.rpt').read_text(encoding='utf-8-sig')
    severity = {'Error':0,'Critical Warning':0,'Warning':0,'Advisory':0}
    for line in drc.splitlines():
        cols = [s.strip() for s in line.split('|')[1:-1]]
        if len(cols) == 4 and cols[1] in severity and cols[-1].isdigit():
            severity[cols[1]] += int(cols[-1])
    create = (LAUNCH / 'create.stdout.log').read_text(encoding='utf-8-sig')
    actual = re.search(r'^M14_V2_PL0_ACTUAL_MHZ=([\d.]+)',create,re.M)
    assert actual
    util = (OUT / 'post_route_utilization.rpt').read_text(encoding='utf-8-sig')
    resources = {}
    for key, label in [('lut','CLB LUTs'),('ff','CLB Registers'),('bram_tile','Block RAM Tile'),('dsp','DSPs')]:
        match = re.search(r'\|\s*'+re.escape(label)+r'\*?\s*\|\s*([\d.]+)',util)
        resources[key] = float(match.group(1)) if match else None
    assert all(v is not None for v in resources.values()), resources
    result = {'phase':'full single-module BD post-route; not board validation',
              'tool':'Vivado 2021.1', 'nominal_target_mhz':200,
              'ps_actual_configured_mhz':float(actual.group(1)),
              'sta_clock_period_ns':float(clock.group(1)),
              'sta_clock_mhz':float(clock.group(2)),
              'wns_ns':float(values[0]),'tns_ns':float(values[1]),
              'setup_failing_endpoints':int(values[2]),
              'whs_ns':float(values[4]),'ths_ns':float(values[5]),
              'hold_failing_endpoints':int(values[6]),
              'wpws_ns':float(values[8]),'tpws_ns':float(values[9]),
              'pulse_width_failing_endpoints':int(values[10]),
              'timing_checks':counts,'drc_severity_counts':severity,
              'post_route_resources':resources,
              'worst_setup_path':{
                  'source':re.search(r'^  Source:\s*(.+)$',text,re.M).group(1),
                  'destination':re.search(r'^  Destination:\s*(.+)$',text,re.M).group(1),
                  'data_path_ns':float(re.search(r'Data Path Delay:\s*([\d.]+)ns',text).group(1))},
              'board_verified':False,'bitstream_generated':False}
    result['timing_closed'] = (
        result['wns_ns'] >= 0 and result['whs_ns'] >= 0 and result['wpws_ns'] >= 0
        and all(result[k] == 0 for k in ['setup_failing_endpoints','hold_failing_endpoints','pulse_width_failing_endpoints'])
        and all(v == 0 for v in counts.values())
        and severity['Error'] == 0 and severity['Critical Warning'] == 0
        and abs(result['sta_clock_period_ns']-5.0) < 0.001
        and 'All user specified timing constraints are met.' in text)
    result['state'] = 'ROUTED_200MHZ_TIMING_CLOSED' if result['timing_closed'] else 'ROUTED_RESULTS_REQUIRE_FURTHER_WORK'
    for name in ['create.execution.json','build.execution.json','create.stdout.log','build.stdout.log']:
        p = LAUNCH / name
        if p.exists(): shutil.copy2(p, OUT / name)
    (ROOT / 'physical_summary.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    files = [p for p in OUT.rglob('*') if p.is_file()] + [ROOT / 'physical_summary.json']
    (ROOT / 'PHYSICAL_SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+
        p.relative_to(ROOT).as_posix()+'\n' for p in sorted(files)),encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__ == '__main__': main()
