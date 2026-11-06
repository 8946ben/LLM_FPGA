"""Independent ELF64/AArch64 PS-memory layout audit. Never executes an ELF."""
from pathlib import Path
import argparse,hashlib,json,struct

def audit(path):
    data=path.read_bytes()
    h=struct.unpack_from('<16sHHIQQQIHHHHHH',data)
    assert h[0][:6]==b'\x7fELF\x02\x01' and h[1:4]==(2,183,1),'Not LE AArch64 executable'
    entry,phoff,phsize,phcount=h[4],h[5],h[9],h[10]
    assert phsize==56 and phcount>0 and phoff+phsize*phcount<=len(data),'Invalid program table'
    loads=[]
    for i in range(phcount):
        kind,flags,offset,virtual,physical,filesz,memsz,align=struct.unpack_from('<IIQQQQQQ',data,phoff+i*phsize)
        if kind!=1:continue
        assert virtual==physical and 0<=physical<0x10000000 and 0<memsz<=0x10000000-physical,'LOAD outside reserved PS software memory'
        assert filesz<=memsz and offset+filesz<=len(data),'Truncated LOAD'
        loads.append(dict(address=hex(physical),memory_bytes=memsz,file_bytes=filesz,flags=flags,alignment=align))
    assert loads and any(int(v['address'],0)<=entry<int(v['address'],0)+v['memory_bytes'] and v['flags']&1 for v in loads),'Entry outside executable PS LOAD'
    return dict(file=path.name,sha256=hashlib.sha256(data).hexdigest(),entry=hex(entry),loads=loads)

def main():
    p=argparse.ArgumentParser();p.add_argument('--elf',type=Path,action='append',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    assert not a.out.exists(),'Preserve prior audit'
    result=dict(state='PASS_OFFLINE_ELF_LAYOUT',architecture='LE AArch64 EXEC',ps_software_range='0x00000000..0x0fffffff',
                mailbox='0x51000000 outside ELF LOADs',board='NOT_RUN',files=[audit(p) for p in a.elf])
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n')
    print('M14_V4_ELF_LAYOUT=PASS PS software memory only; no ELF execution')
if __name__=='__main__':main()
