"""Offline layouts / exact stable selection. No device, torch, EDA or MMIO.

The sorted dynamic-channel order is arithmetic input: never sort channels by
address before reducing. Sorting IO requests is allowed only with restoration.
"""
import heapq
import numpy as np

V, H = 151936, 896
BEAT = 16  # existing v4 master and MIG DATA width128, ADDRESS width64


def score_keys(scores):
    scores = np.asarray(scores, dtype=np.float32)
    if scores.ndim != 1 or not np.isfinite(scores).all():
        raise ValueError('Only finite one-dimensional FP32 scores admitted')
    bits = scores.view(np.uint32).copy()
    bits[scores == 0] = 0  # +0/-0 compare equal; leave score payload untouched
    return np.where(bits >> 31, ~bits, bits ^ np.uint32(0x80000000)).astype('u4')


def validate_t(t, n):
    if isinstance(t, bool) or not isinstance(t, int) or not 1 <= t <= n:
        raise ValueError('Top-T outside 1..N')


def top_heap(scores, t):
    """Streaming bounded heap; bigger key wins, smaller global ID breaks ties."""
    keys = score_keys(scores); validate_t(t, len(keys))
    heap = [(int(k), -i) for i, k in enumerate(keys[:t])]
    heapq.heapify(heap); replacements = 0
    for i in range(t, len(keys)):
        item = (int(keys[i]), -i)
        if item > heap[0]:
            heapq.heapreplace(heap, item); replacements += 1
    return np.array([-i for _, i in sorted(heap, reverse=True)], 'u4'), dict(
        input_rows=len(keys), resident_records=t, replacements=replacements,
        root_comparisons=len(keys)-t, final_order='CPU sorted heap; hardware can use global bitmap scan')


def top_radix(scores, t):
    """Four MSB-byte threshold passes, stable ID tie scan, final reference order.

    Histograms scan the whole cached score array on every pass. The shrinking
    NumPy mask is a software implementation detail, not claimed cycle savings.
    """
    keys = score_keys(scores); validate_t(t, len(keys))
    active = np.ones(len(keys), dtype=bool); rank = t; threshold = 0; passes = []
    for shift in (24, 16, 8, 0):
        digit = (keys >> shift) & 255
        hist = np.bincount(digit[active].astype('i8'), minlength=256)
        descending = hist[::-1].cumsum()
        bucket = 255-int(np.searchsorted(descending, rank, side='left'))
        greater = int(hist[bucket+1:].sum()); rank -= greater
        active &= digit == bucket; threshold |= bucket << shift
        passes.append(dict(shift=shift, bucket=bucket, matching_rows=int(active.sum())))
    above = np.flatnonzero(keys > threshold)
    tied = np.flatnonzero(keys == threshold)[:t-len(above)]
    chosen = np.concatenate([above, tied])
    order = np.lexsort((chosen, -np.asarray(scores)[chosen]))
    return chosen[order].astype('u4'), dict(passes=passes, threshold=int(threshold),
        histogram_counters=256, full_scan_passes=4, membership_emit_scan_passes=1,
        tie_rule='first global IDs at threshold', final_order='CPU lexsort T; hardware candidate bitmap scan needs no score sort')


def runs(ids):
    ids = np.asarray(ids, dtype=np.int64)
    if not len(ids): return np.array([], 'i8'), np.array([], 'i8')
    begins = np.r_[0, np.flatnonzero(np.diff(ids) != 1)+1]
    ends = np.r_[begins[1:], len(ids)]
    return ids[begins], ids[ends-1]+1


def interval_bursts(starts, lengths, beat=BEAT, max_beats=256):
    """Exact burst count for aligned contiguous requests, split at 4KiB.

    Payload includes complete beats. No gap coalescing, row reuse cache or DDR
    command/refresh efficiency is assumed. max_beats*beat divides4096 here.
    """
    starts=np.asarray(starts, dtype='i8'); lengths=np.asarray(lengths, dtype='i8')
    assert np.all(starts % beat == 0) and np.all(lengths % beat == 0)
    assert 4096 % (beat*max_beats) == 0
    end=starts+lengths; first_page=starts//4096; last_page=(end-1)//4096
    same=first_page == last_page; limit=beat*max_beats
    result=(lengths+limit-1)//limit
    cross=~same
    first=4096-starts[cross]%4096; tail=(end[cross]-1)%4096+1
    result[cross]=(first+limit-1)//limit + (tail+limit-1)//limit + (last_page[cross]-first_page[cross]-1)*(4096//limit)
    return dict(payload_bytes=int(lengths.sum()), bursts=int(result.sum()), requests=len(starts))


