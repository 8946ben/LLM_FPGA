"""Qualified CUDA evaluator of v3.1 H8/interleave16 arithmetic; no GEMM/FMA.

Runtime compilation uses the NVRTC shipped with the verified PyTorch install.
This evaluator's speed must never be compared to old Eager runs as method speedup.
"""
from pathlib import Path
import ctypes as C
import torch

SOURCE = r'''
extern "C" __global__ void exact_head(const float* w,const float* h,float* out,int rows) {
  int t=threadIdx.x&31,warp=threadIdx.x>>5,row=blockIdx.x*4+warp,n=blockIdx.y;
  if(row>=rows)return;
  float p0=0.f,p1=0.f,p2=0.f,p3=0.f;
  #pragma unroll
  for(int g=0;g<7;g++) {
    int j=g*128+t;
    p0=__fadd_rn(p0,__fmul_rn(w[(long long)row*896+j],h[(long long)n*896+j]));
    p1=__fadd_rn(p1,__fmul_rn(w[(long long)row*896+j+32],h[(long long)n*896+j+32]));
    p2=__fadd_rn(p2,__fmul_rn(w[(long long)row*896+j+64],h[(long long)n*896+j+64]));
    p3=__fadd_rn(p3,__fmul_rn(w[(long long)row*896+j+96],h[(long long)n*896+j+96]));
  }
  float a=__fadd_rn(__fadd_rn(p0,p2),__fadd_rn(p1,p3));
  a=__fadd_rn(a,__shfl_down_sync(0xffffffff,a,16));
  a=__fadd_rn(a,__shfl_down_sync(0xffffffff,a,8));
  a=__fadd_rn(a,__shfl_down_sync(0xffffffff,a,1));
  a=__fadd_rn(a,__shfl_down_sync(0xffffffff,a,2));
  a=__fadd_rn(a,__shfl_down_sync(0xffffffff,a,4));
  if(t==0)out[(long long)n*rows+row]=a;
}
'''

class ExactCuda:
    def __init__(self,cache):
        torch.cuda.init()
        # Lazy PyTorch initialization alone need not attach a driver context.
        self._context_anchor=torch.empty(1,device='cuda')
        self.cache=Path(cache);self.cache.mkdir(parents=True,exist_ok=True)
        self.driver=C.WinDLL('nvcuda.dll')
        lib=Path(torch.__file__).parent/'lib'
        self.nvrtc=C.CDLL(str(lib/'nvrtc64_130_0.dll'))
        def proto(lib,name,args):
            f=getattr(lib,name);f.argtypes=args;f.restype=C.c_int;return f
        ptr=C.c_void_p; pp=C.POINTER(ptr); sz=C.c_size_t; i=C.c_int; ui=C.c_uint
        self.create=proto(self.nvrtc,'nvrtcCreateProgram',[pp,C.c_char_p,C.c_char_p,i,C.POINTER(C.c_char_p),C.POINTER(C.c_char_p)])
        self.compile=proto(self.nvrtc,'nvrtcCompileProgram',[ptr,i,C.POINTER(C.c_char_p)])
        self.logsize=proto(self.nvrtc,'nvrtcGetProgramLogSize',[ptr,C.POINTER(sz)])
        self.log=proto(self.nvrtc,'nvrtcGetProgramLog',[ptr,ptr])
        self.ptxsize=proto(self.nvrtc,'nvrtcGetPTXSize',[ptr,C.POINTER(sz)])
        self.getptx=proto(self.nvrtc,'nvrtcGetPTX',[ptr,ptr])
        self.destroy=proto(self.nvrtc,'nvrtcDestroyProgram',[pp])
        self.load=proto(self.driver,'cuModuleLoadData',[pp,ptr])
        self.getfunction=proto(self.driver,'cuModuleGetFunction',[pp,ptr,C.c_char_p])
        self.launch=proto(self.driver,'cuLaunchKernel',[ptr,ui,ui,ui,ui,ui,ui,ui,ptr,pp,pp])
        program=ptr();self.check(self.create(C.byref(program),SOURCE.encode(),b'v4b_exact.cu',0,None,None))
        major,minor=torch.cuda.get_device_capability()
        self.options=[f'--gpu-architecture=compute_{major}{minor}','--fmad=false','--ftz=false','--prec-div=true','--std=c++14']
        opts=(C.c_char_p*len(self.options))(*(x.encode() for x in self.options))
        result=self.compile(program,len(self.options),opts)
        count=sz();self.check(self.logsize(program,C.byref(count)));log=C.create_string_buffer(count.value)
        self.check(self.log(program,log));(self.cache/'compile.log').write_bytes(log.value)
        self.check(result)
        self.check(self.ptxsize(program,C.byref(count)));self.ptx=C.create_string_buffer(count.value)
        self.check(self.getptx(program,self.ptx));self.check(self.destroy(C.byref(program)))
        (self.cache/'exact.ptx').write_bytes(self.ptx.value)
        self.module=ptr();self.function=ptr()
        self.check(self.load(C.byref(self.module),self.ptx))
        self.check(self.getfunction(C.byref(self.function),self.module,b'exact_head'))

    @staticmethod
    def check(code):
        if code:raise RuntimeError('CUDA/NVRTC error code '+str(code))

    def __call__(self,weight,hidden):
        assert weight.dtype==torch.float32 and hidden.dtype==torch.float32
        assert weight.is_cuda and hidden.is_cuda and weight.is_contiguous() and hidden.is_contiguous()
        assert weight.ndim==2 and weight.shape[1]==896 and hidden.ndim==2 and hidden.shape[1]==896
        rows=len(weight);out=torch.empty((len(hidden),rows),device=weight.device,dtype=torch.float32)
        args=[C.c_void_p(weight.data_ptr()),C.c_void_p(hidden.data_ptr()),C.c_void_p(out.data_ptr()),C.c_int(rows)]
        values=(C.c_void_p*len(args))(*(C.cast(C.byref(x),C.c_void_p) for x in args))
        self.check(self.launch(self.function,(rows+3)//4,len(hidden),1,128,1,1,0,C.c_void_p(torch.cuda.current_stream().cuda_stream),values,None))
        return out
