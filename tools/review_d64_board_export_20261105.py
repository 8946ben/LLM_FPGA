from pathlib import Path
import json,re,hashlib,xml.etree.ElementTree as ET,datetime,difflib
r=Path('module_14_lm_head_v4/reports/d64_board_20261105_r1');out=r/'exported_ip';ns={'s':'http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009'};top=ET.parse(out/'component.xml').getroot()
def val(e,n):return e.find('s:'+n,ns).text
identity={k:val(top,k) for k in ['vendor','library','name','version']};assert identity==dict(vendor='user.org',library='hls',name='lm_head_v4_partial_proto',version='4.1')
params={val(p,'name'):val(p,'value') for p in top.findall('s:model/s:modelParameters/s:modelParameter',ns)};ports={val(p,'name'):p for p in top.findall('s:model/s:ports/s:port',ns)}
interfaces={val(b,'name'):{val(p,'name'):val(p,'value') for p in b.findall('s:parameters/s:parameter',ns)} for b in top.findall('s:busInterfaces/s:busInterface',ns)}
for name in ['m_axi_meta','m_axi_weights']:
 for suffix,width in [('ARADDR',64),('AWADDR',64),('RDATA',128),('WDATA',128)]:
  vec=ports[name+'_'+suffix].find('s:wire/s:vector',ns);assert int(val(vec,'left'))-int(val(vec,'right'))+1==width
 assert int(params['C_'+name.upper()+'_ADDR_WIDTH'])==64 and int(params['C_'+name.upper()+'_DATA_WIDTH'])==128
assert set(['s_axi_control','ap_clk','ap_rst_n']).issubset(interfaces)
plan=json.loads((r/'EXPORT_PLAN.json').read_text());src=Path('module_14_lm_head_v4/reports/partial_hw_20261024_r1/r3/remote_hls/syn/verilog');unchanged=[];tcls=[];diffs=[]
overlay='\nreg find_df_deadlock = 0;\n// synthesis translate_off\n`include "lm_head_v4_partial_proto_hls_deadlock_detector.vh"\n// synthesis translate_on\n\n'
for name,h in plan['syn_verilog_sha256'].items():
 assert hashlib.sha256((src/name).read_bytes()).hexdigest()==h
 if name.endswith('_ip.tcl'):tcls.append(name);continue
 p=out/'hdl/verilog'/name;assert p.exists(),name
 if hashlib.sha256(p.read_bytes()).hexdigest()==h:unchanged.append(name)
 else:
  assert name=='lm_head_v4_partial_proto.v';actual=p.read_text();original=(src/name).read_text();assert actual.count(overlay)==1
  assert actual.replace(overlay,'').rstrip()==original.rstrip(),'Top contains additional differences'
  diffs.append(''.join(difflib.unified_diff(original.splitlines(True),actual.splitlines(True))))
assert (len(unchanged),len(tcls),len(diffs))==(68,4,1),(len(unchanged),len(tcls),len(diffs))
sim=json.loads((r/'SIMULATED_FP_SOURCES.json').read_text());compiled=json.loads(Path('module_14_lm_head_v4/reports/d64_state_compile_20261105_r2/COMPILED_SOURCES.json').read_text());fp={}
for name,text in sim.items():
 assert hashlib.sha256(text.encode()).hexdigest()==compiled['ip/xil_defaultlib/'+name]
 hw=(out/'hdl/ip'/name).read_text();a=dict(re.findall(r'\.(C_[A-Z0-9_]+)\(([^)]+)\)',text));b=dict(re.findall(r'\.(C_[A-Z0-9_]+)\(([^)]+)\)',hw))
 assert len(a)>60 and a==b,(name,{k:(a.get(k),b.get(k)) for k in a.keys()|b.keys() if a.get(k)!=b.get(k)})
 assert set(re.findall(r'floating_point_v\d+_\d+_\d+',text))==set(re.findall(r'floating_point_v\d+_\d+_\d+',hw))=={'floating_point_v7_1_15'}
 fp[name]=a
missing=[f.text for f in top.findall('.//s:file/s:name',ns) if not (out/f.text).exists()];assert not missing,missing
registers={val(reg,'name'):int(val(reg,'addressOffset'),0) for reg in top.findall('s:memoryMaps/s:memoryMap/s:addressBlock/s:register',ns)}
review=dict(state='PASS_IP_EXPORT_IDENTITY_INTERFACES_AND_COMPUTE_SOURCE_AUDIT',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),identity=identity,model_parameters=params,interfaces=interfaces,registers=registers,original_syn_files_unchanged_in_source=73,export_compute_verilog_byte_identical=68,export_top_exact_addition=diffs,export_top_change_scope='One unused initialized find_df_deadlock register and translate_off detector include only;original hardware logic text identical',fp_complete_parameters_match_simulated_sources=fp,original4_fp_generation_tcl='Export materializes4 wrappers;all actual FP parameters and core library versions match actual compiled simulation wrappers',zip_sha256=hashlib.sha256((r/'export.zip').read_bytes()).hexdigest(),process_after=[],lock_exists=False,limitations='Not BD/timing/bitstream/software/board pass;full12 RTL incomplete by user choice',initial_audit_rejections=['Optional AXI BUSIF width parameters absent;actual model parameters+port vectors checked','Strict original73 byte export assumption rejected;exact generated diagnostic and FP materialization audited'])
(r/'EXPORT_INDEPENDENT_REVIEW.json').write_text(json.dumps(review,indent=2)+'\n');print(review['state']);print(registers)