def make_tiled(bits, path, tile):
    count=(V+tile-1)//tile
    out=np.memmap(path, mode='w+', dtype='<u2', shape=(count,H,tile))
    for n in range(count):
        start=n*tile; size=min(tile,V-start); out[n]=0
        out[n,:,:size]=bits[start:start+size].T
    out.flush(); return out


def gather_tiled(tiled, ids, tile):
    """128-bit group fetch once per selected8-token group, no full tile read."""
    ids=np.asarray(ids, dtype='i8'); out=np.empty((len(ids),H), dtype='u2')
    groups=ids//8; unique,starts=np.unique(groups,return_index=True)
    for index,group in enumerate(unique):
        a=starts[index]; b=starts[index+1] if index+1<len(starts) else len(ids)
        token=int(group)*8; chunk=tiled[token//tile,:,token%tile:token%tile+8].copy()
        out[a:b]=chunk[:,ids[a:b]%8].T
    return out


def preview_tiled(tiled, tile, hidden, dims, fp, tree):
    h=fp(hidden); out=np.empty(V,'f4')
    for n in range(len(tiled)):
        size=min(tile,V-n*tile)
        # IO may be channel-ordered; multiplication/reduction stays dims-ordered.
        selected=fp(tiled[n,dims,:size]).T
        out[n*tile:n*tile+size]=tree(np.multiply(selected,h[dims],dtype=np.float32))
    return out


def traffic(ids, d, tile):
    ids=np.asarray(ids, dtype='i8'); count=(V+tile-1)//tile
    groups=np.unique(ids//8); group_runs_a,group_runs_b=runs(groups)
    # Never merge across tile/channel boundary, even when selected groups touch.
    splits=sum(int((b-1)//(tile//8)-a//(tile//8)) for a,b in zip(group_runs_a,group_runs_b))
    channel_runs=len(group_runs_a)+splits
    a,b=runs(ids)
    row=interval_bursts(a*H*2,(b-a)*H*2)
    return dict(tile_tokens=tile, preview=dict(useful_bytes=V*d*2,
        payload_bytes=count*tile*d*2,bursts=count*d,requests=count*d,
        padded_rows=count*tile-V), dual_exact=row,
        shared_exact=dict(useful_bytes=len(ids)*H*2,payload_bytes=len(groups)*H*BEAT,
            bursts=channel_runs*H,requests=channel_runs*H,
            unique_eight_token_groups=len(groups),
            read_amplification=len(groups)*8/len(ids)),
        shared_whole_selected_tiles_bytes=len(np.unique(ids//tile))*tile*H*2)


def layout_regions(weight_bytes, dual, t=4096):
    """Proposed isolated profile only. No exported ELF/loader/descriptor uses it."""
    align=65536; offset=1048576; regions=[]
    def add(name,size):
        nonlocal offset
        offset=(offset+align-1)//align*align
        regions.append(dict(name=name,offset=offset,address=hex(0x400000000+offset),
            bytes=int(size),end_exclusive=offset+int(size)))
        offset+=int(size)
        regions.append(dict(name=name+'_guard',offset=offset,address=hex(0x400000000+offset),
            bytes=align,end_exclusive=offset+align)); offset+=align
    if dual: add('canonical_row_W',V*H*2)
    add('tiled_W',weight_bytes)
    for name,size in [('rms',H*4),('hidden',H*2),('history',((V+31)//32)*4),
        ('channel_ids',128*4),('candidate_bitmap',((V+31)//32)*4),
        ('candidate_ids',(t+14)*4),('preview_scores',V*4),('radix_keys',V*4),
        ('top_records',t*8),('heap_workspace',t*8),('candidate_raw',(t+14)*4),
        ('optional_dense_debug',V*4),('exact_tile_scratch',1024*H*2),
        ('loader_crc_workspace',2*1024*1024),('descriptor_and_results',65536)]:add(name,size)
    arena=(offset+align-1)//align*align
    assert all(a['end_exclusive']<=b['offset'] for a,b in zip(regions,regions[1:]))
    assert arena<=0x80000000 and all(x['end_exclusive']<=arena for x in regions)
    return dict(status='PROPOSED_OFFLINE_NOT_DEPLOYABLE',base='0x400000000',
        aperture_bytes=0x80000000,arena_bytes=arena,regions=regions,
        prefix_guard_bytes=1048576,alignment=align,remaining_aperture_bytes=0x80000000-arena)
