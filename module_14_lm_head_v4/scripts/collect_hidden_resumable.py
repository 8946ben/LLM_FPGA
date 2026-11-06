"""Run unchanged numeric collector with bounded Windows atomic-I/O retries.

Only module.write is replaced. The original collector/model/policy source SHA
remains truthful and unchanged; this transport wrapper has separate provenance.
"""
from pathlib import Path
import hashlib,importlib.util,json,sys,time

IO_STATS=dict(writes=0,retries=0,retry_files=[])
def atomic_write(path,data):
    path=Path(path);temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    deadline=time.monotonic()+3
    while True:
        try:temp.replace(path);IO_STATS['writes']+=1;return
        except PermissionError as error:
            if getattr(error,'winerror',None) not in (5,32,33) or time.monotonic()>=deadline:raise
            IO_STATS['retries']+=1
            if str(path) not in IO_STATS['retry_files']:IO_STATS['retry_files'].append(str(path))
            time.sleep(.025)

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    m=Path(__file__).resolve().parents[1];source=m/'scripts/collect_hidden.py'
    arguments=sys.argv[1:]
    out=Path(arguments[arguments.index('--out')+1]) if '--out' in arguments else m/'data/hidden_v1'
    split=arguments[arguments.index('--split')+1] if '--split' in arguments else 'train'
    expected=json.loads((out/'train/SETTINGS.json').read_text(encoding='utf-8'))['collector_sha256']
    assert sha(source)==expected,'This wrapper is not permission to bypass numeric-source changes'
    provenance=dict(original_collector_sha256=expected,io_wrapper_sha256=sha(Path(__file__)),
        change='Override module.write only: same JSON bytes + bounded3s retry for Windows5/32/33; numerical/model/policy code unchanged',split=split,state='RUNNING')
    out.mkdir(parents=True,exist_ok=True);report=out/('IO_WRAPPER_'+split+'.json');atomic_write(report,provenance)
    try:
        spec=importlib.util.spec_from_file_location('_m14_collector_original',source)
        module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
        module.write=atomic_write
        module.main();provenance['state']='COMPLETED'
    except BaseException:
        provenance['state']='FAILED';raise
    finally:
        provenance['io_stats']=IO_STATS.copy();atomic_write(report,provenance)
if __name__=='__main__':main()
