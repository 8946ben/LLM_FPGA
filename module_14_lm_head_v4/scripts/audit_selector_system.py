"""Independent offline topology and post-route audit. Never opens FPGA hardware."""
from pathlib import Path
import argparse, hashlib, json, re, zipfile
M=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def text(p):return p.read_text(encoding='utf-8-sig')
def topology(hw):
    p=hw/'implemented_bd.json';bd=json.loads(text(p))['design']
    assert bd['design_info']['validated']=='true'
    c=bd['components'];addr=bd['addressing']
    assert c['selector_0']['vlnv']=='user.org:hls:lm_head_v4_selector:4.0'
    ps=addr['/zynq_ultra_ps_e_0']['address_spaces']['Data']['segments']
    for name,offset in [('SEG_selector_0_Reg',0xA0000000),('SEG_calib_gpio_Reg',0xA0020000)]:
        assert int(ps[name]['offset'],0)==offset and ps[name]['range']=='64K'
    spaces=addr['/selector_0']['address_spaces']
    assert set(spaces)=={'Data_m_axi_plmem','Data_m_axi_histmem'}
    for space in [ps]+[v['segments'] for v in spaces.values()]:
        d=space['SEG_ddr4_0_C0_DDR4_ADDRESS_BLOCK']
        assert int(d['offset'],0)==0x400000000 and d['range']=='2G' and d.get('is_excluded')!='TRUE'
    for space in spaces.values():
        enabled=[v['address_block'] for v in space['segments'].values() if v.get('is_excluded')!='TRUE']
        assert enabled==['/ddr4_0/C0_DDR4_MEMORY_MAP/C0_DDR4_ADDRESS_BLOCK'],enabled
    for name in ('m_axi_plmem','m_axi_histmem'):
        assert int(c['selector_0']['interface_ports'][name]['base_address']['width'])==64
    def param(component,name):return c[component]['parameters'][name]['value']
    for name,value in [('C_GPIO_WIDTH','1'),('C_ALL_INPUTS','1'),('C_IS_DUAL','1'),('C_GPIO2_WIDTH','32'),('C_ALL_INPUTS_2','1')]:assert param('calib_gpio',name)==value
    assert int(param('selector_build_signature','CONST_VAL'),0)==0x4D345301
    assert param('selector_build_signature','CONST_WIDTH')=='32'
    assert param('axi_smc','NUM_SI')=='3' and param('axi_smc','NUM_MI')=='3'
    assert float(param('zynq_ultra_ps_e_0','PSU__CRL_APB__PL0_REF_CTRL__FREQMHZ'))==200
    create_log=text(M/'reports/selector_bd_create_r1_20261021.log')
    actual=re.search(r'^M14_V4_PL0_MHZ=([\d.]+)',create_log,re.M);assert actual
    actual_mhz=float(actual[1]);assert abs(actual_mhz-200)<.01
    assert param('ddr4_0','C0.DDR4_MemoryPart')=='MT40A512M16LY-075'
    assert param('ddr4_0','C0.DDR4_AxiAddressWidth')=='31'
    assert param('ddr4_0','C0.DDR4_AxiDataWidth')=='128'
    assert param('ddr4_0','C0.DDR4_DataWidth')=='32'
    assert int(bd['interface_ports']['pl_ddr_refclk']['parameters']['FREQ_HZ']['value'])==200000000
    links=[set(n['interface_ports']) for n in bd['interface_nets'].values()]
    for i,name in enumerate(('m_axi_plmem','m_axi_histmem'),1):assert {'selector_0/'+name,'axi_smc/S%02d_AXI'%i} in links
    assert {'axi_smc/M02_AXI','axi_cc_ddr/S_AXI'} in links
    assert {'axi_cc_ddr/M_AXI','ddr4_0/C0_DDR4_S_AXI'} in links
    assert not any('S_AXI_HP' in endpoint for link in links for endpoint in link)
    nets=[set(n['ports']) for n in bd['nets'].values()]
    assert any({'selector_build_signature/dout','calib_gpio/gpio2_io_i'}<=n for n in nets)
    reset=next(n for n in nets if 'calib_gate/Op1' in n)
    assert 'rst_ui_ddr/peripheral_aresetn' in reset and 'rst_pl_200M/peripheral_aresetn' not in reset
    xdc=M/'constraints/lm_head_v4_ddr4_pins.xdc'
    accepted=M.parent/'module_14_lm_head_v3_1/constraints/lm_head_v31_ddr4_pins.xdc'
    assert sha(xdc)==sha(accepted),'Changed accepted pin mapping'
    return dict(state='PASS_TOPOLOGY_ONLY',board='NOT_RUN',bd_sha256=sha(p),pin_sha256=sha(xdc),
      masters=2,address_width=64,compute_route='MIG_PL_DDR_ONLY',pl_ddr_base='0x400000000',
      clock_target_mhz=200,generated_ps_pll_actual_mhz=actual_mhz,
      clock_scope='Vivado generated configuration, not physical board measurement',
      signature='0x4D345301 private GPIO2, not public ABI/build',
      note='Structural audit only; not post-route STA/CDC or board DDR calibration')
