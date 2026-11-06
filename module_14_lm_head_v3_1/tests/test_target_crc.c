#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>
#include "loader_core.h"

static unsigned checks;
static uint32_t reference(uint32_t state,const uint8_t *p,size_t n) {
    while(n--) {
        unsigned j;
        state^=*p++;
        for(j=0;j<8;++j) state=(state>>1)^((state&1u)?0xedb88320u:0);
    }
    return state;
}
static void compare(const uint8_t *p,size_t n,uint32_t seed) {
    uint32_t a=m14_target_crc_update(seed,p,n),b=reference(seed,p,n);
    if(a!=b) {fprintf(stderr,"CRC mismatch bytes=%zu seed=%08x\n",n,seed);exit(1);}
    ++checks;
}
int main(void) {
    static uint64_t words[18000];
    static const size_t sizes[]={0,1,2,3,7,8,9,15,16,17,31,63,64,65,127,128,
        255,256,1023,4095,4096,16383,16384,16385,32767,32768,65535,65536,131072};
    uint8_t *data=(uint8_t *)words;
    size_t i,offset,k;
    uint32_t seed=0x12345678u;
    for(i=0;i<sizeof(words);++i) {seed^=seed<<13;seed^=seed>>17;seed^=seed<<5;data[i]=(uint8_t)seed;}
    for(offset=0;offset<16;++offset) for(k=0;k<sizeof(sizes)/sizeof(sizes[0]);++k) {
        compare(data+offset,sizes[k],0xffffffffu);
        compare(data+offset,sizes[k],0x12345678u);
    }
    if((m14_target_crc_update(0xffffffffu,"123456789",9)^0xffffffffu)!=0xcbf43926u) return 2;
    ++checks;
    seed=0xffffffffu;
    for(i=0;i<131072;) {
        size_t n=(i*7u+13u)%17003u+1u;
        if(n>131072-i) n=131072-i;
        seed=m14_target_crc_update(seed,data+3+i,n);i+=n;
    }
    if(seed!=reference(0xffffffffu,data+3,131072)) return 3;
    ++checks;
    seed=m14_target_crc_update(0xffffffffu,data,131072);
    data[65537]^=1;
    compare(data,131072,0xffffffffu);
    if(seed==m14_target_crc_update(0xffffffffu,data,131072)) return 4;
    ++checks;
    {
        SYSTEM_INFO info;DWORD old;
        uint8_t *pages;
        GetSystemInfo(&info);
        pages=VirtualAlloc(NULL,info.dwPageSize*2,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE);
        if(!pages || !VirtualProtect(pages+info.dwPageSize,info.dwPageSize,PAGE_NOACCESS,&old)) return 5;
        memset(pages,0xa5,info.dwPageSize);
        for(i=0;i<=65;++i) compare(pages+info.dwPageSize-i,i,0xffffffffu);
        compare(pages,info.dwPageSize,0xffffffffu);
        VirtualFree(pages,0,MEM_RELEASE);
    }
    printf("M14_TARGET_CRC_HOST=PASS checks=%u guard_page=PASS hardware_access=NONE\n",checks);
    return 0;
}
