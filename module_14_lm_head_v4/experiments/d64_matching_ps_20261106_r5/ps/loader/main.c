#include <stdint.h>
#include <string.h>
#include "loader_core.h"
#include "platform.h"
#include "platform_config.h"
#include "lwip/init.h"
#include "lwip/tcp.h"
#include "lwip/sys.h"
#include "lwip/priv/tcp_priv.h"
#include "netif/xadapter.h"
#include "netif/xemacpsif.h"
#include "xil_cache.h"
#include "xil_mmu.h"
#include "arena_layout.h"
#include "xil_printf.h"
#include "xparameters.h"
#include "xtime_l.h"
/* Adapted from v3.1: v4 loads the complete576MiB d64 image into PL DDR.
 * The A53 and both d64 masters use the same64bit system addresses. */
#define ARENA_ADDR ((UINTPTR)LMH4_PRIVATE_ARENA_A53)
#define PL_DDR_BASE ((UINTPTR)LMH4_PRIVATE_PL_DDR_A53_BASE)
#define CALIB_GPIO ((volatile uint32_t *)LMH4_PRIVATE_CALIB_GPIO_ADDR)
_Static_assert(sizeof(UINTPTR)==8,"Private arena loader requires64bit A53 UINTPTR");
extern volatile int TcpFastTmrFlag, TcpSlowTmrFlag;
extern u32_t tcp_ticks;
struct netif iface;
struct netif *echo_netif=&iface;
static m4a_loader state;
static struct tcp_pcb *client;
static uint8_t header_bytes[32], payload[M4A_CHUNK_BYTES], reply_bytes[32+M4A_READ_MAX];
static unsigned reply_length,reply_acked;
static unsigned header_used, payload_used;
static m4a_header request;
static int reply_pending, commit_pending, reply_queued;
static uint32_t commit_offset, commit_crc;
static XTime last_activity;
static XTime last_tx_kick;
/* Last 16 protocol events at a separate diagnostic window; never weight data. */
static uint32_t diagnostic_sequence;
static int hardware_ok(void) {
    return CALIB_GPIO[2]==LMH4_PRIVATE_SIGNATURE &&
           (CALIB_GPIO[0]&LMH4_PRIVATE_CALIB_BIT)!=0u &&
           ((*(volatile uint32_t *)(UINTPTR)LMH4_PRIVATE_SELECTOR_CTRL)&0x85u)==4u;
}
/* Map the PL DDR aperture as Normal Non-cacheable: the A53 must never hold a
 * private dirty copy of data that the HLS masters read from the same memory. */
static void pl_ddr_mmu_init(void) {
    unsigned index;
    for (index=0; index<LMH4_PRIVATE_PL_DDR_MMU_BLOCKS; ++index) {
        Xil_SetTlbAttributes(PL_DDR_BASE + index*LMH4_PRIVATE_PL_DDR_MMU_BLOCK_SIZE,
                             NORM_NONCACHE);
    }
}
/* Calibration must complete before the first DDR access.  The MIG output is
 * also gated into the AXI clock converter reset, so an early access stalls
 * instead of corrupting memory. */
