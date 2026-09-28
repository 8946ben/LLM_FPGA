/*
 * Replace the Vitis lwip_echo_server src/echo.c with this file.
 *
 * Protocol, little-endian:
 * request  = 8B "OFRMSRQ1" + u64 request_id + u32 row_count + u32 hidden_size
 *          + u32 eps_bits + u32 input_bytes + u32 weight_bytes + u32 flags
 *          + input_bf16[row_count * 896] + weight_bf16[896]
 * response = 8B "OFRMSRP1" + u64 request_id + u32 status + u32 output_bytes
 *          + u32 hw_time_us + u32 total_time_us + output_or_error_payload
 */

#include <stdint.h>
#include <string.h>

#include "lwip/err.h"
#include "lwip/tcp.h"
#include "xil_cache.h"
#include "xil_printf.h"
#include "xparameters.h"
#include "xrmsnorm_layer0_prefill.h"
#include "xtime_l.h"

#ifndef RMSNORM_DEVICE_ID
#if defined(XPAR_XRMSNORM_LAYER0_PREFILL_0_DEVICE_ID)
#define RMSNORM_DEVICE_ID XPAR_XRMSNORM_LAYER0_PREFILL_0_DEVICE_ID
#elif defined(XPAR_RMSNORM_LAYER0_PREFILL_0_DEVICE_ID)
#define RMSNORM_DEVICE_ID XPAR_RMSNORM_LAYER0_PREFILL_0_DEVICE_ID
#else
#error "Cannot find RMSNorm HLS IP device ID macro in xparameters.h"
#endif
#endif

#define RMS_RAW_PORT 50052U
#define RMS_FIXED_ROWS 36U
#define RMS_HIDDEN_SIZE 896U
#define RMS_ELEMENT_BYTES 2U
#define RMS_FIXED_ELEMENTS (RMS_FIXED_ROWS * RMS_HIDDEN_SIZE)
#define RMS_INPUT_BYTES (RMS_FIXED_ELEMENTS * RMS_ELEMENT_BYTES)
#define RMS_WEIGHT_BYTES (RMS_HIDDEN_SIZE * RMS_ELEMENT_BYTES)
#define RMS_OUTPUT_BYTES (RMS_FIXED_ELEMENTS * RMS_ELEMENT_BYTES)
#define RMS_REQUEST_MAGIC "OFRMSRQ1"
#define RMS_RESPONSE_MAGIC "OFRMSRP1"
#define RMS_STATUS_OK 0U
#define RMS_STATUS_ERROR 1U
#define RMS_MAX_REQUEST_BYTES (sizeof(rms_raw_request_header_t) + RMS_INPUT_BYTES + RMS_WEIGHT_BYTES)
#define RMS_MAX_RESPONSE_BYTES (sizeof(rms_raw_response_header_t) + RMS_OUTPUT_BYTES)
#define RMS_IP_TIMEOUT_POLLS 100000000U

typedef struct __attribute__((packed)) {
    uint8_t magic[8];
    uint64_t request_id;
    uint32_t row_count;
    uint32_t hidden_size;
    uint32_t eps_bits;
    uint32_t input_bytes;
    uint32_t weight_bytes;
    uint32_t flags;
} rms_raw_request_header_t;

typedef struct __attribute__((packed)) {
    uint8_t magic[8];
    uint64_t request_id;
    uint32_t status;
    uint32_t output_bytes;
    uint32_t hw_time_us;
    uint32_t total_time_us;
} rms_raw_response_header_t;

typedef struct {
    uint8_t rx_buffer[RMS_MAX_REQUEST_BYTES] __attribute__((aligned(64)));
    uint8_t tx_buffer[RMS_MAX_RESPONSE_BYTES] __attribute__((aligned(64)));
    uint32_t rx_len;
    uint32_t expected_len;
    uint32_t tx_len;
    uint32_t tx_offset;
} rms_tcp_session_t;

