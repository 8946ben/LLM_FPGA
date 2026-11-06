"""New RTL-only harness. Frozen r3 Verilog is consumed byte for byte."""
from pathlib import Path
import hashlib,json,re,tarfile
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
M=ROOT/'module_14_lm_head_v4';E=M/'experiments/partial_rtl_20261024';R=M/'reports/partial_rtl_20261024_r1'
OLD=M/'experiments/partial_hw_20261024';RTL=M/'reports/partial_hw_20261024_r1/r3/remote_hls/syn/verilog'
V=151936;T=4096;TABLE=75968;WS=79068;BIAS=255;N=WS+BIAS+8
PREFIX='lm_head_v4_partial_proto'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def ports(path):
    return re.findall(r'^(input|output)\s+(?:wire\s+)?(\[[^;\n]+?\])?\s*(\w+)\s*;',path.read_text(),re.M)
def hex128(path,a):
    assert len(a)%4==0
    b=np.asarray(a,dtype='<u4').reshape(-1,4)
    path.write_text(''.join(''.join(f'{int(x):08x}' for x in row[::-1])+'\n' for row in b),encoding='ascii')
def main():
    assert not (R/'PLAN.json').exists()
    (E/'fixtures').mkdir(parents=True,exist_ok=True);R.mkdir(parents=True,exist_ok=True)
    cases=[]
    for name in ['old_chinese','old_english','old_chinese','old_code','old_math','new_chinese','new_english','new_code','new_math','zero_hidden']:
        keys=np.fromfile(OLD/'fixtures'/f'{name}.keys.bin',dtype='<u4')
        ids=np.fromfile(OLD/'fixtures'/f'{name}.ids.bin',dtype='<u4')
        cases.append((name,keys,ids))
    for name,keys in [('all_same_bucket',np.uint32(0x80000000)+(np.arange(V,dtype=np.uint32)%17)),
                      ('special_already_top',np.arange(V,dtype=np.uint32)),
                      ('reverse_ids',np.arange(V-1,-1,-1,dtype=np.int64).astype(np.uint32))]:
        ranked=np.lexsort((np.arange(V),-keys.astype(np.int64)))[:T]
        ids=np.union1d(ranked,np.arange(151643,151657)).astype('<u4');cases.append((name,keys,ids))
    records=[]
    for i,(name,keys,ids) in enumerate(cases):
        ranked=np.lexsort((np.arange(V),-keys.astype(np.int64)))[:T]
        assert np.array_equal(ids,np.union1d(ranked,np.arange(151643,151657)))
        a=np.full((N,4),0xa5a55a5a,dtype='<u4');a[BIAS:BIAS+V//4]=keys.reshape(-1,4)
        inp=E/'fixtures'/f'{i:02d}_in.hex';out=E/'fixtures'/f'{i:02d}_out.hex'
        hex128(inp,a.reshape(-1));a[BIAS+TABLE]=[0x4449344d,0x00040001,len(ids),V]
        padded=np.full(((len(ids)+3)//4)*4,0xffffffff,dtype='<u4');padded[:len(ids)]=ids
        a[BIAS+TABLE+1:BIAS+TABLE+1+len(padded)//4]=padded.reshape(-1,4);hex128(out,a.reshape(-1))
        records.append(dict(index=i,name=name,K=len(ids),input=str(inp.relative_to(ROOT)).replace('\\','/'),expected=str(out.relative_to(ROOT)).replace('\\','/')))
    # Use the exact adapter parameter/port block from the frozen top, not a rebuilt adapter.
    top=(RTL/(PREFIX+'.v')).read_text();start=top.index(PREFIX+'_meta_m_axi #(');end=top.index('\n);',start)+3
    adapter=top[start:end].replace('meta_m_axi_U','adapter').replace('m_axi_meta_','bus_').replace('meta_','inner_')
    # Prefix replacement above also touches the module name; restore it explicitly.
    adapter=adapter.replace(PREFIX+'_inner_m_axi',PREFIX+'_meta_m_axi')
    adapter=adapter.replace('ap_rst_n_inv','rst').replace('ap_clk','clk')
    param={'C_M_AXI_META_ID_WIDTH':'1','C_M_AXI_META_ADDR_WIDTH':'64','C_M_AXI_META_DATA_WIDTH':'128',
           'C_M_AXI_META_AWUSER_WIDTH':'1','C_M_AXI_META_ARUSER_WIDTH':'1','C_M_AXI_META_WUSER_WIDTH':'1',
           'C_M_AXI_META_RUSER_WIDTH':'1','C_M_AXI_META_BUSER_WIDTH':'1','C_M_AXI_META_USER_VALUE':'0',
           'C_M_AXI_META_PROT_VALUE':'0','C_M_AXI_META_CACHE_VALUE':'3'}
    for key,val in param.items():adapter=adapter.replace(key,val)
    sub=RTL/(PREFIX+'_p_anonymous_namespace_radix_candidates.v');decl=[];conn=[]
    mapped={'ap_clk':'clk','ap_rst':'rst','ap_start':'start','ap_done':'done','ap_idle':'idle','ap_ready':'ready','workspace':"64'h400000ff0",'ap_return':'result'}
    for direction,width,name in ports(sub):
        if name.startswith('m_axi_meta_'):
            signal=name.replace('m_axi_meta_','inner_');decl.append(f'wire {width or ""} {signal};');conn.append(f'.{name}({signal})')
        else:conn.append(f'.{name}({mapped[name]})')
    for direction,width,name in ports(RTL/(PREFIX+'_meta_m_axi.v')):
        pass # adapter uses parameter expressions; external widths below come from the top.
    for direction,width,name in ports(RTL/(PREFIX+'.v')):
        if not name.startswith('m_axi_meta_'):continue
        width=width or ''
        for key,val in param.items():width=width.replace(key,val)
        width=width.replace('C_M_AXI_META_WSTRB_WIDTH','16')
        decl.append(f'wire {width} {name.replace("m_axi_meta_","bus_")};')
    memports=['AWVALID','AWREADY','AWADDR','AWID','AWLEN','AWSIZE','AWBURST','WVALID','WREADY','WDATA','WSTRB','WLAST',
              'BVALID','BREADY','BID','BRESP','ARVALID','ARREADY','ARADDR','ARID','ARLEN','ARSIZE','ARBURST','RVALID','RREADY','RDATA','RLAST','RID','RRESP']
    assign='assign inner_RLAST=0; assign inner_RID=0; assign inner_RUSER=0; assign inner_RRESP=0; assign inner_BID=0; assign inner_BUSER=0; assign inner_BRESP=0;\nassign bus_RUSER=0; assign bus_BUSER=0;'
    tb='''`timescale 1ns/1ps
module radix_tb;
reg clk=0,rst=1,start=0; always #2.5 clk=~clk;
wire done,idle,ready;wire [31:0] result;
DECL
ASSIGN
DUT dut(CONN);
ADAPTER
axi_stall_memory #(.BASE(64'h400000000),.N(NBEATS)) mem(.clk(clk),.rst(rst),MEMCONN);
reg [127:0] expected[0:NBEATS-1];
integer ci,j,cycles;string fixtures; string inpath,outpath;reg [31:0] ks[0:NCASES-1];
initial begin
if(!$value$plusargs("fixtures=%s",fixtures))$fatal(1,"fixtures missing");
KVALUES
repeat(8)@(negedge clk);rst=0;
for(ci=0;ci<NCASES;ci=ci+1)begin
inpath=$sformatf("%s/%02d_in.hex",fixtures,ci);outpath=$sformatf("%s/%02d_out.hex",fixtures,ci);
$readmemh(inpath,mem.data);$readmemh(outpath,expected);
@(negedge clk);start=1;cycles=0;
while(!done)begin @(negedge clk);cycles=cycles+1;if(cycles>2100000)$fatal(1,"selector timeout case%0d",ci);end
start=0;
if(result!==ks[ci])$fatal(1,"K case%0d got%0d expected%0d",ci,result,ks[ci]);
repeat(100)@(negedge clk);
for(j=0;j<NBEATS;j=j+1)if(mem.data[j]!==expected[j])$fatal(1,"memory case%0d beat%0d got%032h expected%032h",ci,j,mem.data[j],expected[j]);
$display("RADIX_CASE_PASS index=%0d K=%0d cycles=%0d read=%0d write=%0d ARstall=%0d Rgap=%0d AWstall=%0d Wstall=%0d Bdelay=%0d boundary=%0d",ci,result,cycles,mem.rdbeats,mem.wrbeats,mem.arstall,mem.rgap,mem.awstall,mem.wstall,mem.bdelay,mem.boundary);
end
if(mem.arstall==0||mem.rgap==0||mem.awstall==0||mem.wstall==0||mem.bdelay==0||mem.boundary==0)$fatal(1,"coverage absent");
$display("RADIX_RTL_ALL_PASS cases=NCASES source=frozen_r3_with_original_AXI_adapter");$finish;
end
endmodule
'''
    tb=tb.replace('DECL','\n'.join(decl)).replace('ASSIGN',assign).replace('DUT',PREFIX+'_p_anonymous_namespace_radix_candidates').replace('CONN',',\n'.join(conn),1).replace('ADAPTER',adapter)
    tb=tb.replace('MEMCONN',','.join(f'.{s}(bus_{s})' for s in memports)).replace('NBEATS',str(N)).replace('NCASES',str(len(cases)))
    tb=tb.replace('KVALUES','\n'.join(f'ks[{i}]={len(x[2])};' for i,x in enumerate(cases)))
    (E/'radix_tb.sv').write_text(tb,encoding='utf-8')
    # Model body is maintained separately and frozen with the test entry.
    model=ROOT/'tools/rtl_axi_stall_memory_20261024.sv';assert model.exists();(E/'axi_stall_memory.sv').write_bytes(model.read_bytes())
    sources=[p for p in RTL.glob('*.v') if ('radix_candidates' in p.name or 'meta_m_axi' in p.name)]
    (E/'radix_sources.txt').write_text('\n'.join(str(p.relative_to(ROOT)).replace('\\','/') for p in sources)+'\n',encoding='utf-8')
    plan=dict(state='FROZEN_SELECTOR_RTL_ENTRY',tool='Vivado xsim 2022.2 on STHL',cases=records,
              method='Direct frozen generated radix RTL plus original generated AXI adapter; no C++ resynthesis',
              scope='full151936 keys/T4096; 64bit base, 4KiB split, deterministic stalls all5channels, A-B-A, ties, repeated bucket, special inclusion; whole memory compare',
              limitations=['Segmented test is not full integrated RTL','Behavioral bounded single-outstanding memory, not MIG/DDR timing','No FPGA operations or quality retuning'],
              automatic_next_stage=False,source_sha256={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in sources+list(E.rglob('*'))+[Path(__file__)] if p.is_file()})
    dump(R/'PLAN.json',plan)
    with tarfile.open(R/'selector_entry.tar.gz','w:gz') as tar:
        for p in E.rglob('*'):
            if p.is_file():tar.add(p,arcname=str(p.relative_to(ROOT)).replace('\\','/'))
        tar.add(R/'PLAN.json',arcname=str((R/'PLAN.json').relative_to(ROOT)).replace('\\','/'))
    print(json.dumps(dict(cases=len(cases),sources=len(sources),archive_sha256=sha(R/'selector_entry.tar.gz'))))
if __name__=='__main__':main()
