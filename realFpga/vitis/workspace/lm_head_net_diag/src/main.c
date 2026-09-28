/*
 * Copyright (C) 2009 - 2019 Xilinx, Inc.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without modification,
 * are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 *    this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the documentation
 *    and/or other materials provided with the distribution.
 * 3. The name of the author may not be used to endorse or promote products
 *    derived from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR IMPLIED
 * WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
 * SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
 * EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
 * OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
 * IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY
 * OF SUCH DAMAGE.
 *
 */

#include <stdio.h>

#include "xparameters.h"

#include "netif/xadapter.h"

#include "platform.h"
#include "platform_config.h"
#include "lmh_buffers.h"
#if defined (__arm__) || defined(__aarch64__)
#include "xil_printf.h"
#endif

#include "lwip/tcp.h"
#include "xil_cache.h"

#define DDR_TEST_BASE  ((UINTPTR)0x10000000U)
#define DDR_TEST_WORDS 4096U

#if LWIP_IPV6==1
#include "lwip/ip.h"
#else
#if LWIP_DHCP==1
#include "lwip/dhcp.h"
#endif
#endif

/* defined by each RAW mode application */
void print_app_header();
int start_application();
int transfer_data();
void tcp_fasttmr(void);
void tcp_slowtmr(void);

/* missing declaration in lwIP */
void lwip_init();

#if LWIP_IPV6==0
#if LWIP_DHCP==1
extern volatile int dhcp_timoutcntr;
err_t dhcp_start(struct netif *netif);
#endif
#endif

extern volatile int TcpFastTmrFlag;
extern volatile int TcpSlowTmrFlag;
static struct netif server_netif;
struct netif *echo_netif;

static int lmh_buffer_layout_check(void)
{
	const UINTPTR weight_bytes =
			(UINTPTR)__lmh_weight_end - (UINTPTR)__lmh_weight_start;
	const UINTPTR hidden_bytes =
			(UINTPTR)__lmh_hidden_end - (UINTPTR)__lmh_hidden_start;
	const UINTPTR history_bytes =
			(UINTPTR)__lmh_history_end - (UINTPTR)__lmh_history_start;
	const UINTPTR logits_bytes =
			(UINTPTR)__lmh_logits_end - (UINTPTR)__lmh_logits_start;
	const UINTPTR network_rx_bytes =
			(UINTPTR)__lmh_network_rx_end -
			(UINTPTR)__lmh_network_rx_start;

	if ((weight_bytes != LMH_WEIGHT_BYTES) ||
			(hidden_bytes != LMH_HIDDEN_BYTES) ||
			(history_bytes != LMH_HISTORY_BYTES) ||
			(logits_bytes != LMH_LOGITS_BYTES) ||
			(network_rx_bytes != LMH_NETWORK_RX_BYTES)) {
		xil_printf("LMH DDR layout FAIL: unexpected buffer size\r\n");
		return -1;
	}

	if (((LMH_WEIGHT_ADDR | LMH_HIDDEN_ADDR | LMH_HISTORY_ADDR |
			LMH_LOGITS_ADDR | LMH_NETWORK_RX_ADDR) &
			(LMH_BUFFER_ALIGNMENT - 1U)) != 0U) {
		xil_printf("LMH DDR layout FAIL: address is not 64-byte aligned\r\n");
		return -1;
	}

	xil_printf("LMH DDR layout PASS\r\n");
	xil_printf("  weight : 0x%08lx - 0x%08lx (%lu bytes)\r\n",
			(unsigned long)LMH_WEIGHT_ADDR,
			(unsigned long)(UINTPTR)__lmh_weight_end,
			(unsigned long)weight_bytes);
	xil_printf("  hidden : 0x%08lx - 0x%08lx (%lu bytes)\r\n",
			(unsigned long)LMH_HIDDEN_ADDR,
			(unsigned long)(UINTPTR)__lmh_hidden_end,
			(unsigned long)hidden_bytes);
	xil_printf("  history: 0x%08lx - 0x%08lx (%lu bytes)\r\n",
			(unsigned long)LMH_HISTORY_ADDR,
			(unsigned long)(UINTPTR)__lmh_history_end,
			(unsigned long)history_bytes);
	xil_printf("  logits : 0x%08lx - 0x%08lx (%lu bytes)\r\n",
			(unsigned long)LMH_LOGITS_ADDR,
			(unsigned long)(UINTPTR)__lmh_logits_end,
			(unsigned long)logits_bytes);
	xil_printf("  net rx : 0x%08lx - 0x%08lx (%lu bytes)\r\n",
			(unsigned long)LMH_NETWORK_RX_ADDR,
			(unsigned long)(UINTPTR)__lmh_network_rx_end,
			(unsigned long)network_rx_bytes);
	return 0;
}