static XRmsnorm_layer0_prefill rms_ip;
static int rms_ip_ready = 0;
static rms_tcp_session_t tcp_session;
static uint16_t input_buf[RMS_FIXED_ELEMENTS] __attribute__((aligned(64)));
static uint16_t weight_buf[RMS_HIDDEN_SIZE] __attribute__((aligned(64)));
static uint16_t output_buf[RMS_FIXED_ELEMENTS] __attribute__((aligned(64)));

static uint32_t ticks_to_us32(XTime ticks) {
    const uint64_t us = ((uint64_t)ticks * 1000000ULL) / (uint64_t)COUNTS_PER_SECOND;
    return us > 0xFFFFFFFFULL ? 0xFFFFFFFFU : (uint32_t)us;
}

static int magic_matches(const uint8_t magic[8], const char expected[8]) {
    return memcmp(magic, expected, 8) == 0;
}

static int init_rmsnorm_ip(void) {
    const int status = XRmsnorm_layer0_prefill_Initialize(&rms_ip, RMSNORM_DEVICE_ID);
    if (status != XST_SUCCESS) {
        xil_printf("ERROR: RMSNorm IP init failed: %d\r\n", status);
        return -1;
    }
    rms_ip_ready = 1;
    return 0;
}

static err_t send_pending(struct tcp_pcb *tpcb, rms_tcp_session_t *session) {
    while (session->tx_offset < session->tx_len) {
        uint32_t remaining = session->tx_len - session->tx_offset;
        u16_t chunk = tcp_sndbuf(tpcb);
        err_t err;

        if (chunk == 0U) {
            break;
        }
        if ((uint32_t)chunk > remaining) {
            chunk = (u16_t)remaining;
        }
        if (chunk > 4096U) {
            chunk = 4096U;
        }

        err = tcp_write(tpcb, &session->tx_buffer[session->tx_offset], chunk, TCP_WRITE_FLAG_COPY);
        if (err == ERR_MEM) {
            break;
        }
        if (err != ERR_OK) {
            xil_printf("ERROR: tcp_write failed: %d\r\n", err);
            return err;
        }
        session->tx_offset += chunk;
    }

    (void)tcp_output(tpcb);
    return ERR_OK;
}

static void prepare_response(
    rms_tcp_session_t *session,
    uint64_t request_id,
    uint32_t status,
    const uint8_t *payload,
    uint32_t payload_len,
    uint32_t hw_time_us,
    uint32_t total_time_us
) {
    rms_raw_response_header_t header;

    memcpy(header.magic, RMS_RESPONSE_MAGIC, 8);
    header.request_id = request_id;
    header.status = status;
    header.output_bytes = payload_len;
    header.hw_time_us = hw_time_us;
    header.total_time_us = total_time_us;

    memcpy(session->tx_buffer, &header, sizeof(header));
    if (payload_len > 0U && payload != NULL) {
        memcpy(&session->tx_buffer[sizeof(header)], payload, payload_len);
    }
    session->tx_len = sizeof(header) + payload_len;
    session->tx_offset = 0U;
}

static err_t prepare_error_and_send(
    struct tcp_pcb *tpcb,
    rms_tcp_session_t *session,
    uint64_t request_id,
    const char *message,
    XTime total_start
) {
    XTime total_end;
    XTime_GetTime(&total_end);
    prepare_response(
        session,
        request_id,
        RMS_STATUS_ERROR,
        (const uint8_t *)message,
        (uint32_t)strlen(message),
        0U,
        ticks_to_us32(total_end - total_start)
    );
    return send_pending(tpcb, session);
}

