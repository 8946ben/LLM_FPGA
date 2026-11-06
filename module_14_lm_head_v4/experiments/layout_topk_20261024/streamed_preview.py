"""Binary carry tree: identical adjacent-pair FP32 order with log2(d) slots.

Functional model only. NumPy vector work does not assert HLS II or resources.
"""
import numpy as np


def preview(tiled,tile,hidden,dims,fp):
    d=len(dims);assert d>0 and d&(d-1)==0
    h=fp(hidden);levels=d.bit_length();v=151936
    out=np.empty(v,'f4')
    for n in range(len(tiled)):
        size=min(tile,v-n*tile);stack=np.empty((levels,size),'f4')
        for j,channel in enumerate(dims):
            value=np.multiply(fp(tiled[n,int(channel),:size]),h[channel],dtype=np.float32)
            count=j+1;level=0
            while not count&1:
                value=np.add(stack[level],value,dtype=np.float32);level+=1;count>>=1
            stack[level]=value
        out[n*tile:n*tile+size]=stack[levels-1]
    return out
