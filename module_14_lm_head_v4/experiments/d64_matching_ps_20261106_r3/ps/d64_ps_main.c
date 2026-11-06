/* Offline source only. Requires matchingfinalXSA/BSP and explicitfutureboardrun.
 * One persistentDUT,12statecases then4*(3warmup+30timed+1000stable).
 * Allcompute data/snapshots/records live inPLDDR;program/stack inPSDDR.
 * PhysicalAXI transactiontrace andIPcyclecounter are NOTprovided. */
#include <stdint.h>
#include <string.h>
#include "xil_io.h"
#include "xil_mmu.h"
#include "xil_cache.h"
#include "xil_exception.h"
#include "xtime_l.h"
#include "d64_control.h"
#include "d64_cases.h"
#include "loader/loader_core.h"
_Static_assert(sizeof(UINTPTR)==8,"A53 64bitrequired");
typedef struct {uint64_t start,end,preview;uint32_t index,kind,rc,status,token,score,k,crc,valid,may_running;} record;
_Static_assert(sizeof(record)==64,"FixedrecordABI");
static uint64_t ticks(void){XTime t;XTime_GetTime(&t);return(uint64_t)t;}
static uint32_t rd(void*c,uint64_t a){(void)c;return Xil_In32((UINTPTR)a);}
static void wr(void*c,uint64_t a,uint32_t v){(void)c;Xil_Out32((UINTPTR)a,v);}
static void barrier(void*c){(void)c;__asm__ volatile("dsb sy" ::: "memory");}
static uint64_t micros(void*c){uint64_t t=ticks();(void)c;return(t/COUNTS_PER_SECOND)*1000000u+((t%COUNTS_PER_SECOND)*1000000u)/COUNTS_PER_SECOND;}
static const d64_io io={0,rd,wr,barrier,micros};
static uint32_t header[32];
static void ps_notify(unsigned status){uint32_t*mail=(uint32_t*)(UINTPTR)0x51000000u;mail[0]=0x52343644u;mail[1]=1;mail[2]=status;mail[3]=header[4];mail[4]=header[5];Xil_DCacheFlushRange((UINTPTR)mail,32);barrier(0);}
static void publish(unsigned status){header[3]=status;barrier(0);memcpy((void*)(UINTPTR)D64_STATE_RESULTS,header,sizeof header);barrier(0);ps_notify(status);}
static uint32_t target_crc(uint64_t a,unsigned n){barrier(0);return m4a_target_crc_update(0xffffffffu,(const volatile void*)(UINTPTR)a,n)^0xffffffffu;}
static void copy(uint64_t to,uint64_t from,unsigned n){barrier(0);m4a_target_copy((void*)(UINTPTR)to,(const volatile void*)(UINTPTR)from,n);barrier(0);}
static int fixture(unsigned slot){uint64_t a=D64_FIXTURES+(uint64_t)slot*D64_FIXTURE_STRIDE;if(target_crc(a,D64_META_BYTES)!=d64_meta_crc[slot])return 0;copy(D64_META,a,D64_META_BYTES);return 1;}
static int call(unsigned index,unsigned kind,const d64_case*c,uint64_t destination){d64_request q={c->capacity,c->debug,1};d64_result out;record rec;int rc;
 memset(&rec,0,sizeof rec);rec.index=index;rec.kind=kind;barrier(0);rec.start=ticks();rc=d64_call(&io,&q,60000000u,&out);rec.end=ticks();barrier(0);
 rec.preview=out.preview_beats;rec.rc=(uint32_t)rc;rec.status=out.status;rec.token=out.token;rec.score=out.score_bits;rec.k=out.k;rec.crc=out.crc;rec.valid=out.valid_mask;rec.may_running=(uint32_t)out.may_still_be_running;
 memcpy((void*)(UINTPTR)destination,&rec,sizeof rec);barrier(0);
 if(out.may_still_be_running)return 2; /* No weightrestore/reset/newcall whileIPbusy. */
 if(rc || out.status!=c->status || out.token!=c->token || out.score_bits!=c->score || out.k!=c->k || out.crc!=c->crc)return 1;
 return 0;}
