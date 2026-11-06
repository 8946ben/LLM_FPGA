"""Review r4 static reports and independently evaluate DSP control cones."""
from pathlib import Path
import re,json,hashlib,itertools,datetime
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'module_14_lm_head_v4/reports/d64_system_200m_20261106_r4'
H=R/'terminal_collection_r1/module_14_lm_head_v4/reports/d64_system_200m_20261106_r4/hardware'
N=ROOT/'module_14_lm_head_v4/reports/d64_postroute_audit_20261106_r1/collected/netlist'
def verilog_int(s):
 if "'" not in s:return int(s,0)
 _,s=s.split("'",1);return int(s[1:],{'b':2,'h':16,'d':10}[s[0].lower()])
def parse_cones():
 nodes={};dsps={};bits={}
 for line in (N/'dsp_cones.tsv').read_text().splitlines():
  row=line.split('\t');kind=row[0]
  if kind=='DSP':dsps[row[1]]=dict(preg=int(row[2]),opmodereg=int(row[3]),invert=verilog_int(row[4]))
  elif kind=='BIT':bits.setdefault(row[1],{})[int(row[2])]=row[3]
  elif kind=='NODE':
   node=dict(ref=row[2],cell=row[3],init=row[4],inputs=dict(x.split('=',1) for x in row[5].split(',') if x))
   assert row[1] not in nodes;nodes[row[1]]=node
  elif kind=='LEAF':assert False,('Missing/ambiguous driver',row)
  else:assert False,row
 def inputs(n):return nodes[n]['inputs']
 def leaves(n,stack=()):
  assert n not in stack,('combinational cycle',n)
  node=nodes[n];ref=node['ref']
  if ref in ['GND','VCC']:return set()
  if ref.startswith('LUT') and not node['init']:return {n}
  if ref.startswith('LUT') or ref=='INV':return set().union(*(leaves(v,stack+(n,)) for v in inputs(n).values()))
  assert re.fullmatch(r'FD[RSCE]*',ref),('Unsupported driver',node)
  return {n}
 def evaluate(n,values):
  node=nodes[n];ref=node['ref']
  if ref=='GND':return 0
  if ref=='VCC':return 1
  if ref=='INV':return 1-evaluate(next(iter(inputs(n).values())),values)
  if ref.startswith('LUT') and not node['init']:return values[n]
  if ref.startswith('LUT'):
   assert re.fullmatch(r'LUT[1-6]',ref),ref
   width=int(ref[-1]);assert set(inputs(n))=={'I'+str(i) for i in range(width)}
   index=sum(evaluate(inputs(n)['I'+str(i)],values)<<i for i in range(width))
   return (verilog_int(node['init'])>>index)&1
  return values[n]
 results=[]
 for dsp,properties in dsps.items():
  assert set(bits[dsp])==set(range(9))
  ls=sorted(set().union(*(leaves(n) for n in bits[dsp].values())));assert len(ls)<=16,(dsp,len(ls))
  ops=set()
  for values in itertools.product([0,1],repeat=len(ls)):
   assignment=dict(zip(ls,values));op=sum(evaluate(bits[dsp][i],assignment)<<i for i in range(9))^properties['invert'];ops.add(op)
  feedback=[op for op in ops if ((op>>7)&3)==1 or ((op>>4)&7) in [2,4,6] or (op&3)==2]
  results.append(dict(cell=dsp,**properties,leaves=ls,possible_opmode=[format(op,'09b') for op in sorted(ops)],p_feedback_possible=bool(feedback)))
 unsafe=[x for x in results if not x['preg'] and x['p_feedback_possible']]
 assert not unsafe,unsafe
 return results

