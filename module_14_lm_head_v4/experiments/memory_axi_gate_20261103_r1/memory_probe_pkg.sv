`timescale 1ns/1ps
package lmh_memory_probe_pkg;
integer master_ar_seen=0;
function automatic void sample(input string label,input longint amount=0);
 integer pf,rc,rss,vm,anon,file_rss,shared,fd;string line;
 rss=-1;vm=0;anon=0;file_rss=0;shared=0;pf=$fopen("/proc/self/status","r");
 if(!pf)$fatal(1,"memory probe proc open");
 while(!$feof(pf))begin
  rc=$fgets(line,pf);
  if($sscanf(line,"VmRSS: %d kB",rss)==1)continue;
  if($sscanf(line,"VmSize: %d kB",vm)==1)continue;
  if($sscanf(line,"RssAnon: %d kB",anon)==1)continue;
  if($sscanf(line,"RssFile: %d kB",file_rss)==1)continue;
  if($sscanf(line,"RssShmem: %d kB",shared)==1)continue;
 end
 $fclose(pf);if(rss<0)$fatal(1,"memory probe RSS missing");
 fd=$fopen("memory_phases.csv","a");if(!fd)$fatal(1,"memory sample open");
 $fwrite(fd,"%s,%0.0f,%0d,%0d,%0d,%0d,%0d,%0d\n",label,$realtime/1ps,amount,rss,vm,anon,file_rss,shared);$fclose(fd);
 $display("MEMORY_PHASE label=%s time_ps=%0.0f amount=%0d rss_kib=%0d vm_kib=%0d anon_kib=%0d file_kib=%0d shared_kib=%0d",label,$realtime/1ps,amount,rss,vm,anon,file_rss,shared);
endfunction
endpackage
