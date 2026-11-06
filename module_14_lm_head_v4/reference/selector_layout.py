"""Host-side companion to the private descriptor, not a board loader.

Checks full64bit physical addresses before an eventual driver programs the
HLS arena pointer. The parent HLS validates relative ranges as well.
"""
import math,struct
PHYSICAL_BASE=0x400000000
MAX_ARENA=320*1024*1024
MINIMUM=(272269312,1792,18992,38895616,229376,229376,512,8388608,512,607744,607760,607760,1215488)

def validate_descriptor(data,*,physical_base=PHYSICAL_BASE,arena_bytes=MAX_ARENA,descriptor_offset=1048576,history_address=None):
    if not isinstance(physical_base,int) or physical_base!=PHYSICAL_BASE:raise ValueError('PL DDR base must be full64bit0x400000000; PS DDR or truncated base rejected')
    if not isinstance(arena_bytes,int) or not 0<arena_bytes<=MAX_ARENA or arena_bytes%16:raise ValueError('arena')
    if not isinstance(descriptor_offset,int) or descriptor_offset<0 or descriptor_offset%16 or descriptor_offset>arena_bytes-240:raise ValueError('descriptor address')
    if len(data)!=240:raise ValueError('descriptor length')
    magic,version,count,total,reserved=struct.unpack_from('<IHHII',data)
    if (magic,version,count,total,reserved)!=(0x4353344d,1,13,240,0):raise ValueError('descriptor header')
    flags,penalty,k,reserved=struct.unpack_from('<IfII',data,16)
    if flags&~7 or k!=16384 or reserved or (flags&2 and (not math.isfinite(penalty) or penalty<1)):raise ValueError('configuration')
    intervals=[(descriptor_offset,descriptor_offset+240,'descriptor')];regions=[]
    for i,minimum in enumerate(MINIMUM):
        offset,capacity=struct.unpack_from('<QQ',data,32+i*16)
        if i==12 and not flags&1:
            if offset or capacity:raise ValueError('inactive sparse region must be zero')
            regions.append(None);continue
        if offset%16 or capacity%16 or capacity<minimum or offset>arena_bytes or capacity>arena_bytes-offset:raise ValueError('region bounds/capacity')
        intervals.append((offset,offset+capacity,str(i)))
        regions.append(dict(offset=offset,capacity=capacity,address=physical_base+offset))
    intervals.sort()
    for a,b in zip(intervals,intervals[1:]):
        if a[1]>b[0]:raise ValueError('overlap')
    expected_history=regions[2]['address']
    if history_address is not None and history_address!=expected_history:raise ValueError('history AXI pointer must match validated PL DDR region')
    return dict(flags=flags,penalty=penalty,top_k=k,regions=regions,physical_descriptor=physical_base+descriptor_offset,history_address=expected_history)
