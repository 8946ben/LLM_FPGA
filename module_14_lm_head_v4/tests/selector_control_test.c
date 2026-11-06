#include "../standalone/selector_control.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define PL UINT64_C(0x400000000)
#define DESC UINT64_C(1048576)
#define CTRL UINT64_C(0xA0000000)
#define GPIO UINT64_C(0xA0020000)
typedef struct {uint32_t regs[64],descriptor[60],signature,cal;unsigned writes,starts,barriers;uint64_t clock;int mode;} Fake;
static uint32_t read32(void*p,uint64_t addr){Fake*f=p;
 if(addr==GPIO+8)return f->signature;
 if(addr==GPIO)return f->cal;
 if(addr>=PL+DESC && addr<PL+DESC+240)return f->descriptor[(addr-PL-DESC)/4];
 assert(addr>=CTRL && addr<CTRL+256);if(f->mode==4 && addr==CTRL+0x14)return 0;
 return f->regs[(addr-CTRL)/4];}
static void write32(void*p,uint64_t addr,uint32_t value){Fake*f=p;assert(addr>=CTRL && addr<CTRL+256);++f->writes;f->regs[(addr-CTRL)/4]=value;
 if(addr==CTRL && value==1){++f->starts;if(f->mode==5){f->regs[0]=0;return;}f->regs[0]=6;
 f->regs[0x48/4]=f->mode==6?5:0;f->regs[0x58/4]=f->regs[0x40/4]?1:6;f->regs[0x68/4]=f->mode==6?2:0;
 f->regs[0x78/4]=8527;f->regs[0x88/4]=21529;f->regs[0xa8/4]=20412;f->regs[0xb8/4]=0x41de477c;f->regs[0xc8/4]=f->mode==7?0:0x1c6404e7;
 if(f->mode==8)f->regs[0x88/4]=0;
 if(f->mode==9)f->regs[0xa8/4]=151936;
 if(f->mode==10)f->regs[0xb8/4]=0x7fc00000;
 if(f->mode==11)f->regs[0x58/4]=4;
 if(f->mode==12)f->regs[0x98/4]=2;
 }}
static void barrier(void*p){++((Fake*)p)->barriers;}
static uint64_t time_us(void*p){Fake*f=p;f->clock+=10;return f->clock;}
static void init(Fake*f,const uint32_t*d){memset(f,0,sizeof(*f));memcpy(f->descriptor,d,240);f->signature=0x4d345301;f->cal=1;f->regs[0]=4;}
int main(int argc,char**argv){assert(argc==2);uint32_t descriptor[60];FILE*fp=fopen(argv[1],"rb");assert(fp && fread(descriptor,1,240,fp)==240);fclose(fp);Fake f;lmh4_result out;lmh4_io io={&f,read32,write32,barrier,time_us};unsigned cases=0;
 init(&f,descriptor);assert(lmh4_control_call(&io,0,1,1000,&out)==CTL_OK && out.token_valid && out.token==20412 && f.starts==1);assert(f.regs[0x14/4]==4 && f.regs[0x20/4]==4);++cases;
 init(&f,descriptor);assert(lmh4_control_call(&io,1,0,1000,&out)==CTL_OK && !out.token_valid && out.stage==1);++cases;
 init(&f,descriptor);f.signature=0;assert(lmh4_control_call(&io,0,1,1000,&out)==CTL_WRONG_IMAGE && f.writes==0);++cases;
 init(&f,descriptor);f.cal=0;assert(lmh4_control_call(&io,0,1,1000,&out)==CTL_NOT_CALIBRATED && f.writes==0);++cases;
 init(&f,descriptor);assert(lmh4_control_call(&io,0,0,1000,&out)==CTL_NOT_VERIFIED && f.writes==0);++cases;
 init(&f,descriptor);f.descriptor[0]=0;assert(lmh4_control_call(&io,0,1,1000,&out)==CTL_BAD_DESCRIPTOR && f.writes==0);++cases;
 init(&f,descriptor);f.regs[0]=0;assert(lmh4_control_call(&io,0,1,1000,&out)==CTL_BUSY && f.writes==0);++cases;
 init(&f,descriptor);f.mode=4;assert(lmh4_control_call(&io,0,1,1000,&out)==CTL_READBACK && f.starts==0 && !out.token_valid);++cases;
 init(&f,descriptor);f.mode=5;assert(lmh4_control_call(&io,0,1,20,&out)==CTL_TIMEOUT && out.may_still_be_running && !out.token_valid);++cases;
 init(&f,descriptor);f.mode=6;assert(lmh4_control_call(&io,0,1,1000,&out)==CTL_HARDWARE_FAILED && !out.token_valid && out.child_status==2);++cases;
 init(&f,descriptor);f.mode=7;assert(lmh4_control_call(&io,0,1,1000,&out)==CTL_BAD_RESULT && !out.token_valid);++cases;
 for(int mode=8;mode<=12;++mode){init(&f,descriptor);f.mode=mode;assert(lmh4_control_call(&io,0,1,1000,&out)==CTL_BAD_RESULT && !out.token_valid);++cases;}
 for(unsigned i=0;i<9;++i){init(&f,descriptor);
   if(i==0)f.descriptor[3]=1;
   if(i==1)f.descriptor[4]=8;
   if(i==2)f.descriptor[5]=0x3f000000;
   if(i==3)f.descriptor[5]=0x7fc00000;
   if(i==4)f.descriptor[8]+=1;
   if(i==5){f.descriptor[8]=0xfffffff0;f.descriptor[9]=0xffffffff;}
   if(i==6){f.descriptor[10]=0xfffffff0;f.descriptor[11]=0xffffffff;}
   if(i==7){f.descriptor[8+10*4]=f.descriptor[8+11*4];f.descriptor[9+10*4]=f.descriptor[9+11*4];}
   if(i==8)f.descriptor[4]=6;
   assert(lmh4_control_call(&io,0,1,1000,&out)==CTL_BAD_DESCRIPTOR && f.writes==0);++cases;
 }
 printf("SELECTOR_CONTROL_HOST_TEST=PASS cases=%u fake_MMIO_only\n",cases);return 0;}
