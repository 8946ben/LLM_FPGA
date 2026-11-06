#include "d64_control.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef struct {uint32_t m[64];uint32_t sig,cal;unsigned starts,polls,writes;uint64_t clock;int busy,corrupt,hang,invalid,badcrc,badk,nan,high;} mock;
static uint32_t read32(void*ctx,uint64_t a){mock*m=ctx;unsigned o;
 if(a==D64_GPIO+8)return m->sig;
 if(a==D64_GPIO)return m->cal;
 assert(a>=D64_CTL && a<D64_CTL+256);o=(unsigned)(a-D64_CTL);
 if(o==0){if(!m->starts)return m->busy?1u:4u;return !m->hang && ++m->polls>=3?6u:1u;}
 if(o==0x14 && m->corrupt)return m->m[o/4]^1u;
 return m->m[o/4];}
static void write32(void*ctx,uint64_t a,uint32_t v){mock*m=ctx;unsigned o=(unsigned)(a-D64_CTL);assert(a>=D64_CTL && a<D64_CTL+256);++m->writes;m->m[o/4]=v;if(o==0){unsigned j;assert(v==1);++m->starts;m->polls=0;
 for(j=0;j<6;++j)m->m[(0x54+j*16)/4]=1u;
 m->m[0xa8/4]=1u;
 m->m[0x50/4]=(m->m[0x40/4]<D64_WS_BEATS || m->m[0x48/4]>1u)?1u:0u;
 m->m[0x60/4]=m->m[0x50/4]?0u:20412u;m->m[0x70/4]=m->m[0x50/4]?0u:(m->nan?0x7fc00000u:0x41de477cu);
 m->m[0x80/4]=m->m[0x50/4]?0u:(m->badk?4111u:4109u);m->m[0x90/4]=m->m[0x50/4]?0u:d64_token_crc(m->m[0x60/4],m->m[0x70/4])^(m->badcrc?1u:0u);m->m[0xa0/4]=m->m[0x50/4]?0u:1220608u;m->m[0xa4/4]=m->high?1u:0u;if(m->invalid)m->m[0x64/4]=0;
 }}
static void barrier(void*c){(void)c;}static uint64_t now(void*c){mock*m=c;return m->clock++;}
static void init(mock*m){memset(m,0,sizeof(*m));m->sig=D64_SIGNATURE;m->cal=1;}
int main(void){mock m;d64_io io={&m,read32,write32,barrier,now};d64_request q={D64_WS_BEATS,1,1};d64_result r;unsigned cases=0;
 init(&m);assert(d64_call(&io,&q,100,&r)==D64_OK && r.token_valid && r.token==20412u && r.crc==0x1c6404e7u && m.starts==1);assert(m.m[0x14/4]==4 && m.m[0x20/4]==4 && m.m[0x2c/4]==4 && m.m[0x38/4]==4);++cases;
 init(&m);m.sig=0x4d345301;assert(d64_call(&io,&q,100,&r)==D64_WRONG_IMAGE && !m.starts);++cases;
 init(&m);m.cal=0;assert(d64_call(&io,&q,100,&r)==D64_NO_CALIBRATION && !m.starts);++cases;
 init(&m);q.weights_verified=0;assert(d64_call(&io,&q,100,&r)==D64_NOT_VERIFIED && !m.starts);q.weights_verified=1;++cases;
 init(&m);m.busy=1;assert(d64_call(&io,&q,100,&r)==D64_BUSY && !m.starts);++cases;
 init(&m);m.corrupt=1;assert(d64_call(&io,&q,100,&r)==D64_READBACK && !m.starts);++cases;
 init(&m);m.hang=1;assert(d64_call(&io,&q,3,&r)==D64_TIMEOUT && r.may_still_be_running && m.starts==1);++cases;
 init(&m);m.invalid=1;assert(d64_call(&io,&q,100,&r)==D64_VALID_MISSING && !r.token_valid);++cases;
 init(&m);m.badcrc=1;assert(d64_call(&io,&q,100,&r)==D64_BAD_RESULT && !r.token_valid);++cases;
 init(&m);m.badk=1;assert(d64_call(&io,&q,100,&r)==D64_BAD_RESULT);++cases;
 init(&m);m.nan=1;assert(d64_call(&io,&q,100,&r)==D64_BAD_RESULT);++cases;
 init(&m);m.high=1;assert(d64_call(&io,&q,100,&r)==D64_BAD_RESULT);++cases;
 init(&m);q.capacity_beats=D64_WS_BEATS-1;assert(d64_call(&io,&q,100,&r)==D64_OK && r.status==1 && !r.token_valid && m.starts==1);q.capacity_beats=D64_WS_BEATS;++cases;
 init(&m);q.debug=2;assert(d64_call(&io,&q,100,&r)==D64_OK && r.status==1 && !r.token_valid);q.debug=1;++cases;
 init(&m);assert(d64_call(&io,&q,0,&r)==D64_ARGUMENT && !m.starts);++cases;
 printf("D64_CONTROL_HOST_PASS cases=%u\n",cases);return 0;}
