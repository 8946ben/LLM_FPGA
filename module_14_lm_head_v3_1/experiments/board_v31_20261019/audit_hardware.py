"""Fail closed on incomplete timing, DRC errors or an XSA/bit mismatch."""
from pathlib import Path
import hashlib, json, re, zipfile

m=Path(__file__).resolve().parents[2]
out=m/'reports/board_v31_20261019'
hw=out/'hardware'

def audit():
    bd_path=hw/'implemented_bd.json'
    bd=json.loads(bd_path.read_text(encoding='utf-8-sig'))['design']
    addresses=bd['addressing']
    spaces=[addresses['/zynq_ultra_ps_e_0']['address_spaces']['Data']]
    hls_spaces=addresses['/lm_head_v2_0']['address_spaces']
    spaces.extend(hls_spaces['Data_'+n] for n in ('m_axi_hidden','m_axi_weight','m_axi_history','m_axi_logits'))
    for space in spaces:
        seg=space['segments']['SEG_ddr4_0_C0_DDR4_ADDRESS_BLOCK']
        assert int(seg['offset'],0)==0x400000000 and seg['range']=='2G'
        assert seg.get('is_excluded')!='TRUE'
    for space in spaces[1:]:
        assert all(space['segments'][name]['is_excluded']=='TRUE' for name in ('SEG_calib_gpio_Reg','SEG_lm_head_v2_0_Reg'))
    assert bd['components']['calib_gpio']['parameters']['C_GPIO_WIDTH']['value']=='1'
    refclk=bd['interface_ports']['pl_ddr_refclk']['parameters']['FREQ_HZ']['value']
    assert int(refclk)==200000000
    reset=next(n['ports'] for n in bd['nets'].values() if 'calib_gate/Op1' in n['ports'])
    assert 'rst_ui_ddr/peripheral_aresetn' in reset and 'rst_pl_200M/peripheral_aresetn' not in reset
    links=[set(n['interface_ports']) for n in bd['interface_nets'].values()]
    for i,name in enumerate(('m_axi_hidden','m_axi_weight','m_axi_history','m_axi_logits'),1):
        assert {'lm_head_v2_0/'+name,'axi_smc/S%02d_AXI'%i} in links
    assert {'axi_smc/M02_AXI','axi_cc_ddr/S_AXI'} in links
    assert {'axi_cc_ddr/M_AXI','ddr4_0/C0_DDR4_S_AXI'} in links
    assert not any('S_AXI_HP' in endpoint for link in links for endpoint in link)
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
    cdc=(hw/'cdc.rpt').read_text(encoding='utf-8-sig')
    cdc_counts={rule:{'severity':severity,'count':int(count)} for rule,severity,count in
                re.findall(r'^(CDC-\d+)\s+(Info|Warning|Critical)\s+(\d+)\s',cdc,re.M)}
    assert cdc_counts, 'Missing CDC summary'
    cdc_critical=sum(v['count'] for v in cdc_counts.values() if v['severity']=='Critical')
    # Vendor debug FIFO enable structures are the only accepted CDC warnings.
    cdc_unknown_warnings=[s for s in cdc.splitlines() if re.match(r'^\s*\d+\s+CDC-\d+\s+Warning',s)
                          and not ('CDC-15' in s and 'dbg_hub/inst/' in s)]
    ct=(hw/'check_timing.rpt').read_text(encoding='utf-8-sig')
    output_delays=re.search(r'checking no_output_delay \((\d+)\)',ct)
    assert output_delays
    reset_only=(int(output_delays[1])==1 and 'c0_ddr4_reset_n_0' in ct)
    skew=(hw/'bus_skew.rpt').read_text(encoding='utf-8-sig')
    skew_slacks=[float(v) for v in re.findall(r'^\s*(?:Slow|Fast)\s+[\d.]+\s+[\d.]+\s+(-?[\d.]+)\s*$',skew,re.M)]
    assert skew_slacks, 'Missing bus-skew checks'
    drc=(hw/'drc.rpt').read_text(encoding='utf-8-sig')
    mig_warnings=re.findall(r'^\|\s*(MIG-\d+)\s*\|\s*(?:Warning|Critical Warning|Error)\s*\|',drc,re.M)
    io_contract=dict(line.split('=',1) for line in (hw/'io_contract.txt').read_text(encoding='utf-8-sig').splitlines() if '=' in line)
    assert io_contract==dict(reset_pin='AM5',reset_iostandard='LVCMOS12',reset_drive='8')
    severity={name:0 for name in ('Error','Critical Warning','Warning','Advisory')}
    for line in drc.splitlines():
        cols=[s.strip() for s in line.split('|')[1:-1]]
        if len(cols)==4 and cols[1] in severity and cols[-1].isdigit(): severity[cols[1]]+=int(cols[-1])
    clock=re.search(r'^clk_pl_0\s+\{[^}]+\}\s+([\d.]+)\s+([\d.]+)',timing,re.M)
    assert clock
    log=(m/'build/board_v31_20261019/launch/create_bd.stdout.log').read_text(encoding='utf-8-sig')
    actual_match=re.search(r'^M14_V31_PL0_MHZ=([\d.]+)',log,re.M)
    assert actual_match, 'Missing configured PL0 frequency marker'
    actual=float(actual_match.group(1))
    assert float(bd['components']['zynq_ultra_ps_e_0']['parameters']['PSU__CRL_APB__PL0_REF_CTRL__FREQMHZ']['value'])==200
    bit=hw/'m14_v31_system_wrapper.bit'; xsa=hw/'m14_v31_single.xsa'
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
        cdc_rules=cdc_counts,cdc_critical=cdc_critical,cdc_unknown_warnings=cdc_unknown_warnings,
        mig_warnings=mig_warnings,reset_io=io_contract,
        bus_skew_min_slack_ns=min(skew_slacks),
        untimed_output_ports=['c0_ddr4_reset_n_0'] if reset_only else [],
        untimed_output_note='MIG-generated asynchronous DRAM reset; not a clocked DDR data/control lane',
        configured_clock_mhz=actual,resources=resources,bit_sha256=bit_sha,xsa_embedded_bit_matches=True)
    result['implemented_bd_sha256']=hashlib.sha256(bd_path.read_bytes()).hexdigest()
    result['pin_constraints_sha256']=hashlib.sha256((m/'constraints/lm_head_v31_ddr4_pins.xdc').read_bytes()).hexdigest()
    result['bd_contract']='PASS: common system window, PL DDR-only HLS route, one-bit calibration GPIO and UI-domain reset'
    passed=(all(result[key]>=0 for key in ('wns_ns','whs_ns','wpws_ns'))
        and all(result[key]==0 for key in ('setup_failing_endpoints','hold_failing_endpoints','pulse_width_failing_endpoints'))
        and all(v==0 for v in checks.values()) and severity['Error']==0 and severity['Critical Warning']==0
        and cdc_critical==0 and not cdc_unknown_warnings and not mig_warnings and min(skew_slacks)>=0
        and (int(output_delays[1])==0 or reset_only)
        and abs(result['sta_clock_period_ns']-5)<.001 and abs(actual-200)<.01
        and 'All user specified timing constraints are met.' in timing)
    result['state']='PASS' if passed else 'FAIL'
    (out/'hardware_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    assert passed,result
    return result

if __name__=='__main__': print(json.dumps(audit(),indent=2))
