#include "d64_control.h"
#include <string.h>
static void wr64(const d64_io*i,unsigned o,uint64_t v){i->write32(i->ctx,D64_CTL+o,(uint32_t)v);i->write32(i->ctx,D64_CTL+o+4,(uint32_t)(v>>32));}
static uint64_t rd64(const d64_io*i,unsigned o){uint32_t l=i->read32(i->ctx,D64_CTL+o),h=i->read32(i->ctx,D64_CTL+o+4);return (uint64_t)l|((uint64_t)h<<32);}
uint32_t d64_token_crc(uint32_t t,uint32_t v){uint32_t c=0xffffffffu;unsigned j,b;for(j=0;j<8;++j){c^=((j<4?t:v)>>(8*(j&3)))&255u;for(b=0;b<8;++b)c=(c>>1)^((0u-(c&1u))&0xedb88320u);}return c^0xffffffffu;}
int d64_call(const d64_io*i,const d64_request*q,uint64_t timeout,d64_result*r){
 unsigned j;uint64_t begin;static const unsigned offsets[6]={0x50,0x60,0x70,0x80,0x90,0xa0};uint32_t values[6];
 if(!r)return D64_ARGUMENT;
 memset(r,0,sizeof(*r));
 if(!i||!q||!i->read32||!i->write32||!i->barrier||!i->now_us||!timeout||timeout>60000000u)return D64_ARGUMENT;
 if(i->read32(i->ctx,D64_GPIO+8)!=D64_SIGNATURE)return D64_WRONG_IMAGE;
 if(!(i->read32(i->ctx,D64_GPIO)&1u))return D64_NO_CALIBRATION;
 if(!q->weights_verified)return D64_NOT_VERIFIED;
 if((i->read32(i->ctx,D64_CTL)&0x85u)!=4u)return D64_BUSY;
 wr64(i,0x10,D64_META);wr64(i,0x1c,D64_TILED);wr64(i,0x28,D64_CANONICAL);wr64(i,0x34,D64_WORKSPACE);
 i->write32(i->ctx,D64_CTL+0x40,q->capacity_beats);i->write32(i->ctx,D64_CTL+0x48,q->debug);i->barrier(i->ctx);
 if(rd64(i,0x10)!=D64_META||rd64(i,0x1c)!=D64_TILED||rd64(i,0x28)!=D64_CANONICAL||rd64(i,0x34)!=D64_WORKSPACE||i->read32(i->ctx,D64_CTL+0x40)!=q->capacity_beats||i->read32(i->ctx,D64_CTL+0x48)!=q->debug)return D64_READBACK;
 begin=i->now_us(i->ctx);i->write32(i->ctx,D64_CTL,1);r->launched=1;i->barrier(i->ctx);
 for(;;){if(i->read32(i->ctx,D64_CTL)&2u)break;if(i->now_us(i->ctx)-begin>=timeout){r->wait_us=i->now_us(i->ctx)-begin;r->may_still_be_running=1;return D64_TIMEOUT;}}
 r->wait_us=i->now_us(i->ctx)-begin;i->barrier(i->ctx);
 for(j=0;j<6;++j){values[j]=i->read32(i->ctx,D64_CTL+offsets[j]);if(i->read32(i->ctx,D64_CTL+offsets[j]+(j==5?8u:4u))&1u)r->valid_mask|=1u<<j;}
 r->status=values[0];r->token=values[1];r->score_bits=values[2];r->k=values[3];r->crc=values[4];r->preview_beats=(uint64_t)values[5]|((uint64_t)i->read32(i->ctx,D64_CTL+0xa4)<<32);
 if(r->valid_mask!=63u)return D64_VALID_MISSING;
 if(!r->status){if(r->token>=151936u||r->k<4096u||r->k>4110u||(r->score_bits&0x7f800000u)==0x7f800000u||r->preview_beats!=1220608u||r->crc!=d64_token_crc(r->token,r->score_bits))return D64_BAD_RESULT;r->token_valid=1;}
 return D64_OK;
}
