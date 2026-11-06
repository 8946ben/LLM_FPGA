#include "loader/loader_core.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void){m4a_loader s={0};m4a_header h={M4A_WIRE_MAGIC,M4A_WIRE_VERSION,M4A_BEGIN,0,0,0,M4A_IMAGE_BYTES,0},x;uint64_t a;unsigned ack=0;uint8_t b[32];
 assert(M4A_IMAGE_BYTES==603979776u && M4A_WIRE_MAGIC==0x41343644u);
 assert(m4a_target_window(M4A_IMAGE_BYTES-16,16,&a) && a==UINT64_C(0x423fffff0));assert(!m4a_target_window(M4A_IMAGE_BYTES-16,17,&a));assert(!m4a_target_window(UINT64_C(0x100000000),16,&a));
 assert(m4a_validate(&s,&h)==M4A_OK);m4a_encode(b,&h);m4a_decode(&x,b);assert(!memcmp(&h,&x,sizeof h));h.magic=0x5241344d;assert(m4a_validate(&s,&h)==M4A_BAD_HEADER);h.magic=M4A_WIRE_MAGIC;h.total=335544320;assert(m4a_validate(&s,&h)==M4A_BAD_HEADER);h.total=M4A_IMAGE_BYTES;
 h.op=D64_ATTACH_READ_ONLY;assert(m4a_validate(&s,&h)==M4A_OK);s.active=1;assert(m4a_validate(&s,&h)==M4A_BAD_HEADER);s.active=0;s.read_only=1;assert(!s.ready);h.op=M4A_READ;h.crc=16;h.offset=M4A_IMAGE_BYTES-16;assert(m4a_validate(&s,&h)==M4A_OK);h.crc=17;assert(m4a_validate(&s,&h)==M4A_BAD_HEADER);h.crc=16;s.read_only=0;assert(m4a_validate(&s,&h)==M4A_NOT_READY);s.ready=1;assert(m4a_validate(&s,&h)==M4A_OK);
 h.op=M4A_DATA;h.offset=0;h.crc=0;h.size=1;assert(m4a_validate(&s,&h)==M4A_NOT_READY);s.active=1;s.next=0;s.seq=h.seq=1;assert(m4a_validate(&s,&h)==M4A_OK);h.offset=1;assert(m4a_validate(&s,&h)==M4A_BAD_ORDER);
 assert(m4a_crc("123456789",9)==0xcbf43926u);assert(!m4a_reply_ack(&ack,48,32));assert(m4a_reply_ack(&ack,48,16));assert(!m4a_reply_ack(&ack,48,1));puts("D64_LOADER_HOST_PASS bounds/protocol/read_only_not_verified/CRC/partialACK");return 0;}