def main():
 receipt=json.loads((R/'TERMINAL_COLLECTION_R1.json').read_text());assert receipt['all_observed_identities_absent'] and receipt['source_sha_match'] and receipt['group_empty'] and receipt['lock_absent']
 for rel,v in receipt['files'].items():
  p=R/'terminal_collection_r1'/rel;assert p.stat().st_size==v['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256'],rel
 metrics=json.loads((H/'route_metrics.json').read_text());assert metrics['setup_slack_ns']>=0 and metrics['hold_slack_ns']>=0
 timing=(H/'timing.rpt').read_text();assert 'All user specified timing constraints are met.' in timing
 check=(H/'check_timing.rpt').read_text();counts=dict(re.findall(r'^\d+\. checking (\w+) \((\d+)\)',check,re.M));assert counts and all(int(n)==(1 if k=='no_output_delay' else 0) for k,n in counts.items())
 assert check.count('\nc0_ddr4_reset_n_0\n')==1
 skew=[float(x) for x in re.findall(r'Slack \(MET\)\s*:\s*([\d.]+)ns',(H/'bus_skew.rpt').read_text())];assert len(skew)==14 and min(skew)>=0 and '(VIOLATED)' not in (H/'bus_skew.rpt').read_text()
 route=(H/'route_status.rpt').read_text();assert re.search(r'fully routed nets\.+\s*:\s*158100',route) and re.search(r'nets with routing errors\.+\s*:\s*0',route)
 cdc=(H/'cdc.rpt').read_text();summary=re.findall(r'^(CDC-\d+)\s+(\w+)\s+(\d+)\s',cdc,re.M);assert summary==[('CDC-3','Info','174'),('CDC-9','Info','12'),('CDC-15','Warning','4')]
 rows=[s for s in cdc.splitlines() if re.match(r'\s*\d+\s+CDC-15\s',s)];assert len(rows)==4 and all(s.count('dbg_hub/inst/BSCANID.')==2 and 'SUBCORE_FIFO' in s and 'False Path' in s for s in rows)
 drc=(H/'drc.rpt').read_text();summary=re.findall(r'^\| ([\w-]+)\s+\|\s*(Warning|Advisory|Error|Critical Warning)\s+\|.*?\|\s*(\d+)\s*\|',drc,re.M)
 assert summary and all(s in ['Warning','Advisory'] for _,s,_ in summary)
 blocks=re.split(r'(?m)(?=^[A-Z][A-Z0-9-]+#\d+ )',drc)
 pdcn=[b for b in blocks if b.startswith('PDCN-1569#')];assert len(pdcn)==3 and all('cell dbg_hub/inst/' in b for b in pdcn)
 results=parse_cones();assert len(results)==182
 warned=[b for b in blocks if b.startswith('DPREG-7#')];assert len(warned)==64
 warned_cells=[re.search(r'The DSP48E2 cell (\S+) with',b).group(1) for b in warned]
 byname={x['cell']:x for x in results};assert all(n in byname and byname[n]['preg']==0 and not byname[n]['p_feedback_possible'] for n in warned_cells)
 expected={}
 xdc=ROOT/'module_14_lm_head_v4/experiments/d64_system_200m_20261105_r1/lm_head_v4_ddr4_pins.xdc'
 for s in xdc.read_text().splitlines():
  m=re.fullmatch(r'set_property (PACKAGE_PIN|IOSTANDARD|DRIVE|SLEW) (\S+) \[get_ports \{(.*)\}\]',s)
  if m:expected.setdefault(m[3],{})[m[1]]=m[2]
 actual={}
 for s in (N/'io.tsv').read_text().splitlines():
  fields=s.split('\t');assert len(fields)==5;actual[fields[0]]=dict(zip(['PACKAGE_PIN','IOSTANDARD','DRIVE','SLEW'],fields[1:]))
 assert len(expected)>=70,len(expected)
 for port,properties in expected.items():
  assert port in actual,port
  for k,v in properties.items():assert actual[port][k]==v,(port,k,v,actual[port][k])
 assert actual['c0_ddr4_reset_n_0']['PACKAGE_PIN']=='AM5' and actual['c0_ddr4_reset_n_0']['IOSTANDARD']=='LVCMOS12' and actual['c0_ddr4_reset_n_0']['DRIVE']=='8'
 reset=(N/'reset_fanin.txt').read_text().strip();assert 'ddr4_0/inst/' in reset and 'reset' in reset.lower(),reset
 clocks=(H/'clocks.rpt').read_text();assert re.search(r'^clk_pl_0\s+5\.000\s',clocks,re.M) and re.search(r'^mmcm_clkout0\s+5\.000\s',clocks,re.M)
 out=dict(state='PASS_OFFLINE_ROUTE_WITH_EXPLICIT_FINDING_DISPOSITIONS_NOT_BOARD',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),metrics=metrics,post_route_dcp=receipt['post_route_dcp'],collection_archive_sha256=receipt['archive_sha256'],resources=receipt['resources'],cdc_summary=[('CDC-3','Info','174'),('CDC-9','Info','12'),('CDC-15','Warning','4')],drc_summary=summary,bus_skew_min_slack_ns=min(skew),pin_ports_checked=len(expected),dsp_count=len(results),dpreg7_count=64,dsp_feedback='Conservative exhaustive OPMODE evaluation: sequential outputs and protected LUTs without exposed INIT are independent unconstrained Boolean leaves; no P feedback for any PREG=0 cell',findings=dict(ddr_reset='Only missing output delay is MIG-owned asynchronous DDR reset; AM5/LVCMOS12/DRIVE8 and MIG fanin verified. No synchronous data endpoint exempted. No added false path or invented delay.',cdc15='All four paths in vendor debug hub read/write FIFO; production AXI CDC reports synchronized structures and positive bus-skew limits.',dpreg7='All 64 warned DSPs conservatively evaluated with protected LUT outputs unconstrained; feedback mux choices excluded even in this overapproximation; no RTL edits or warning suppression.',pipelining='DSP pipeline recommendations retained; declared target timing positive; no numerical qualification inferred.',pdcn1569='Three LUT warnings confined to debug hub; not computation datapath.',rtstat10='Vendor MIG unused calibration/debug nets listed in raw report; actual routable nets complete.'),board='NOT_RUN',full12rtl='INCOMPLETE_USER_STOPPED',bit_allowed='Manual generation from this exact post_route DCP/project only, with matching XSA/BSP audit still required',dsp=results)
 (R/'INDEPENDENT_ROUTE_REVIEW.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in out.items() if k!='dsp'},indent=2))
if __name__=='__main__':main()