/*
 * 2026-07-24 zb: Small non-destructive-for-this-application DDR smoke test.
 * The selected 64 KiB test window is far above the linked application image.
 */
static int ddr_smoke_test(void)
{
	volatile u32 *test_area = (volatile u32 *)DDR_TEST_BASE;
	u32 i;
	u32 expected;

	xil_printf("DDR smoke test: base=0x%08lx, bytes=%lu\r\n",
			(unsigned long)DDR_TEST_BASE,
			(unsigned long)(DDR_TEST_WORDS * sizeof(u32)));

	for (i = 0; i < DDR_TEST_WORDS; ++i) {
		test_area[i] = 0xA5A50000U ^ i;
	}
	Xil_DCacheFlushRange(DDR_TEST_BASE, DDR_TEST_WORDS * sizeof(u32));
	Xil_DCacheInvalidateRange(DDR_TEST_BASE, DDR_TEST_WORDS * sizeof(u32));

	for (i = 0; i < DDR_TEST_WORDS; ++i) {
		expected = 0xA5A50000U ^ i;
		if (test_area[i] != expected) {
			xil_printf("DDR smoke test FAIL at 0x%08lx: expected=0x%08lx actual=0x%08lx\r\n",
					(unsigned long)(DDR_TEST_BASE + i * sizeof(u32)),
					(unsigned long)expected,
					(unsigned long)test_area[i]);
			return -1;
		}
	}

	xil_printf("DDR smoke test PASS\r\n");
	return 0;
}

#if LWIP_IPV6==1
void print_ip6(char *msg, ip_addr_t *ip)
{
	print(msg);
	xil_printf(" %x:%x:%x:%x:%x:%x:%x:%x\n\r",
			IP6_ADDR_BLOCK1(&ip->u_addr.ip6),
			IP6_ADDR_BLOCK2(&ip->u_addr.ip6),
			IP6_ADDR_BLOCK3(&ip->u_addr.ip6),
			IP6_ADDR_BLOCK4(&ip->u_addr.ip6),
			IP6_ADDR_BLOCK5(&ip->u_addr.ip6),
			IP6_ADDR_BLOCK6(&ip->u_addr.ip6),
			IP6_ADDR_BLOCK7(&ip->u_addr.ip6),
			IP6_ADDR_BLOCK8(&ip->u_addr.ip6));

}
#else
void
print_ip(char *msg, ip_addr_t *ip)
{
	print(msg);
	xil_printf("%d.%d.%d.%d\n\r", ip4_addr1(ip), ip4_addr2(ip),
			ip4_addr3(ip), ip4_addr4(ip));
}

void
print_ip_settings(ip_addr_t *ip, ip_addr_t *mask, ip_addr_t *gw)
{

	print_ip("Board IP: ", ip);
	print_ip("Netmask : ", mask);
	print_ip("Gateway : ", gw);
}
#endif

#if defined (__arm__) && !defined (ARMR5)
#if XPAR_GIGE_PCS_PMA_SGMII_CORE_PRESENT == 1 || XPAR_GIGE_PCS_PMA_1000BASEX_CORE_PRESENT == 1
int ProgramSi5324(void);
int ProgramSfpPhy(void);
#endif
#endif

#ifdef XPS_BOARD_ZCU102
#ifdef XPAR_XIICPS_0_DEVICE_ID
int IicPhyReset(void);
#endif
#endif

