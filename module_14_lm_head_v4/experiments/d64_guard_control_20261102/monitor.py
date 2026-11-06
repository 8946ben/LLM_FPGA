def group_snapshot(group):
 rows=[]
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   stat=(p/'stat').read_text();v=stat[stat.rindex(')')+2:].split()
   if v[0]!='Z' and int(v[2])==group:
    rows.append(dict(pid=int(p.name),start_ticks=v[19],rss_kib=int(v[21])*os.sysconf('SC_PAGE_SIZE')//1024))
  except OSError:pass
 return rows

def tool(phase,command,cwd,timeout):
 state.update(state='EXECUTING_'+phase.upper(),phase=phase);save()
 def stop_owned(p):
  try:os.killpg(p.pid,signal.SIGTERM)
  except ProcessLookupError:pass
  try:p.wait(timeout=15)
  except subprocess.TimeoutExpired:
   try:os.killpg(p.pid,signal.SIGKILL)
   except ProcessLookupError:pass
   p.wait()
 with (R/(phase+'.log')).open('w') as out,(R/(phase+'_resources.jsonl')).open('w') as resources:
  p=subprocess.Popen(['bash','-c','source /tools/Xilinx/Vitis/2022.2/settings64.sh >/dev/null 2>&1; exec '+command],cwd=cwd,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
  state.update(child_pid=p.pid,child_pgid=p.pid,command=command);save();start=time.monotonic();peak=0
  try:
   while True:
    procs=group_snapshot(p.pid);rss=sum(x['rss_kib'] for x in procs);peak=max(peak,rss)
    available=next(int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'))
    elapsed=time.monotonic()-start
    sample=dict(utc=stamp(),elapsed_s=elapsed,group_rss_kib=rss,available_kib=available,members=procs)
    resources.write(json.dumps(sample)+'\n');resources.flush()
    if p.poll() is not None:break
    reason=('STOP_REQUESTED' if (R/'STOP_REQUESTED').exists() else 'PHASE_TIMEOUT' if elapsed>timeout else 'MEM_AVAILABLE_BELOW_32GIB' if available<32*1024*1024 else 'GROUP_RSS_ABOVE_128GIB' if rss>128*1024*1024 else None)
    if reason:
     state['stop_evidence']=dict(reason=reason,phase=phase,timeout_seconds=timeout,**sample);save();stop_owned(p);raise RuntimeError(reason)
    time.sleep(5)
   assert p.returncode==0,(phase,p.returncode)
   assert not members(p.pid),'Residual owned group'
   state.setdefault('phase_resources',{})[phase]=dict(elapsed_s=elapsed,peak_group_rss_kib=peak,returncode=p.returncode);save()
  except BaseException:
   stop_owned(p);raise