static int run_rmsnorm_ip(
    uint32_t row_count,
    uint32_t eps_bits,
    const uint8_t *input_payload,
    const uint8_t *weight_payload,
    uint32_t *hw_time_us,
    uint32_t *total_time_us
) {
    XTime total_start;
    XTime total_end;
    XTime hw_start;
    XTime hw_end;
    uint32_t polls = 0U;
    const uint32_t active_input_bytes = row_count * RMS_HIDDEN_SIZE * RMS_ELEMENT_BYTES;

    if (!rms_ip_ready) {
        return -1;
    }

    XTime_GetTime(&total_start);
    memset(input_buf, 0, RMS_INPUT_BYTES);
    memset(output_buf, 0, RMS_OUTPUT_BYTES);
    memcpy(input_buf, input_payload, active_input_bytes);
    memcpy(weight_buf, weight_payload, RMS_WEIGHT_BYTES);

    Xil_DCacheFlushRange((UINTPTR)input_buf, RMS_INPUT_BYTES);
    Xil_DCacheFlushRange((UINTPTR)weight_buf, RMS_WEIGHT_BYTES);
    Xil_DCacheFlushRange((UINTPTR)output_buf, RMS_OUTPUT_BYTES);

    XRmsnorm_layer0_prefill_Set_input_r(&rms_ip, (uint64_t)(UINTPTR)input_buf);
    XRmsnorm_layer0_prefill_Set_weight(&rms_ip, (uint64_t)(UINTPTR)weight_buf);
    XRmsnorm_layer0_prefill_Set_output_r(&rms_ip, (uint64_t)(UINTPTR)output_buf);
    XRmsnorm_layer0_prefill_Set_eps(&rms_ip, eps_bits);

    XTime_GetTime(&hw_start);
    XRmsnorm_layer0_prefill_Start(&rms_ip);
    while (!XRmsnorm_layer0_prefill_IsDone(&rms_ip)) {
        ++polls;
        if (polls > RMS_IP_TIMEOUT_POLLS) {
            return -2;
        }
    }
    XTime_GetTime(&hw_end);

    Xil_DCacheInvalidateRange((UINTPTR)output_buf, RMS_OUTPUT_BYTES);
    XTime_GetTime(&total_end);

    *hw_time_us = ticks_to_us32(hw_end - hw_start);
    *total_time_us = ticks_to_us32(total_end - total_start);
    return 0;
}

static err_t process_request(struct tcp_pcb *tpcb, rms_tcp_session_t *session) {
    rms_raw_request_header_t request;
    XTime total_start;
    const uint8_t *input_payload;
    const uint8_t *weight_payload;
    uint32_t output_bytes;
    uint32_t hw_time_us = 0U;
    uint32_t total_time_us = 0U;
    int status;

    XTime_GetTime(&total_start);
    memcpy(&request, session->rx_buffer, sizeof(request));

    if (!magic_matches(request.magic, RMS_REQUEST_MAGIC)) {
        return prepare_error_and_send(tpcb, session, request.request_id, "bad request magic", total_start);
    }
    if (request.row_count == 0U || request.row_count > RMS_FIXED_ROWS) {
        return prepare_error_and_send(tpcb, session, request.request_id, "row_count outside supported range", total_start);
    }
    if (request.hidden_size != RMS_HIDDEN_SIZE) {
        return prepare_error_and_send(tpcb, session, request.request_id, "hidden_size mismatch", total_start);
    }
    if (request.input_bytes != request.row_count * RMS_HIDDEN_SIZE * RMS_ELEMENT_BYTES) {
        return prepare_error_and_send(tpcb, session, request.request_id, "input_bytes mismatch", total_start);
    }
    if (request.weight_bytes != RMS_WEIGHT_BYTES) {
        return prepare_error_and_send(tpcb, session, request.request_id, "weight_bytes mismatch", total_start);
    }

    input_payload = &session->rx_buffer[sizeof(request)];
    weight_payload = input_payload + request.input_bytes;
    status = run_rmsnorm_ip(
        request.row_count,
        request.eps_bits,
        input_payload,
        weight_payload,
        &hw_time_us,
        &total_time_us
    );
    if (status == -1) {
        return prepare_error_and_send(tpcb, session, request.request_id, "RMSNorm IP is not ready", total_start);
    }
    if (status == -2) {
        return prepare_error_and_send(tpcb, session, request.request_id, "RMSNorm IP timeout", total_start);
    }
    if (status != 0) {
        return prepare_error_and_send(tpcb, session, request.request_id, "RMSNorm IP failed", total_start);
    }

    output_bytes = request.row_count * RMS_HIDDEN_SIZE * RMS_ELEMENT_BYTES;
    prepare_response(
        session,
        request.request_id,
        RMS_STATUS_OK,
        (const uint8_t *)output_buf,
        output_bytes,
        hw_time_us,
        total_time_us
    );
    xil_printf("raw rmsnorm rows=%lu hw_us=%lu total_us=%lu\r\n",
               (unsigned long)request.row_count,
               (unsigned long)hw_time_us,
               (unsigned long)total_time_us);
    return send_pending(tpcb, session);
}