static int pl_ddr_wait_calib(void) {
    XTime start, now;
    XTime_GetTime(&start);
    while ((*CALIB_GPIO & LMH4_PRIVATE_CALIB_BIT) == 0u) {
        XTime_GetTime(&now);
        if (now-start > (XTime)COUNTS_PER_SECOND*10u) return 0;
    }
    return 1;
}
static void diagnostic(uint32_t event, uint32_t detail) {
    uint32_t words[16]={++diagnostic_sequence,event,detail,header_used,payload_used,
        request.op,request.seq,request.size,state.next,(uint32_t)state.active,
        (uint32_t)state.ready,(uint32_t)reply_pending,(uint32_t)reply_queued,
        (uint32_t)commit_pending,request.crc,tcp_ticks};
    UINTPTR address=(UINTPTR)0x51001000u+((diagnostic_sequence-1u)%16u)*64u;
    memcpy((void *)address,words,sizeof(words));
    Xil_DCacheFlushRange(address,sizeof(words));
    if(client) {
        uint32_t debug[32]={diagnostic_sequence,event,tcp_ticks,(uint32_t)client->state,
            client->flags,client->nrtx,(uint32_t)client->rtime,(uint32_t)client->rto,
            client->snd_nxt,client->lastack,client->snd_lbb,client->snd_wnd,client->cwnd,
            (uint32_t)(UINTPTR)client->unsent,(uint32_t)(UINTPTR)client->unacked,
            client->snd_queuelen,client->snd_buf,client->rcv_nxt,client->rcv_wnd,client->mss};
        struct xemac_s *adapter=(struct xemac_s *)iface.state;
        xemacpsif_s *mac=(xemacpsif_s *)adapter->state;
        XEmacPs_BdRing *ring=&(XEmacPs_GetTxRing(&mac->emacps));
        debug[20]=ring->FreeCnt; debug[21]=ring->HwCnt;
        debug[22]=ring->PreCnt; debug[23]=ring->PostCnt;
        debug[24]=XEmacPs_ReadReg(mac->emacps.Config.BaseAddress,XEMACPS_TXSR_OFFSET);
        debug[25]=XEmacPs_ReadReg(mac->emacps.Config.BaseAddress,XEMACPS_NWCTRL_OFFSET);
        memcpy((void *)(UINTPTR)0x51002000u,debug,sizeof(debug));
        Xil_DCacheFlushRange((UINTPTR)0x51002000u,sizeof(debug));
    }
}
static void reset_connection(void) {
    client=NULL; header_used=payload_used=0;
    reply_pending=commit_pending=reply_queued=0;
    reply_length=reply_acked=0;
    if(state.active) { state.active=0; state.ready=0; }
}
static void retry_pending_mac_tx(void) {
    SYS_ARCH_DECL_PROTECT(level);
    struct xemac_s *adapter=(struct xemac_s *)iface.state;
    xemacpsif_s *mac=(xemacpsif_s *)adapter->state;
    XEmacPs_BdRing *ring=&(XEmacPs_GetTxRing(&mac->emacps));
    SYS_ARCH_PROTECT(level);
    if(ring->HwCnt && !(XEmacPs_ReadReg(mac->emacps.Config.BaseAddress,
                                     XEMACPS_TXSR_OFFSET)&XEMACPS_TXSR_TXGO_MASK)) {
        /* Resume the existing DMA queue; do not enqueue a duplicate TCP reply. */
        XEmacPs_Transmit(&mac->emacps);
    }
    SYS_ARCH_UNPROTECT(level);
}
static void on_error(void *arg, err_t err) { (void)arg; (void)err; reset_connection(); }
static void respond(uint32_t status, uint32_t crc) {
    m4a_header reply;
    m4a_reply(&reply,&state,&request,status,crc);
    m4a_encode(reply_bytes,&reply);
    reply_pending=1; reply_queued=0;
    reply_length=32;reply_acked=0;
    header_used=payload_used=0;
    diagnostic(3,status);
}
static uint32_t target_crc_update(uint32_t crc, UINTPTR address, size_t bytes) {
    uint32_t result;
    __asm__ volatile("dsb sy" ::: "memory");
    result=m4a_target_crc_update(crc,(const volatile void *)address,bytes);
    __asm__ volatile("dsb sy" ::: "memory");
    return result;
}
static void process(void) {
    uint32_t crc;
    uint64_t address;
    if(!hardware_ok()) {
        state.active=state.ready=0;respond(M4A_NOT_READY,0);return;
    }
    if(request.op==M4A_BEGIN) {
        state.next=0; state.seq=1; state.expected_crc=request.crc;
        state.active=1; state.ready=0;state.read_only=0; respond(M4A_OK,request.crc);
    } else if(request.op==D64_ATTACH_READ_ONLY) {
        state.active=0;state.ready=0;state.read_only=1;respond(M4A_OK,0);
    } else if(request.op==M4A_STATUS) {
        respond(state.ready ? M4A_OK:M4A_NOT_READY,state.ready ? state.expected_crc:0);
    } else if(request.op==M4A_DATA) {
        crc=m4a_crc(payload,request.size);
        if(crc!=request.crc) { state.active=state.ready=0; respond(M4A_BAD_CRC,crc); return; }
        if(!m4a_target_window(state.next,request.size,&address)) {
            state.active=state.ready=0;respond(M4A_BAD_HEADER,0);return;
        }
        memcpy((void *)(UINTPTR)address,payload,request.size);
        /* Flush before invalidation: the readback must reach DDR, not dirty cache. */
        Xil_DCacheFlushRange(ARENA_ADDR+state.next,request.size);
        Xil_DCacheInvalidateRange(ARENA_ADDR+state.next,request.size);
        crc=target_crc_update(0xffffffffu,ARENA_ADDR+state.next,request.size)^0xffffffffu;
        if(crc!=request.crc) { state.active=state.ready=0; respond(M4A_DDR_ERROR,crc); return; }
        state.next+=request.size; ++state.seq; respond(M4A_OK,crc);
    } else if(request.op==M4A_READ) {
        unsigned n=request.crc;
        if(!m4a_target_window(request.offset,n,&address)) {
            state.active=state.ready=0;respond(M4A_BAD_HEADER,0);return;
        }
        __asm__ volatile("dsb sy" ::: "memory");
        m4a_target_copy(reply_bytes+32,(const volatile void *)(UINTPTR)address,n);
        __asm__ volatile("dsb sy" ::: "memory");
        crc=m4a_crc(reply_bytes+32,n);
        respond(M4A_OK,crc);reply_length=32+n;
    } else {
        commit_pending=1; commit_offset=0; commit_crc=0xffffffffu;
    }
}
static err_t on_sent(void *arg, struct tcp_pcb *pcb, u16_t len) {
    (void)arg; (void)pcb; (void)len;
    /* One complete response (header plus optional READ body) outstanding.
     * A partial cumulative ACK must not release the response buffer. */
    if(reply_queued) {
        if(m4a_reply_ack(&reply_acked,reply_length,len)) {reply_pending=0;reply_queued=0;}
    }
    diagnostic(4,len);
    return ERR_OK;
}
static err_t on_recv(void *arg, struct tcp_pcb *pcb, struct pbuf *p, err_t err) {
    struct pbuf *q; (void)arg;
    diagnostic(1,p ? p->tot_len:0);
    if(!p) {
        tcp_arg(pcb,NULL); tcp_recv(pcb,NULL); tcp_err(pcb,NULL); tcp_sent(pcb,NULL);
        if(tcp_close(pcb)!=ERR_OK) {
            tcp_abort(pcb); reset_connection(); return ERR_ABRT;
        }
        reset_connection(); return ERR_OK;
    }
    if(err!=ERR_OK) { pbuf_free(p); return err; }
    XTime_GetTime(&last_activity);
    /* Clients must wait for each response. A pipelined request is rejected. */
    if(reply_pending || commit_pending) {
        diagnostic(0xe1,0);
        pbuf_free(p); tcp_abort(pcb); reset_connection(); return ERR_ABRT;
    }
    for(q=p;q;q=q->next) {
        const uint8_t *src=q->payload; unsigned remaining=q->len;
        while(remaining) {
            unsigned n;
            if(header_used<32) {
                n=32-header_used; if(n>remaining) n=remaining;
                memcpy(header_bytes+header_used,src,n); header_used+=n; src+=n; remaining-=n;
                if(header_used==32) {
                    int status;
                    m4a_decode(&request,header_bytes); status=m4a_validate(&state,&request);
                    diagnostic(2,(uint32_t)status);
                    if(status!=M4A_OK) {
                        /* Invalid lengths are never consumed or copied to DDR. */
                        state.active=state.ready=0;
                        pbuf_free(p); tcp_abort(pcb); reset_connection(); return ERR_ABRT;
                    }
                    if(!request.size) process();
                }
            } else {
                n=request.size-payload_used; if(n>remaining) n=remaining;
                memcpy(payload+payload_used,src,n); payload_used+=n; src+=n; remaining-=n;
                if(payload_used==request.size) process();
            }
            if((reply_pending || commit_pending) && (remaining || q->next)) {
                diagnostic(0xe2,remaining);
                pbuf_free(p); tcp_abort(pcb); reset_connection(); return ERR_ABRT;
            }
        }
    }
    tcp_recved(pcb,p->tot_len); pbuf_free(p); return ERR_OK;
}
static err_t on_accept(void *arg, struct tcp_pcb *pcb, err_t err) {
    (void)arg;
    if(err!=ERR_OK) return err;
    if(client) { tcp_abort(pcb); return ERR_ABRT; }
    client=pcb; tcp_recv(pcb,on_recv); tcp_err(pcb,on_error); tcp_sent(pcb,on_sent);
    tcp_nagle_disable(pcb); XTime_GetTime(&last_activity); return ERR_OK;
}
int main(void) {
    ip_addr_t ip, mask, gw;
    unsigned char mac[6]={0x00,0x0a,0x35,0x00,0x01,0x14};
    struct tcp_pcb *listener, *bound;
    init_platform();
    if(CALIB_GPIO[2]!=LMH4_PRIVATE_SIGNATURE) {
        xil_printf("D64A_TCP_LOADER_WRONG_IMAGE\r\n");return 6;
    }
    pl_ddr_mmu_init();
    if (!pl_ddr_wait_calib()) {
        xil_printf("D64A_TCP_LOADER_CALIB_FAIL\r\n");
        return 5;
    }
    if(!hardware_ok()) {
        xil_printf("D64A_TCP_LOADER_SELECTOR_BUSY\r\n");return 7;
    }
    xil_printf("D64A_TCP_LOADER_PL_DDR base=0x%08lx arena=0x%08lx\r\n",
               (unsigned long)PL_DDR_BASE, (unsigned long)ARENA_ADDR);
    lwip_init();
    IP4_ADDR(&ip,192,168,0,190); IP4_ADDR(&mask,255,255,255,0); IP4_ADDR(&gw,0,0,0,0);
    if(!xemac_add(&iface,&ip,&mask,&gw,mac,PLATFORM_EMAC_BASEADDR)) return 1;
    netif_set_default(&iface); platform_enable_interrupts(); netif_set_up(&iface);
    listener=tcp_new(); if(!listener) return 2;
    if(tcp_bind(listener,IP_ADDR_ANY,1416)!=ERR_OK) return 3;
    bound=tcp_listen(listener); if(!bound) return 4;
    tcp_accept(bound,on_accept);
    xil_printf("D64A_TCP_LOADER_READY ip=192.168.0.190 port=1416 bytes=%lu\r\n",(unsigned long)M4A_IMAGE_BYTES);
    while(1) {
        XTime now;
        if(TcpFastTmrFlag) { tcp_fasttmr(); TcpFastTmrFlag=0; }
        if(TcpSlowTmrFlag) { tcp_slowtmr(); TcpSlowTmrFlag=0; }
        xemacif_input(&iface);
        if(client && commit_pending) {
            if(!hardware_ok()) {
                commit_pending=0;state.active=state.ready=0;
                respond(M4A_NOT_READY,0);continue;
            }
            /* Bound each scan slice so network timers keep running. */
            uint32_t n=M4A_IMAGE_BYTES-commit_offset;
            if(n>65536) n=65536;
            Xil_DCacheInvalidateRange(ARENA_ADDR+commit_offset,n);
            commit_crc=target_crc_update(commit_crc,ARENA_ADDR+commit_offset,n);
            commit_offset+=n; XTime_GetTime(&last_activity);
            if(commit_offset==M4A_IMAGE_BYTES) {
                uint32_t crc=commit_crc^0xffffffffu;
                commit_pending=0; state.active=0; state.ready=(crc==state.expected_crc);
                respond(state.ready ? M4A_OK:M4A_DDR_ERROR,crc);
                xil_printf("D64A_TCP_ARENA_COMMIT ready=%d crc=0x%08lx\r\n",state.ready,(unsigned long)crc);
            }
        }
        if(client && reply_pending && !reply_queued) {
            err_t status=tcp_write(client,reply_bytes,(u16_t)reply_length,TCP_WRITE_FLAG_COPY);
            if(status==ERR_OK) { reply_queued=1; }
            else if(status!=ERR_MEM) { tcp_abort(client); reset_connection(); }
        }
        if(client && reply_queued) {
            /* tcp_write acceptance does not guarantee DMA transmit acceptance.
             * Retry an unsent reply when a burst of small RX packets/ACKs fills
             * the Ethernet TX ring; never queue a duplicate reply. */
            err_t status=tcp_output(client);
            if(status!=ERR_OK && status!=ERR_MEM && status!=ERR_BUF) {
                diagnostic(0xe4,(uint32_t)status);
                tcp_abort(client); reset_connection();
            }
        }
        XTime_GetTime(&now);
        if(client && reply_queued && now-last_tx_kick>(XTime)COUNTS_PER_SECOND/4u) {
            last_tx_kick=now;
            retry_pending_mac_tx();
        }
        if(client && now-last_activity>(XTime)COUNTS_PER_SECOND*60) {
            diagnostic(0xe3,0);
            tcp_abort(client); reset_connection();
        }
    }
}
