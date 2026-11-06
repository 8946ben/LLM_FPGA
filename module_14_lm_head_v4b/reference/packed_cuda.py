"""Actual packed-buffer GPU reference. Same reduction as the qualified evaluator."""
from pathlib import Path
import ctypes as C
import importlib.util,re
import torch

class PackedCuda:
    def __init__(self,cache,metadata=None):
        path=Path(__file__).with_name('exact_cuda.py')
        spec=importlib.util.spec_from_file_location('v4b_packed_compiler',path)
        compiler=importlib.util.module_from_spec(spec);spec.loader.exec_module(compiler)
        if metadata is None:
            load=r'''
__device__ __forceinline__ float loadw(const unsigned char* w,int row,int col){
  long long address=(long long)row*1792+col*2;
  unsigned int bits=(unsigned int)w[address]|((unsigned int)w[address+1]<<8);
  return __uint_as_float(bits<<16);
}
'''
        else:
            b,g=metadata['bits'],metadata['group'];payload=g*b//8;zb=metadata['zero_bytes'];record=payload+4+zb
            load='''
__device__ __forceinline__ float loadw(const unsigned char* w,int row,int col){
  const unsigned char* p=w+256+(long long)row*ROW_BYTES+(col/GROUP)*RECORD_BYTES;
  int bit=(col%GROUP)*BITS, byte=bit>>3, shift=bit&7;
  unsigned int word=(unsigned int)p[byte]|((unsigned int)p[byte+1]<<8)|((unsigned int)p[byte+2]<<16);
  int q=(word>>shift)&MASK;
  SIGN_EXTEND
  unsigned int sb=(unsigned int)p[PAYLOAD]|((unsigned int)p[PAYLOAD+1]<<8)|((unsigned int)p[PAYLOAD+2]<<16)|((unsigned int)p[PAYLOAD+3]<<24);
  int zero=ZERO_EXPR;
  return __fmul_rn((float)(q-zero),__uint_as_float(sb));
}
'''
            pairs={'ROW_BYTES':metadata['row_bytes'],'GROUP':g,'RECORD_BYTES':record,'BITS':b,'MASK':(1<<b)-1,'PAYLOAD':payload,
                   'SIGN_EXTEND':f'if(q>={1<<(b-1)})q-={1<<b};' if metadata['symmetric'] else '',
                   'ZERO_EXPR':'0' if zb==0 else ('(int)p[PAYLOAD+4]' if zb==1 else '((int)p[PAYLOAD+4]|((int)p[PAYLOAD+5]<<8))')}
            # Insert ZERO_EXPR first because its expression also has PAYLOAD tokens.
            for key in ['ZERO_EXPR','ROW_BYTES','GROUP','RECORD_BYTES','BITS','MASK','PAYLOAD','SIGN_EXTEND']:load=load.replace(key,str(pairs[key]))
        source=compiler.SOURCE.replace('const float* w','const unsigned char* w')
        source=re.sub(r'w\[\(long long\)row\*896\+([^\]]+)\]',r'loadw(w,row,\1)',source)
        compiler.SOURCE=load+source
        self.source=compiler.SOURCE;self.engine=compiler.ExactCuda(cache)
        (Path(cache)/'packed.cu').write_text(self.source,encoding='utf-8')

    def __call__(self,weight,hidden,rows):
        assert weight.is_cuda and hidden.is_cuda and weight.is_contiguous() and hidden.is_contiguous()
        assert hidden.dtype==torch.float32 and hidden.ndim==2 and hidden.shape[1]==896
        assert weight.dtype in (torch.uint8,torch.bfloat16)
        out=torch.empty((len(hidden),rows),dtype=torch.float32,device=hidden.device)
        args=[C.c_void_p(weight.data_ptr()),C.c_void_p(hidden.data_ptr()),C.c_void_p(out.data_ptr()),C.c_int(rows)]
        values=(C.c_void_p*len(args))(*(C.cast(C.byref(x),C.c_void_p) for x in args))
        self.engine.check(self.engine.launch(self.engine.function,(rows+3)//4,len(hidden),1,128,1,1,0,
          C.c_void_p(torch.cuda.current_stream().cuda_stream),values,None))
        return out
