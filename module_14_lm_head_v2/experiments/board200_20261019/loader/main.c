#include <stdint.h>
#include <string.h>
#include "loader_core.h"
#include "platform.h"
#include "platform_config.h"
#include "lwip/init.h"
#include "lwip/tcp.h"
#include "lwip/priv/tcp_priv.h"
#include "netif/xadapter.h"
#include "xil_cache.h"
#include "xil_printf.h"
#include "xparameters.h"
#include "xtime_l.h"
#define WEIGHT_ADDR ((UINTPTR)0x40000000u)
extern volatile int TcpFastTmrFlag, TcpSlowTmrFlag;
struct netif iface;
struct netif *echo_netif=&iface;
static m14_loader state;
static struct tcp_pcb *client;
static uint8_t header_bytes[32], payload[M14_CHUNK_BYTES], reply_bytes[32];
static unsigned header_used, payload_used;
static m14_header request;
static int reply_pending, commit_pending, reply_queued;
static uint32_t commit_offset, commit_crc;
static XTime last_activity;
/* Last 16 protocol events at a separate diagnostic window; never weight data. */
static uint32_t diagnostic_sequence;
static void diagnostic(uint32_t event, uint32_t detail) {
    uint32_t words[16]={++diagnostic_sequence,event,detail,header_used,payload_used,
        request.op,request.seq,request.size,state.next,(uint32_t)state.active,
        (uint32_t)state.ready,(uint32_t)reply_pending,(uint32_t)reply_queued,
        (uint32_t)commit_pending,request.crc,0};
    UINTPTR address=(UINTPTR)0x51001000u+((diagnostic_sequence-1u)%16u)*64u;
    memcpy((void *)address,words,sizeof(words));
    Xil_DCacheFlushRange(address,sizeof(words));
}
static void reset_connection(void) {
    client=NULL; header_used=payload_used=0;
    reply_pending=commit_pending=reply_queued=0;
    if(state.active) { state.active=0; state.ready=0; }
}
static void on_error(void *arg, err_t err) { (void)arg; (void)err; reset_connection(); }
static void respond(uint32_t status, uint32_t crc) {
    m14_header reply;
    m14_reply(&reply,&state,&request,status,crc);
    m14_encode(reply_bytes,&reply);
    reply_pending=1; reply_queued=0;
    header_used=payload_used=0;
    diagnostic(3,status);
}
static void process(void) {
    uint32_t crc;
    if(request.op==M14_BEGIN) {
        state.next=0; state.seq=1; state.expected_crc=request.crc;
        state.active=1; state.ready=0; respond(M14_OK,request.crc);
    } else if(request.op==M14_STATUS) {
        respond(state.ready ? M14_OK:M14_NOT_READY,state.ready ? state.expected_crc:0);
    } else if(request.op==M14_DATA) {
        crc=m14_crc(payload,request.size);
        if(crc!=request.crc) { state.active=state.ready=0; respond(M14_BAD_CRC,crc); return; }
        memcpy((void *)(WEIGHT_ADDR+state.next),payload,request.size);
        /* Flush before invalidation: the readback must reach DDR, not dirty cache. */
        Xil_DCacheFlushRange(WEIGHT_ADDR+state.next,request.size);
        Xil_DCacheInvalidateRange(WEIGHT_ADDR+state.next,request.size);
        crc=m14_crc((const void *)(WEIGHT_ADDR+state.next),request.size);
        if(crc!=request.crc) { state.active=state.ready=0; respond(M14_DDR_ERROR,crc); return; }
        state.next+=request.size; ++state.seq; respond(M14_OK,crc);
    } else {
        commit_pending=1; commit_offset=0; commit_crc=0xffffffffu;
    }
}
static err_t on_sent(void *arg, struct tcp_pcb *pcb, u16_t len) {
    (void)arg; (void)pcb; (void)len;
    /* Only one 32-byte response may be outstanding. */
    if(reply_queued) { reply_pending=0; reply_queued=0; }
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
                    m14_decode(&request,header_bytes); status=m14_validate(&state,&request);
                    diagnostic(2,(uint32_t)status);
                    if(status!=M14_OK) {
                        /* Invalid lengths are never consumed or copied to DDR. */
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
    init_platform(); lwip_init();
    IP4_ADDR(&ip,192,168,0,190); IP4_ADDR(&mask,255,255,255,0); IP4_ADDR(&gw,0,0,0,0);
    if(!xemac_add(&iface,&ip,&mask,&gw,mac,PLATFORM_EMAC_BASEADDR)) return 1;
    netif_set_default(&iface); platform_enable_interrupts(); netif_set_up(&iface);
    listener=tcp_new(); if(!listener) return 2;
    if(tcp_bind(listener,IP_ADDR_ANY,1414)!=ERR_OK) return 3;
    bound=tcp_listen(listener); if(!bound) return 4;
    tcp_accept(bound,on_accept);
    xil_printf("M14_TCP_LOADER_READY ip=192.168.0.190 port=1414 bytes=%lu\r\n",(unsigned long)M14_WEIGHT_BYTES);
    while(1) {
        XTime now;
        if(TcpFastTmrFlag) { tcp_fasttmr(); TcpFastTmrFlag=0; }
        if(TcpSlowTmrFlag) { tcp_slowtmr(); TcpSlowTmrFlag=0; }
        xemacif_input(&iface);
        if(client && commit_pending) {
            /* Bound each scan slice so network timers keep running. */
            uint32_t n=M14_WEIGHT_BYTES-commit_offset;
            if(n>65536) n=65536;
            Xil_DCacheInvalidateRange(WEIGHT_ADDR+commit_offset,n);
            commit_crc=m14_crc_update(commit_crc,(const void *)(WEIGHT_ADDR+commit_offset),n);
            commit_offset+=n; XTime_GetTime(&last_activity);
            if(commit_offset==M14_WEIGHT_BYTES) {
                uint32_t crc=commit_crc^0xffffffffu;
                commit_pending=0; state.active=0; state.ready=(crc==state.expected_crc);
                respond(state.ready ? M14_OK:M14_DDR_ERROR,crc);
                xil_printf("M14_TCP_WEIGHT_COMMIT ready=%d crc=0x%08lx\r\n",state.ready,(unsigned long)crc);
            }
        }
        if(client && reply_pending && !reply_queued) {
            err_t status=tcp_write(client,reply_bytes,32,TCP_WRITE_FLAG_COPY);
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
        if(client && now-last_activity>(XTime)COUNTS_PER_SECOND*60) {
            diagnostic(0xe3,0);
            tcp_abort(client); reset_connection();
        }
    }
}
