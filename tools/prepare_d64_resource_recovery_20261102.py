"""Prepare isolated packed-bank memory qualification; never starts full M14."""
from pathlib import Path
import difflib, hashlib, json, tarfile

ROOT=Path(__file__).resolve().parents[1]
M=ROOT/'module_14_lm_head_v4'
E=M/'experiments/d64_resource_recovery_20261102'
R=M/'reports/d64_resource_recovery_20261102_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    E.mkdir(exist_ok=True);R.mkdir(exist_ok=True)
    assert not (R/'PLAN.json').exists()
    old=M/'experiments/sim_memory_bank_20261026/mem_model.sv'
    original=old.read_text(encoding='utf-8')
    packed=original
    replacements={
      'logic[WIDTH-1:0] mem[];':'logic[16*WIDTH-1:0] mem[];',
      'bit IsWr[];':'bit[15:0] IsWr[];',
      'mem = new[count];':'mem = new[(count+15)/16];',
      'IsWr = new[count];':'IsWr = new[(count+15)/16];',
      'banks[bank_id].mem[slot]':'banks[bank_id].mem[slot >> 4][(slot & 15)*WIDTH +: WIDTH]',
      'banks[bank_id].IsWr[slot]':'banks[bank_id].IsWr[slot >> 4][slot & 15]',
    }
    for a,b in replacements.items():
        assert a in packed,a
        packed=packed.replace(a,b)
    assert packed[packed.index('class mem_model_pages#'):]==original[original.index('class mem_model_pages#'):]
    (E/'mem_model.sv').write_text(packed,encoding='utf-8')
    (E/'model.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),packed.splitlines(True),fromfile='qualified_byte_banks',tofile='packed16_banks')),encoding='utf-8')
    tb=(M/'experiments/sim_memory_bank_20261026/bank_memory_tb.sv').read_text()
    # Compare original 2093 CSV events unchanged; add assertions without CSV rows.
    anchor=' $fclose(fd);$display("BANK_MEMORY_UNIT_PASS '
    assert anchor in tb
    more='''
 // Every lane of a packed word retains X/Z and independent written flags.
 m.init(1048593,0);
 for(i=0;i<16;i=i+1)begin
   status=m.read_one_elem(value,1048576+i);
   if(status || value!==8'hxx)$fatal(1,"unwritten packed lane");
 end
 for(i=0;i<16;i=i+1)begin
   status=m.write_one_elem((i*19+7)&255,1048576+i);
   if(status)$fatal(1,"packed lane write");
 end
 for(i=0;i<16;i=i+1)begin
   status=m.read_one_elem(value,1048576+i);
   if(status || value!==((i*19+7)&255))$fatal(1,"packed lane value");
 end
 status=m.read_one_elem(value,1048592);if(status || value!==8'hxx)$fatal(1,"partial last word unwritten");
 status=m.write_one_elem(8'b10xz01zx,1048592);
 status=m.read_one_elem(value,1048592);if(status || value!==8'b10xz01zx)$fatal(1,"byte XZ preserve");
 status=m.write_one_elem(8'h55,1048593);if(!status)$fatal(1,"padding accepted");
 status=m.read_one_elem(value,1048593);if(!status || value!==8'hxx)$fatal(1,"padding read accepted");
 m.init(32,17);status=m.read_one_elem(value,33);if(status || value!==8'hxx)$fatal(1,"reinit stale");
 $display("PACKED_LANES_PASS lanes=16 last_bank=17 padding_rejected=1 reinit=1 four_state=1");
'''
    tb=tb.replace(anchor,more+anchor)
    (E/'bank_memory_tb.sv').write_text(tb)
    benchmark='''`timescale 1ns/1ps
module memory_bench_tb;
import uvm_pkg::*; import file_agent_pkg::*;
mem_model#(8) m;
logic[7:0] q[$], got;
integer i,j,k,status,fd;
longint unsigned checksum;
initial begin
 fd=$fopen("bench_events.csv","w");
 m=new("bench");m.init(4194304,0);
 $display("BENCH_PHASE init");
 for(i=0;i<4194304;i=i+1)begin
   status=m.write_one_elem((i*17+3)&255,i);
   if(status)$fatal(1,"bench write");
 end
 $display("BENCH_PHASE filled");
 for(k=0;k<3;k=k+1)begin
   checksum=0;
   for(i=0;i<262144;i=i+1)begin
     status=m.read_elems(q,i*16,16);
     if(status || q.size()!=16)$fatal(1,"bench read status");
     for(j=0;j<16;j=j+1)begin
       if(q[j]!==(((i*16+j)*17+3)&255))$fatal(1,"bench data");
       checksum=checksum+q[j];
     end
   end
   if(checksum!==64'd534773760)$fatal(1,"bench checksum");
   $fwrite(fd,"%0d,%0d\\n",k,checksum);$fflush(fd);
   $display("BENCH_PHASE epoch=%0d checksum=%0d",k,checksum);
 end
 $fclose(fd);$display("MEMORY_BENCH_PASS bytes=4194304 epochs=3 reads=12582912");$finish;
end
endmodule
'''
    (E/'memory_bench_tb.sv').write_text(benchmark)
    # The remote runner is copied by the caller before freezing its identity.
    runner=ROOT/'tools/run_d64_resource_recovery_20261102.py'
    (E/'run_qualification.py').write_bytes(runner.read_bytes())
    sources={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in E.iterdir() if p.is_file()}
    plan={'state':'FROZEN_FINITE_MEMORY_QUALIFICATION_ONLY','baseline_model':str(old.relative_to(ROOT)).replace('\\','/'),
      'baseline_sha256':sha(old),'source_sha256':sources,
      'scope':'Simulation storage representation only; original RTL, FP32, FIFO and AXI stalls unchanged',
      'cases':['packed_unit','byte_bench','packed_bench'],
      'limits':{'per_phase_seconds':600,'min_available_gib':32,'max_group_rss_gib':48},
      'full_m14':'NOT_RUN','board':'NOT_RUN','automatic_next_stage':False}
    (R/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
    with tarfile.open(R/'entry.tar.gz','w:gz') as archive:
        for p in list(E.iterdir())+[R/'PLAN.json']:archive.add(p,arcname=str(p.relative_to(ROOT)))
    print(json.dumps({'archive':str(R/'entry.tar.gz'),'sha256':sha(R/'entry.tar.gz')}))

if __name__=='__main__':main()
