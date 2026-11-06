"""Fail closed on incomplete timing, DRC errors or an XSA/bit mismatch."""
from pathlib import Path
import hashlib, json, re, zipfile

m=Path(__file__).resolve().parents[2]
out=m/'reports/board200_20261019'
hw=out/'hardware'

def audit():
    timing=(hw/'timing.rpt').read_text(encoding='utf-8-sig')
    lines=timing.splitlines()
    i=next(i for i,s in enumerate(lines) if 'WNS(ns)' in s and 'WPWS(ns)' in s)
    values=next(s.split() for s in lines[i+1:i+6] if re.match(r'^\s*-?\d+\.\d+\s',s))
    assert len(values)==12
    checks={}
    for name in ('no_clock','constant_clock','unconstrained_internal_endpoints','multiple_clock','generated_clocks','loops','latch_loops'):
        found=re.search(r'checking '+name+r' \((\d+)\)',timing)
        assert found, 'Missing timing check: '+name
        checks[name]=int(found.group(1))
    drc=(hw/'drc.rpt').read_text(encoding='utf-8-sig')
    severity={name:0 for name in ('Error','Critical Warning','Warning','Advisory')}
    for line in drc.splitlines():
        cols=[s.strip() for s in line.split('|')[1:-1]]
        if len(cols)==4 and cols[1] in severity and cols[-1].isdigit(): severity[cols[1]]+=int(cols[-1])
    clock=re.search(r'^clk_pl_0\s+\{[^}]+\}\s+([\d.]+)\s+([\d.]+)',timing,re.M)
    assert clock
    log=(m/'build/board200_20261019/launch/create_bd.stdout.log').read_text(encoding='utf-8-sig')
    actual=float(re.search(r'^M14_V2_PL0_ACTUAL_MHZ=([\d.]+)',log,re.M).group(1))
    bit=hw/'m14_v2_system_wrapper.bit'; xsa=hw/'m14_v2_single.xsa'
    bit_sha=hashlib.sha256(bit.read_bytes()).hexdigest()
    with zipfile.ZipFile(xsa) as z:
        embedded=[name for name in z.namelist() if name.endswith('.bit')]
        assert len(embedded)==1
        assert hashlib.sha256(z.read(embedded[0])).hexdigest()==bit_sha,'XSA/bit mismatch'
    util=(hw/'utilization.rpt').read_text(encoding='utf-8-sig')
    resources={}
    for key,label in (('lut','CLB LUTs'),('ff','CLB Registers'),('bram_tile','Block RAM Tile'),('dsp','DSPs')):
        resources[key]=float(re.search(r'\|\s*'+re.escape(label)+r'\*?\s*\|\s*([\d.]+)',util).group(1))
    result=dict(wns_ns=float(values[0]),whs_ns=float(values[4]),wpws_ns=float(values[8]),
        setup_failing_endpoints=int(values[2]),hold_failing_endpoints=int(values[6]),pulse_width_failing_endpoints=int(values[10]),
        timing_checks=checks,drc_severity_counts=severity,sta_clock_period_ns=float(clock.group(1)),
        configured_clock_mhz=actual,resources=resources,bit_sha256=bit_sha,xsa_embedded_bit_matches=True)
    passed=(all(result[key]>=0 for key in ('wns_ns','whs_ns','wpws_ns'))
        and all(result[key]==0 for key in ('setup_failing_endpoints','hold_failing_endpoints','pulse_width_failing_endpoints'))
        and all(v==0 for v in checks.values()) and severity['Error']==0 and severity['Critical Warning']==0
        and abs(result['sta_clock_period_ns']-5)<.001 and abs(actual-200)<.01
        and 'All user specified timing constraints are met.' in timing)
    result['state']='PASS' if passed else 'FAIL'
    (out/'hardware_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    assert passed,result
    return result

if __name__=='__main__': print(json.dumps(audit(),indent=2))