static void update_expected_len(rms_tcp_session_t *session) {
    rms_raw_request_header_t request;
    uint32_t expected;

    if (session->expected_len != 0U || session->rx_len < sizeof(request)) {
        return;
    }

    memcpy(&request, session->rx_buffer, sizeof(request));
    expected = sizeof(request) + request.input_bytes + request.weight_bytes;
    if (expected > RMS_MAX_REQUEST_BYTES) {
        session->expected_len = sizeof(request);
        return;
    }
    session->expected_len = expected;
}

static err_t sent_callback(void *arg, struct tcp_pcb *tpcb, u16_t len) {
    rms_tcp_session_t *session = (rms_tcp_session_t *)arg;
    (void)len;
    return send_pending(tpcb, session);
}

err_t recv_callback(void *arg, struct tcp_pcb *tpcb, struct pbuf *p, err_t err) {
    rms_tcp_session_t *session = (rms_tcp_session_t *)arg;
    struct pbuf *q;

    if (p == NULL) {
        tcp_recv(tpcb, NULL);
        tcp_sent(tpcb, NULL);
        tcp_close(tpcb);
        return ERR_OK;
    }
    if (err != ERR_OK) {
        pbuf_free(p);
        return err;
    }

    tcp_recved(tpcb, p->tot_len);
    for (q = p; q != NULL; q = q->next) {
        if (session->rx_len + q->len > RMS_MAX_REQUEST_BYTES) {
            pbuf_free(p);
            return prepare_error_and_send(tpcb, session, 0ULL, "request too large", 0);
        }
        memcpy(&session->rx_buffer[session->rx_len], q->payload, q->len);
        session->rx_len += q->len;
    }
    pbuf_free(p);

    update_expected_len(session);
    if (session->expected_len != 0U && session->rx_len >= session->expected_len) {
        return process_request(tpcb, session);
    }

    return ERR_OK;
}

err_t accept_callback(void *arg, struct tcp_pcb *newpcb, err_t err) {
    (void)arg;
    if (err != ERR_OK || newpcb == NULL) {
        return ERR_VAL;
    }

    memset(&tcp_session, 0, sizeof(tcp_session));
    tcp_arg(newpcb, &tcp_session);
    tcp_recv(newpcb, recv_callback);
    tcp_sent(newpcb, sent_callback);

    return ERR_OK;
}

int transfer_data(void) {
    return 0;
}

void print_app_header(void) {
    xil_printf("\r\n----- RMSNorm raw TCP server -----\r\n");
    xil_printf("TCP port: %lu\r\n", (unsigned long)RMS_RAW_PORT);
    xil_printf("Fixed IP shape: rows<=%lu, hidden=%lu, bf16\r\n",
               (unsigned long)RMS_FIXED_ROWS,
               (unsigned long)RMS_HIDDEN_SIZE);
}

int start_application(void) {
    struct tcp_pcb *pcb;
    err_t err;

    if (init_rmsnorm_ip() != 0) {
        return -1;
    }

    pcb = tcp_new_ip_type(IPADDR_TYPE_ANY);
    if (pcb == NULL) {
        xil_printf("ERROR: tcp_new failed\r\n");
        return -2;
    }

    err = tcp_bind(pcb, IP_ANY_TYPE, RMS_RAW_PORT);
    if (err != ERR_OK) {
        xil_printf("ERROR: unable to bind port %lu: %d\r\n", (unsigned long)RMS_RAW_PORT, err);
        return -3;
    }

    pcb = tcp_listen(pcb);
    if (pcb == NULL) {
        xil_printf("ERROR: tcp_listen failed\r\n");
        return -4;
    }

    tcp_accept(pcb, accept_callback);
    xil_printf("RMSNorm raw TCP server started @ port %lu\r\n", (unsigned long)RMS_RAW_PORT);
    return 0;
}