int main(void){unsigned i,j,failed=0;uint64_t begin;uint32_t contract[16];
 Xil_ExceptionDisable();Xil_ICacheEnable();Xil_DCacheEnable();memset(header,0,sizeof header);header[0]=0x52343644u;header[1]=1;header[3]=0xffffffffu;header[6]=(uint32_t)COUNTS_PER_SECOND;header[7]=(uint32_t)((uint64_t)COUNTS_PER_SECOND>>32);ps_notify(0xffffffffu);
 if(rd(0,D64_GPIO+8)!=D64_SIGNATURE){ps_notify(1);return 1;}begin=ticks();while(!(rd(0,D64_GPIO)&1u)){if(ticks()-begin>(uint64_t)COUNTS_PER_SECOND*10){ps_notify(2);return 2;}}
 for(i=0;i<2;++i)Xil_SetTlbAttributes((UINTPTR)(D64_PL+(uint64_t)i*UINT64_C(0x40000000)),NORM_NONCACHE);
 barrier(0);m4a_target_copy(contract,(const volatile void*)(UINTPTR)D64_CONTRACT,sizeof contract);
 if(contract[0]!=0x43343644u || contract[1]!=1 || contract[2]!=D64_SIGNATURE || contract[3]!=D64_IMAGE_BYTES || contract[4]!=D64_META_BYTES || contract[5]!=D64_WS_BEATS || contract[6]!=D64_LOGICAL_BYTES || contract[7]!=12 || contract[8]!=4 || contract[9]!=3 || contract[10]!=30 || contract[11]!=1000 || m4a_crc(contract,56)!=contract[14]){publish(3);return 3;}
 if(target_crc(D64_TILED,273416192u)!=D64_TILED_CRC || target_crc(D64_CANONICAL,272269312u)!=D64_CANONICAL_CRC){publish(4);return 4;}header[9]=1;header[2]=1;publish(0xffffffffu);
 for(i=0;i<12;++i){const d64_case*c=&d64_cases[i];uint64_t before=D64_SNAPSHOTS+(uint64_t)(2*i)*D64_SNAPSHOT_STRIDE,after=before+D64_SNAPSHOT_STRIDE;
  if(!fixture(i)){failed=5;break;}
  if(c->mutation_offset!=0xffffffffu){if(Xil_In16((UINTPTR)(D64_TILED+c->mutation_offset))!=c->original){failed=6;break;}Xil_Out16((UINTPTR)(D64_TILED+c->mutation_offset),(uint16_t)c->replacement);barrier(0);}
  copy(before,D64_META,D64_LOGICAL_BYTES);j=(unsigned)call(i,3,c,D64_STATE_RESULTS+256u+(uint64_t)i*64u);
  if(j==2){failed=7;break;} /* Kernelmaystillrun;leaveweightrestorationtomanualrecovery. */
  copy(after,D64_META,D64_LOGICAL_BYTES);
  if(c->mutation_offset!=0xffffffffu){Xil_Out16((UINTPTR)(D64_TILED+c->mutation_offset),(uint16_t)c->original);barrier(0);}
  if(j){failed=8;break;}
  for(j=0;j<4;++j)if(Xil_In32((UINTPTR)(D64_META+D64_LOGICAL_BYTES-16u+4u*j))!=0xa5a5a5a5u)failed=9;
  if(failed)break;
  header[4]=i+1;publish(0xffffffffu);
 }
 if(!failed){header[2]=2;for(i=0;i<4 && !failed;++i){const d64_case*c=&d64_cases[12+i];if(!fixture(12+i)){failed=5;break;}
  for(j=0;j<1033;++j){unsigned kind=(i<<8)|(j<3?0u:j<33?1u:2u);unsigned n=header[5];if(call(n,kind,c,D64_TIMINGS+(uint64_t)n*64u)){failed=10;break;}header[5]=n+1;}
  publish(0xffffffffu);
 }}
 if(!failed){if(target_crc(D64_TILED,273416192u)!=D64_TILED_CRC || target_crc(D64_CANONICAL,272269312u)!=D64_CANONICAL_CRC)failed=11;else header[10]=1;}
 header[2]=3;publish(failed);return(int)failed;
}