int main()
{
#if LWIP_IPV6==0
	ip_addr_t ipaddr, netmask, gw;

#endif
	/* the mac address of the board. this should be unique per board */
	unsigned char mac_ethernet_address[] =
	{ 0x00, 0x0a, 0x35, 0x00, 0x01, 0x02 };

	echo_netif = &server_netif;
#if defined (__arm__) && !defined (ARMR5)
#if XPAR_GIGE_PCS_PMA_SGMII_CORE_PRESENT == 1 || XPAR_GIGE_PCS_PMA_1000BASEX_CORE_PRESENT == 1
	ProgramSi5324();
	ProgramSfpPhy();
#endif
#endif

/* Define this board specific macro in order perform PHY reset on ZCU102 */
#ifdef XPS_BOARD_ZCU102
	if(IicPhyReset()) {
		xil_printf("Error performing PHY reset \n\r");
		return -1;
	}
#endif

	init_platform();

	if (lmh_buffer_layout_check() != 0) {
		xil_printf("Stopping because the LM Head DDR layout is invalid.\r\n");
		return -1;
	}

	if (ddr_smoke_test() != 0) {
		xil_printf("Stopping before network initialization because DDR test failed.\r\n");
		return -1;
	}

#if LWIP_IPV6==0
#if LWIP_DHCP==1
    ipaddr.addr = 0;
	gw.addr = 0;
	netmask.addr = 0;
#else
	/* initialize IP addresses to be used */
	IP4_ADDR(&ipaddr,  192, 168,   8, 190);
	IP4_ADDR(&netmask, 255, 255, 255,  0);
	IP4_ADDR(&gw,      192, 168,   8,   1);
#endif
#endif
	print_app_header();

	lwip_init();

#if (LWIP_IPV6 == 0)
	/* Add network interface to the netif_list, and set it as default */
	if (!xemac_add(echo_netif, &ipaddr, &netmask,
						&gw, mac_ethernet_address,
						PLATFORM_EMAC_BASEADDR)) {
		xil_printf("Error adding N/W interface\n\r");
		return -1;
	}
#else
	/* Add network interface to the netif_list, and set it as default */
	if (!xemac_add(echo_netif, NULL, NULL, NULL, mac_ethernet_address,
						PLATFORM_EMAC_BASEADDR)) {
		xil_printf("Error adding N/W interface\n\r");
		return -1;
	}
	echo_netif->ip6_autoconfig_enabled = 1;

	netif_create_ip6_linklocal_address(echo_netif, 1);
	netif_ip6_addr_set_state(echo_netif, 0, IP6_ADDR_VALID);

	print_ip6("\n\rBoard IPv6 address ", &echo_netif->ip6_addr[0].u_addr.ip6);

#endif
	netif_set_default(echo_netif);

	/* now enable interrupts */
	platform_enable_interrupts();

	/* specify that the network if is up */
	netif_set_up(echo_netif);

#if (LWIP_IPV6 == 0)
#if (LWIP_DHCP==1)
	/* Create a new DHCP client for this interface.
	 * Note: you must call dhcp_fine_tmr() and dhcp_coarse_tmr() at
	 * the predefined regular intervals after starting the client.
	 */
	dhcp_start(echo_netif);
	dhcp_timoutcntr = 24;

	while(((echo_netif->ip_addr.addr) == 0) && (dhcp_timoutcntr > 0))
		xemacif_input(echo_netif);

	if (dhcp_timoutcntr <= 0) {
		if ((echo_netif->ip_addr.addr) == 0) {
			xil_printf("DHCP Timeout\r\n");
			xil_printf("Configuring default IP of 192.168.1.10\r\n");
			IP4_ADDR(&(echo_netif->ip_addr),  192, 168,   1, 10);
			IP4_ADDR(&(echo_netif->netmask), 255, 255, 255,  0);
			IP4_ADDR(&(echo_netif->gw),      192, 168,   1,  1);
		}
	}

	ipaddr.addr = echo_netif->ip_addr.addr;
	gw.addr = echo_netif->gw.addr;
	netmask.addr = echo_netif->netmask.addr;
#endif

	print_ip_settings(&ipaddr, &netmask, &gw);

#endif
	/* 2026-07-24 zb: do not enter the network loop if LMH1/IP init failed. */
	if (start_application() != 0) {
		xil_printf("Stopping because the LM Head service failed to start.\r\n");
		return -1;
	}

	/* receive and process packets */
	while (1) {
		if (TcpFastTmrFlag) {
			tcp_fasttmr();
			TcpFastTmrFlag = 0;
		}
		if (TcpSlowTmrFlag) {
			tcp_slowtmr();
			TcpSlowTmrFlag = 0;
		}
		xemacif_input(echo_netif);
		transfer_data();
	}

	/* never reached */
	cleanup_platform();

	return 0;
}