def routed(hw):
    result=topology(hw)
    timing=text(hw/'timing.rpt');lines=timing.splitlines()
    i=next(i for i,s in enumerate(lines) if 'WNS(ns)' in s and 'WPWS(ns)' in s)
    values=next(s.split() for s in lines[i+1:i+6] if re.match(r'^\s*-?\d+\.\d+\s',s));assert len(values)==12
    checks={}
    for name in ('no_clock','constant_clock','unconstrained_internal_endpoints','multiple_clock','generated_clocks','loops','latch_loops'):
        found=re.search(r'checking '+name+r' \((\d+)\)',timing);assert found,name;checks[name]=int(found[1])
    cdc=text(hw/'cdc.rpt')
    counts={rule:{'severity':severity,'count':int(count)} for rule,severity,count in re.findall(r'^(CDC-\d+)\s+(Info|Warning|Critical)\s+(\d+)\s',cdc,re.M)}
    assert counts,'Missing CDC table'
    critical=sum(v['count'] for v in counts.values() if v['severity']=='Critical')
    unknown=[s for s in cdc.splitlines() if re.match(r'^\s*\d+\s+CDC-\d+\s+Warning',s) and not ('CDC-15' in s and 'dbg_hub/inst/' in s)]
    ct=text(hw/'check_timing.rpt');od=re.search(r'checking no_output_delay \((\d+)\)',ct);assert od
    reset_only=int(od[1])==1 and 'c0_ddr4_reset_n_0' in ct
    skew=text(hw/'bus_skew.rpt')
    slacks=[float(v) for v in re.findall(r'^\s*(?:Slow|Fast)\s+[\d.]+\s+[\d.]+\s+(-?[\d.]+)\s*$',skew,re.M)];assert slacks
    drc=text(hw/'drc.rpt')
    mig=re.findall(r'^\|\s*(MIG-\d+)\s*\|\s*(?:Warning|Critical Warning|Error)\s*\|',drc,re.M)
    severity={name:0 for name in ('Error','Critical Warning','Warning','Advisory')}
    for line in drc.splitlines():
        cols=[s.strip() for s in line.split('|')[1:-1]]
        if len(cols)==4 and cols[1] in severity and cols[-1].isdigit():severity[cols[1]]+=int(cols[-1])
    io=dict(s.split('=',1) for s in text(hw/'io_contract.txt').splitlines() if '=' in s)
    assert io==dict(reset_pin='AM5',reset_iostandard='LVCMOS12',reset_drive='8')
    clock=re.search(r'^clk_pl_0\s+\{[^}]+\}\s+([\d.]+)\s+([\d.]+)',timing,re.M);assert clock
    bit=hw/'m14_v4_system_wrapper.bit';xsa=hw/'m14_v4_single.xsa';bit_sha=sha(bit)
    with zipfile.ZipFile(xsa) as z:
        members=[n for n in z.namelist() if n.endswith('.bit')];assert len(members)==1
        assert hashlib.sha256(z.read(members[0])).hexdigest()==bit_sha,'XSA/bit mismatch'
    resources={};util=text(hw/'utilization.rpt')
    for key,label in [('lut','CLB LUTs'),('ff','CLB Registers'),('bram_tile','Block RAM Tile'),('dsp','DSPs')]:
        resources[key]=float(re.search(r'\|\s*'+re.escape(label)+r'\*?\s*\|\s*([\d.]+)',util)[1])
    result.update(wns_ns=float(values[0]),whs_ns=float(values[4]),wpws_ns=float(values[8]),
      setup_failing_endpoints=int(values[2]),hold_failing_endpoints=int(values[6]),pulse_width_failing_endpoints=int(values[10]),
      timing_checks=checks,cdc_rules=counts,cdc_critical=critical,cdc_unknown_warnings=unknown,
      drc_severity_counts=severity,mig_warnings=mig,bus_skew_min_slack_ns=min(slacks),reset_io=io,
      untimed_output_ports=['c0_ddr4_reset_n_0'] if reset_only else [],
      untimed_output_note='Vendor asynchronous MIG reset only; not timed DDR data/control lane',
      sta_clock_period_ns=float(clock[1]),resources=resources,bit_sha256=bit_sha,xsa_sha256=sha(xsa),xsa_bit_matches=True)
    passed=all(result[k]>=0 for k in ('wns_ns','whs_ns','wpws_ns')) and all(result[k]==0 for k in ('setup_failing_endpoints','hold_failing_endpoints','pulse_width_failing_endpoints'))
    passed=passed and not any(checks.values()) and not severity['Error'] and not severity['Critical Warning'] and critical==0 and not unknown and not mig and min(slacks)>=0
    passed=passed and (int(od[1])==0 or reset_only) and abs(float(clock[1])-5)<.001 and 'All user specified timing constraints are met.' in timing
    result['state']='PASS_OFFLINE_SYSTEM' if passed else 'FAIL_OFFLINE_SYSTEM'
    result['note']='Complete offline system implementation; not RTL functional, software package, board or release acceptance'
    result['evidence_sha256']={p.name:sha(p) for p in hw.iterdir() if p.is_file() and p.suffix in ('.rpt','.txt')}
    return result
def main():
    p=argparse.ArgumentParser();p.add_argument('--hardware',default='reports/board_v4_20261021/hardware_r2');p.add_argument('--topology-only',action='store_true');args=p.parse_args()
    hw=M/args.hardware
    result=topology(hw) if args.topology_only else routed(hw)
    out=hw.parent/('topology_audit_r2.json' if args.topology_only else 'hardware_audit_r2.json')
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2));assert result['state'].startswith('PASS'),result
if __name__=='__main__':main()
