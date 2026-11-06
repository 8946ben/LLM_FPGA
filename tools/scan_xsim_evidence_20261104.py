"""Bounded-memory log facts for independent post-return RTL evidence review."""
from pathlib import Path
import hashlib,re

FIFO_PATTERN=r'^DF_FIFO_RLE_SUMMARY file=(\S+) depth_samples=(\d+) block_samples=(\d+) end_depth=(\d+) max_depth=(\d+) pushes=(\d+) pops=(\d+) clamped_reads=(\d+)$'
RANGE_PATTERN=r'^LMH_RANGE_GUARD_SUMMARY meta_read_bursts=(\d+) meta_write_bursts=(\d+) weight_read_bursts=(\d+)$'

def scan_xsim_log(path):
    path=Path(path);before=path.stat();errors=[];error_count=0;warnings=[];warning_count=0
    ranges=[];range_count=0;fifos=[];fifo_count=0;sentinels=0;lines=0;warning_hash=hashlib.sha256()
    # Universal newline handling matches the old read_text parser. Refuse an
    # implausibly huge individual line rather than allocating an unbounded one.
    with path.open('r',encoding='utf-8',errors='replace',newline=None) as source:
        while True:
            line=source.readline(1048576)
            if not line:break
            if len(line)==1048576 and not line.endswith('\n'):raise ValueError('Log line exceeds1MiB guard')
            line=line.rstrip('\n');lines+=1
            if line.startswith(('UVM_FATAL','UVM_ERROR','ERROR:','Fatal:')) and not re.fullmatch(r'UVM_(?:ERROR|FATAL)\s*:\s*0\s*',line):
                error_count+=1
                if len(errors)<8:errors.append(line)
            if line=='BANK_FULL_INPUT_SENTINEL_PASS checked=1522':sentinels+=1
            match=re.fullmatch(RANGE_PATTERN,line)
            if match:
                range_count+=1
                if len(ranges)<8:ranges.append(match.groups())
            match=re.fullmatch(FIFO_PATTERN,line)
            if match:
                fifo_count+=1
                if len(fifos)<8:fifos.append(match.groups())
            if 'DSP' in line and ('Warning' in line or 'WARNING' in line):
                warning_count+=1;warning_hash.update((line+'\n').encode('utf-8'))
                if len(warnings)<8 and line not in warnings:warnings.append(line)
    middle=path.stat();assert (before.st_size,before.st_mtime_ns)==(middle.st_size,middle.st_mtime_ns),'Log changed during scan'
    digest=hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda:source.read(1048576),b''):digest.update(block)
    after=path.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'Log changed during hashing'
    return dict(bytes=before.st_size,lines=lines,sha256=digest.hexdigest(),error_count=error_count,error_examples=errors,
        sentinel_pass_count=sentinels,range_guard_count=range_count,range_guard_rows=ranges,fifo_summary_count=fifo_count,fifo_summary_rows=fifos,
        dsp_warning_count=warning_count,dsp_warning_examples=warnings,normalized_warning_lines_sha256=warning_hash.hexdigest(),
        warning_scope='All warning lines counted/hashed in order; at most8 distinct examples retained. Numeric effect is decided only by bitwise outputs.')
