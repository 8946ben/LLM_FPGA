#include "../standalone/arena_loader/loader_core.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static uint32_t slow_crc(const unsigned char *p,size_t n) {
    uint32_t c=0xffffffffu;size_t i;unsigned b;
    for(i=0;i<n;++i){c^=p[i];for(b=0;b<8;++b)c=(c>>1)^((0u-(c&1u))&0xedb88320u);}
    return c^0xffffffffu;
}
static m4a_header header(unsigned op,unsigned seq,unsigned off,unsigned size,unsigned crc) {
    m4a_header h={M4A_WIRE_MAGIC,M4A_WIRE_VERSION,op,seq,off,size,M4A_IMAGE_BYTES,crc};return h;
}
int main(void) {
    m4a_loader s={0};m4a_header h,r,d;uint8_t wire[32];uint64_t address=0;
    unsigned i,j;static unsigned char source[33024],dest[33024];
    const size_t lengths[]={0,1,7,8,9,15,16,16383,16384,16385,32787};
    assert(M4A_WIRE_MAGIC==0x5241344du && M4A_IMAGE_BYTES==335544320u);
    assert(m4a_crc("123456789",9)==0xcbf43926u);
    assert(m4a_crc("",0)==0);
    h=header(M4A_BEGIN,0,0,0,0x89abcdefu);m4a_encode(wire,&h);
    assert(memcmp(wire,"M4AR\1\0\0\0\1\0\0\0",12)==0);
    assert(wire[28]==0xef && wire[29]==0xcd && wire[30]==0xab && wire[31]==0x89);
    m4a_decode(&d,wire);assert(memcmp(&d,&h,sizeof(h))==0);

    assert(m4a_target_window(0,1,&address) && address==UINT64_C(0x400000000));
    assert(m4a_target_window(M4A_IMAGE_BYTES-1,1,&address));
    assert(address==M4A_TARGET_BASE+M4A_IMAGE_BYTES-1 && address>UINT32_MAX);
    assert(!m4a_target_window(M4A_IMAGE_BYTES,1,&address));
    assert(!m4a_target_window(UINT64_MAX,1,&address));
    assert(!m4a_target_window(16,UINT64_MAX,&address));
    assert(!m4a_target_window(0,1,NULL));

    assert(m4a_validate(&s,&h)==M4A_OK);
    h.magic=0x5734314du;assert(m4a_validate(&s,&h)==M4A_BAD_HEADER);h.magic=M4A_WIRE_MAGIC;
    h.total=272269312u;assert(m4a_validate(&s,&h)==M4A_BAD_HEADER);h.total=M4A_IMAGE_BYTES;
    h.version=2;assert(m4a_validate(&s,&h)==M4A_BAD_HEADER);h.version=1;
    h.seq=1;assert(m4a_validate(&s,&h)==M4A_BAD_HEADER);
    h=header(M4A_DATA,1,0,1,0);assert(m4a_validate(&s,&h)==M4A_NOT_READY);
    h=header(M4A_STATUS,123,0,0,0);assert(m4a_validate(&s,&h)==M4A_OK);
    s.active=1;s.seq=1;
    h=header(M4A_DATA,1,0,M4A_CHUNK_BYTES,0);assert(m4a_validate(&s,&h)==M4A_OK);
    h.size=M4A_CHUNK_BYTES+1;assert(m4a_validate(&s,&h)==M4A_BAD_HEADER);
    h.size=0;assert(m4a_validate(&s,&h)==M4A_BAD_HEADER);
    h.size=1;h.offset=1;assert(m4a_validate(&s,&h)==M4A_BAD_ORDER);
    h.offset=0;h.seq=2;assert(m4a_validate(&s,&h)==M4A_BAD_ORDER);
    s.next=M4A_IMAGE_BYTES-1;h=header(M4A_DATA,1,s.next,1,0);assert(m4a_validate(&s,&h)==M4A_OK);
    h.size=2;assert(m4a_validate(&s,&h)==M4A_BAD_HEADER);
    s.next=UINT32_MAX;h.offset=UINT32_MAX;assert(m4a_validate(&s,&h)==M4A_BAD_HEADER);
    s.next=M4A_IMAGE_BYTES;s.expected_crc=0x12345678u;
    h=header(M4A_COMMIT,1,s.next,0,s.expected_crc);assert(m4a_validate(&s,&h)==M4A_OK);
    h.crc^=1;assert(m4a_validate(&s,&h)==M4A_BAD_ORDER);
    h=header(M4A_READ,400,0,0,240);assert(m4a_validate(&s,&h)==M4A_NOT_READY);
    s.active=0;s.ready=1;assert(m4a_validate(&s,&h)==M4A_OK);
    h.crc=0;assert(m4a_validate(&s,&h)==M4A_BAD_HEADER);
    h.crc=513;assert(m4a_validate(&s,&h)==M4A_BAD_HEADER);
    h.crc=512;h.offset=M4A_IMAGE_BYTES-512;assert(m4a_validate(&s,&h)==M4A_OK);
    h.offset++;assert(m4a_validate(&s,&h)==M4A_BAD_HEADER);
    h=header(M4A_READ,400,1048576,0,240);m4a_reply(&r,&s,&h,M4A_OK,0xa5);
    assert(r.offset==h.offset && r.crc==0xa5 && r.op==(M4A_READ|0x80000000u) && r.seq==400 && r.size==0);
    {unsigned ack=0;
     assert(!m4a_reply_ack(&ack,544,32) && ack==32);
     assert(!m4a_reply_ack(&ack,544,1) && ack==33);
     assert(m4a_reply_ack(&ack,544,511) && ack==544);
     assert(!m4a_reply_ack(&ack,544,1) && ack==544);
     ack=0;assert(!m4a_reply_ack(&ack,32,16));assert(m4a_reply_ack(&ack,32,16));
     ack=0;assert(!m4a_reply_ack(&ack,544,UINT32_MAX) && ack==0);
     assert(!m4a_reply_ack(&ack,31,31) && ack==0);}

    for(i=0;i<sizeof(source);++i)source[i]=(unsigned char)((i*29u)^(i>>5));
    for(i=0;i<8;++i)for(j=0;j<sizeof(lengths)/sizeof(lengths[0]);++j) {
        size_t n=lengths[j];uint32_t expected=slow_crc(source+i,n),c;
        memset(dest,0x5a,sizeof(dest));m4a_target_copy(dest+3,source+i,n);
        assert(memcmp(dest+3,source+i,n)==0 && dest[2]==0x5a && dest[n+3]==0x5a);
        c=m4a_target_crc_update(0xffffffffu,source+i,n)^0xffffffffu;
        assert(c==expected);
    }
    {uint32_t c=m4a_target_crc_update(0xffffffffu,source+3,16381);
     c=m4a_target_crc_update(c,source+3+16381,16390)^0xffffffffu;
     assert(c==slow_crc(source+3,32771));}
    puts("M4A_LOADER_CORE_HOST=PASS protocol_bounds_crc_copy; 88 alignment/length combinations; no PL DDR or network");
    return 0;
}
