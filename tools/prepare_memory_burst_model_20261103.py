"""Simulation-only packed-slot APIs; original byte APIs and deployed RTL preserved."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';E=M/'experiments/memory_burst_model_20261103_r3'
B=M/'experiments/memory_full_loader_small_20261103_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 E.mkdir(exist_ok=True);assert not (E/'MODEL_CHANGES.json').exists()
 model=(B/'mem_model.sv').read_text();edits=[]
 def edit(a,b):
  nonlocal model
  assert model.count(a)==1,a[:100];model=model.replace(a,b);edits.append([a,b])
 methods=r'''    // Sixteen elements, aligned to one packed slot; byte APIs remain available.
    function bit write_packed16(logic[16*WIDTH-1:0] data, longint addrin);
        longint relative;
        int bank_id,slot,count;
        relative=addrin-this.offset;
        if(depth<16 || relative<0 || relative>depth-16 || (relative&15)!=0)return 1;
        bank_id=relative>>20;slot=(relative&1048575)>>4;
        if(banks[bank_id]==null)begin
            count=depth-bank_id*1048576;if(count>1048576)count=1048576;
            banks[bank_id]=new(count);
        end
        banks[bank_id].mem[slot]=data;banks[bank_id].IsWr[slot]=16'hffff;
        return 0;
    endfunction

    function bit read_packed16(ref logic[16*WIDTH-1:0] data,input longint addrin);
        longint relative;
        int bank_id,slot;
        relative=addrin-this.offset;
        if(depth<16 || relative<0 || relative>depth-16 || (relative&15)!=0)begin data='hx;return 1;end
        bank_id=relative>>20;slot=(relative&1048575)>>4;
        if(banks[bank_id]==null)data='hx;else data=banks[bank_id].mem[slot];
        for(int j=0;j<16;j++)begin
            if(banks[bank_id]==null || banks[bank_id].IsWr[slot][j]==0)begin
                `uvm_warning(this.get_full_name, $sformatf("reading an unwritten address: addr:'d%0d, offset:'d%0d, depth: 'd%0d",addrin+j,this.offset,this.depth))
            end
        end
        is_rd=1;return 0;
    endfunction

    // Silent helper preserves write_elems_pipepage's original no-summary behavior.
    function int write_elems_packed(logic[WIDTH-1:0] data[$],longint addr);
        int i,errors;
        longint relative;
        logic[16*WIDTH-1:0] packed_word;
        i=0;errors=0;
        while(i<data.size())begin
            relative=addr+i-this.offset;
            if(data.size()-i>=16 && depth>=16 && relative>=0 && relative<=depth-16 && (relative&15)==0)begin
                for(int j=0;j<16;j++)packed_word[j*WIDTH+:WIDTH]=data[i+j];
                errors+=write_packed16(packed_word,addr+i);i+=16;
            end else begin errors+=write_one_elem(data[i],addr+i);i++;end
        end
        return errors;
    endfunction

'''
 anchor='    //return means the number of un-successful read\n'
 edit(anchor,methods+anchor)
 old=r'''        logic[WIDTH-1:0] tmp;
        read_elems = 0;
        data.delete();
        for(int i=0; i<length; i++) begin
            read_elems += read_one_elem(tmp, addr+i);
            data.push_back(tmp);
        end'''
 new=r'''        logic[WIDTH-1:0] tmp;
        logic[16*WIDTH-1:0] packed_word;
        longint relative;
        int i;
        read_elems = 0;
        data.delete();i=0;
        while(i<length)begin
            relative=addr+i-this.offset;
            if(length-i>=16 && depth>=16 && relative>=0 && relative<=depth-16 && (relative&15)==0)begin
                read_elems+=read_packed16(packed_word,addr+i);
                for(int j=0;j<16;j++)begin tmp=packed_word[j*WIDTH+:WIDTH];data.push_back(tmp);end
                i+=16;
            end else begin
                read_elems+=read_one_elem(tmp,addr+i);data.push_back(tmp);i++;
            end
        end'''
 edit(old,new)
 edit('''        write_elems = 0;
        for(int i=0; i<data.size; i++) begin
            write_elems += write_one_elem(data[i], addr+i);
        end''','''        write_elems = write_elems_packed(data,addr);''')
 old='''            for(k=0;k<16;k=k+1)begin
                errors=blk.write_one_elem((word128>>(k*8)) & 255,i*16+k+start_offset);
                if(errors) `uvm_fatal("stream_format","write outside configured input")
            end'''
 new='''            errors=blk.write_packed16(word128,i*16+start_offset);
            if(errors) `uvm_fatal("stream_format","write outside configured input")'''
 edit(old,new)
 old='''                for(int k=0; k<data.size; k++) pages[i].write_one_elem(data[k], addr[k]-page_ofst[i]-min_offset);'''
 new='''                bit contiguous;
                contiguous=(data.size()==addr.size() && data.size()>0);
                for(int k=1;k<addr.size();k++)if(addr[k]!=addr[0]+k)contiguous=0;
                if(contiguous)void'(pages[i].write_elems_packed(data,addr[0]-page_ofst[i]-min_offset));
                else for(int k=0;k<data.size;k++)void'(pages[i].write_one_elem(data[k],addr[k]-page_ofst[i]-min_offset));'''
 edit(old,new)
 restored=model
 for a,b in reversed(edits):assert restored.count(b)==1;restored=restored.replace(b,a)
 assert restored==(B/'mem_model.sv').read_text()
 (E/'mem_model.sv').write_text(model)
 (E/'MODEL_CHANGES.json').write_text(json.dumps({'predecessor_sha256':sha(B/'mem_model.sv'),'candidate_sha256':sha(E/'mem_model.sv'),'edits':edits},indent=2)+'\n')
 print(json.dumps({'model':str(E/'mem_model.sv'),'sha256':sha(E/'mem_model.sv'),'edits':len(edits)}))
if __name__=='__main__':main()
