/* Diagnostic only: overwrites 256 KiB of the reserved PL DDR guard, not weights. */
#include <stdint.h>
#include <string.h>
#include "xil_cache.h"
#include "xil_mmu.h"
#include "xtime_l.h"
#include "pl_ddr_layout.h"
#include "loader_core.h"
#define BYTES (256u*1024u)
static uint64_t pattern[BYTES/8u];
struct report {
    uint32_t magic,state,bytes,byte_crc,word_crc,expected,changed_crc,changed_expected;
    uint64_t byte_ticks,word_ticks,timer_hz;
};
static struct report result;
static void publish(void) {
    memcpy((void *)(UINTPTR)0x51003000u,&result,sizeof(result));
    Xil_DCacheFlushRange((UINTPTR)0x51003000u,sizeof(result));
}
int main(void) {
    XTime a,b;
    unsigned i;
    volatile uint64_t *target=(volatile uint64_t *)(UINTPTR)M14_V31_PL_DDR_A53_BASE;
    result.magic=0x43524333u;result.state=1;result.bytes=BYTES;result.timer_hz=COUNTS_PER_SECOND;publish();
    for(i=0;i<M14_V31_PL_DDR_MMU_BLOCKS;++i)
        Xil_SetTlbAttributes((UINTPTR)M14_V31_PL_DDR_A53_BASE+i*M14_V31_PL_DDR_MMU_BLOCK_SIZE,NORM_NONCACHE);
    if((*(volatile uint32_t *)(UINTPTR)M14_V31_CALIB_GPIO_ADDR & 1u)==0u) {
        result.state=0x4641494cu;publish();return 1;
    }
    for(i=0;i<BYTES/8u;++i) {pattern[i]=0x9e3779b97f4a7c15ull*(i+1u);target[i]=pattern[i];}
    __asm__ volatile("dsb sy" ::: "memory");
    result.expected=m14_crc(pattern,BYTES);result.state=2;publish();
    XTime_GetTime(&a);
    result.byte_crc=m14_crc((const void *)(UINTPTR)M14_V31_PL_DDR_A53_BASE,BYTES);
    __asm__ volatile("dsb sy" ::: "memory");XTime_GetTime(&b);result.byte_ticks=b-a;
    result.state=3;publish();
    XTime_GetTime(&a);
    result.word_crc=m14_target_crc_update(0xffffffffu,target,BYTES)^0xffffffffu;
    __asm__ volatile("dsb sy" ::: "memory");XTime_GetTime(&b);result.word_ticks=b-a;
    target[123]^=1u;pattern[123]^=1u;__asm__ volatile("dsb sy" ::: "memory");
    result.changed_expected=m14_crc(pattern,BYTES);
    result.changed_crc=m14_target_crc_update(0xffffffffu,target,BYTES)^0xffffffffu;
    result.state=(result.byte_crc==result.expected && result.word_crc==result.expected &&
                  result.changed_crc==result.changed_expected && result.changed_crc!=result.expected)
                  ? 0x444f4e45u:0x4641494cu;
    publish();while(1) {};
}
