/*
 * Module 16 LM Head raw TCP server for AXU9EGB.
 *
 * 2026-07-24 zb:
 * - Implements the existing LMH1 little-endian protocol.
 * - Streams large weight chunks directly into the reserved PS-DDR weight area.
 * - Preserves a completed weight across TCP reconnects.
 * - Uses the generated lm_head_argmax HLS driver for RUN_TOKEN.
 * - 2026-07-24 zb: accepts bounded runtime dimensions for controlled 4x4
 *   board tests while retaining the Qwen2.5 maximum DDR limits.
 *
 * The receive path deliberately does not require a complete TCP frame or pbuf.
 * Header, payload prefix, and payload data may all be split arbitrarily.
 */

#include <stdint.h>
#include <string.h>

#include "lwip/err.h"
#include "lwip/tcp.h"
#include "xil_cache.h"
#include "xil_printf.h"
#include "xparameters.h"
#include "xlm_head_argmax.h"
#include "xtime_l.h"

#include "lmh_buffers.h"

#if defined(XPAR_XLM_HEAD_ARGMAX_0_DEVICE_ID)
#define LMH_DEVICE_ID XPAR_XLM_HEAD_ARGMAX_0_DEVICE_ID
#elif defined(XPAR_LM_HEAD_ARGMAX_0_DEVICE_ID)
#define LMH_DEVICE_ID XPAR_LM_HEAD_ARGMAX_0_DEVICE_ID
#else
#error "Cannot find lm_head_argmax HLS IP device ID in xparameters.h"
#endif

#define LMH_TCP_PORT                    19016U
#define LMH_PROTOCOL_VERSION            1U
#define LMH_HEADER_BYTES                24U
#define LMH_LOAD_PREFIX_BYTES           24U
#define LMH_RUN_PREFIX_BYTES            16U
#define LMH_RESULT_PREFIX_BYTES         16U
#define LMH_PING_RESULT_BYTES           16U
#define LMH_TX_INLINE_BYTES             192U
#define LMH_TCP_WRITE_CHUNK_BYTES       4096U
#define LMH_MAX_WEIGHT_CHUNK_BYTES      (16U << 20)
#define LMH_IP_TIMEOUT_POLLS            1000000000U

#define LMH_OPCODE_LOAD_WEIGHT          1U
#define LMH_OPCODE_RUN_TOKEN            2U
#define LMH_OPCODE_PING                 3U
#define LMH_OPCODE_RESPONSE_BIT         0x8000U
#define LMH_OPCODE_ERROR                0xFFFFU

#define LMH_FLAG_ENABLE_PENALTY         (1U << 0)
#define LMH_FLAG_WANT_LOGITS            (1U << 1)
#define LMH_FLAG_FIRST_CHUNK            (1U << 2)
#define LMH_FLAG_LAST_CHUNK             (1U << 3)

#define LMH_STATUS_OK                   0U
#define LMH_STATUS_NOT_READY            1U

typedef struct {
    uint8_t header[LMH_HEADER_BYTES];
    uint32_t header_len;

    uint16_t opcode;
    uint32_t request_id;
    uint32_t flags;
    uint32_t payload_bytes;
    uint32_t expected_crc;
    uint32_t payload_received;
    uint32_t crc_state;

    uint8_t load_prefix[LMH_LOAD_PREFIX_BYTES];
    uint32_t load_prefix_len;
    uint64_t load_total_bytes;
    uint64_t load_offset;
    uint32_t load_data_bytes;
    uint8_t load_valid;
    uint8_t load_matches_upload;
    const char *frame_error;

    uint8_t tx_header[LMH_HEADER_BYTES];
    uint8_t tx_inline[LMH_TX_INLINE_BYTES];
    const uint8_t *tx_extra;
    uint32_t tx_inline_len;
    uint32_t tx_extra_len;
    uint32_t tx_total_len;
    uint32_t tx_offset;
    uint32_t tx_acked;
    uint8_t tx_active;
    uint8_t close_after_tx;
} lmh_tcp_session_t;

typedef struct {
    uint8_t ready;
    uint8_t upload_active;
    uint64_t total_bytes;
    uint64_t next_offset;
    uint32_t hidden_size;
    uint32_t vocab_size;
} lmh_weight_state_t;

static XLm_head_argmax lmh_ip;
static uint8_t lmh_ip_ready;
static lmh_tcp_session_t tcp_session;
static lmh_weight_state_t weight_state;
static struct tcp_pcb *active_pcb;
static uint32_t crc32_table[256];

/*
 * 2026-07-24 zb: low-address diagnostic buffers for the controlled 4x4 board
 * test.  They isolate HP0/DDR address reachability from the HLS arithmetic.
 * Full-model requests continue to use the reserved LMH_* DDR regions.
 */
static uint16_t small_hidden[4] __attribute__((aligned(64)));
static uint16_t small_weight[16] __attribute__((aligned(64)));
static uint32_t small_history[1] __attribute__((aligned(64)));
static uint16_t small_logits[4] __attribute__((aligned(64)));

static uint16_t get_le16(const uint8_t *data)
{
    return (uint16_t)data[0] | ((uint16_t)data[1] << 8);
}

static uint32_t get_le32(const uint8_t *data)
{
    return (uint32_t)data[0]
        | ((uint32_t)data[1] << 8)
        | ((uint32_t)data[2] << 16)
        | ((uint32_t)data[3] << 24);
}

static uint64_t get_le64(const uint8_t *data)
{
    return (uint64_t)get_le32(data)
        | ((uint64_t)get_le32(data + 4U) << 32);
}

static void put_le16(uint8_t *data, uint16_t value)
{
    data[0] = (uint8_t)value;
    data[1] = (uint8_t)(value >> 8);
}

static void put_le32(uint8_t *data, uint32_t value)
{
    data[0] = (uint8_t)value;
    data[1] = (uint8_t)(value >> 8);
    data[2] = (uint8_t)(value >> 16);
    data[3] = (uint8_t)(value >> 24);
}

static void put_le64(uint8_t *data, uint64_t value)
{
    put_le32(data, (uint32_t)value);
    put_le32(data + 4U, (uint32_t)(value >> 32));
}

static void init_crc32_table(void)
{
    uint32_t index;
    for (index = 0U; index < 256U; ++index) {
        uint32_t value = index;
        uint32_t bit;
        for (bit = 0U; bit < 8U; ++bit) {
            value = (value >> 1) ^
                (0xEDB88320U & (0U - (value & 1U)));
        }
        crc32_table[index] = value;
    }
}

/*
 * IEEE CRC32 compatible with Python zlib.crc32().
 * The state remains un-finalized while bytes arrive incrementally. A table is
 * generated once at boot so a 260 MiB upload does not pay eight bit-steps per
 * byte.
 */
static uint32_t crc32_update(uint32_t state, const uint8_t *data, uint32_t length)
{
    uint32_t index;
    for (index = 0U; index < length; ++index) {
        state = crc32_table[(state ^ data[index]) & 0xFFU] ^ (state >> 8);
    }
    return state;
}

static uint32_t crc32_segments(
    const uint8_t *first,
    uint32_t first_len,
    const uint8_t *second,
    uint32_t second_len)
{
    uint32_t state = 0xFFFFFFFFU;
    state = crc32_update(state, first, first_len);
    if (second_len != 0U) {
        state = crc32_update(state, second, second_len);
    }
    return state ^ 0xFFFFFFFFU;
}

static uint32_t ticks_to_us32(XTime ticks)
{
    const uint64_t us =
        ((uint64_t)ticks * 1000000ULL) / (uint64_t)COUNTS_PER_SECOND;
    return us > 0xFFFFFFFFULL ? 0xFFFFFFFFU : (uint32_t)us;
}

static void reset_frame(lmh_tcp_session_t *session)
{
    session->header_len = 0U;
    session->opcode = 0U;
    session->request_id = 0U;
    session->flags = 0U;
    session->payload_bytes = 0U;
    session->expected_crc = 0U;
    session->payload_received = 0U;
    session->crc_state = 0xFFFFFFFFU;
    session->load_prefix_len = 0U;
    session->load_total_bytes = 0U;
    session->load_offset = 0U;
    session->load_data_bytes = 0U;
    session->load_valid = 0U;
    session->load_matches_upload = 0U;
    session->frame_error = NULL;
}

static void reset_session(lmh_tcp_session_t *session)
{
    memset(session, 0, sizeof(*session));
    reset_frame(session);
}

static const uint8_t *tx_pointer(
    const lmh_tcp_session_t *session,
    uint32_t offset,
    uint32_t *available)
{
    if (offset < LMH_HEADER_BYTES) {
        *available = LMH_HEADER_BYTES - offset;
        return &session->tx_header[offset];
    }
    offset -= LMH_HEADER_BYTES;
    if (offset < session->tx_inline_len) {
        *available = session->tx_inline_len - offset;
        return &session->tx_inline[offset];
    }
    offset -= session->tx_inline_len;
    *available = session->tx_extra_len - offset;
    return &session->tx_extra[offset];
}

static err_t close_connection(struct tcp_pcb *tpcb)
{
    err_t err;
    tcp_arg(tpcb, NULL);
    tcp_recv(tpcb, NULL);
    tcp_sent(tpcb, NULL);
    tcp_poll(tpcb, NULL, 0U);
    tcp_err(tpcb, NULL);
    err = tcp_close(tpcb);
    if (err != ERR_OK) {
        tcp_abort(tpcb);
        err = ERR_ABRT;
    }
    if (active_pcb == tpcb) {
        active_pcb = NULL;
    }
    return err;
}

static err_t send_pending(struct tcp_pcb *tpcb, lmh_tcp_session_t *session)
{
    while (session->tx_active != 0U &&
           session->tx_offset < session->tx_total_len) {
        uint32_t segment_available;
        uint32_t remaining = session->tx_total_len - session->tx_offset;
        const uint8_t *source =
            tx_pointer(session, session->tx_offset, &segment_available);
        u16_t chunk = tcp_sndbuf(tpcb);
        err_t err;

        if (chunk == 0U) {
            break;
        }
        if ((uint32_t)chunk > remaining) {
            chunk = (u16_t)remaining;
        }
        if ((uint32_t)chunk > segment_available) {
            chunk = (u16_t)segment_available;
        }
        if (chunk > LMH_TCP_WRITE_CHUNK_BYTES) {
            chunk = LMH_TCP_WRITE_CHUNK_BYTES;
        }

        err = tcp_write(tpcb, source, chunk, TCP_WRITE_FLAG_COPY);
        if (err == ERR_MEM) {
            break;
        }
        if (err != ERR_OK) {
            xil_printf("LMH1 tcp_write failed: %d\r\n", err);
            return err;
        }
        session->tx_offset += chunk;
    }

    (void)tcp_output(tpcb);
    if (session->tx_active != 0U &&
        session->tx_offset == session->tx_total_len) {
        session->tx_active = 0U;
    }
    return ERR_OK;
}

static err_t prepare_response(
    struct tcp_pcb *tpcb,
    lmh_tcp_session_t *session,
    uint16_t opcode,
    uint32_t request_id,
    uint32_t flags,
    const uint8_t *inline_payload,
    uint32_t inline_len,
    const uint8_t *extra_payload,
    uint32_t extra_len,
    uint8_t close_after_tx)
{
    uint32_t payload_len;
    uint32_t payload_crc;

    if (inline_len > LMH_TX_INLINE_BYTES ||
        (extra_len != 0U && extra_payload == NULL) ||
        session->tx_active != 0U) {
        return ERR_VAL;
    }

    payload_len = inline_len + extra_len;
    if (inline_len != 0U) {
        memcpy(session->tx_inline, inline_payload, inline_len);
    }
    session->tx_inline_len = inline_len;
    session->tx_extra = extra_payload;
    session->tx_extra_len = extra_len;

    payload_crc = crc32_segments(
        session->tx_inline,
        inline_len,
        extra_payload,
        extra_len);
    memcpy(session->tx_header, "LMH1", 4U);
    put_le16(&session->tx_header[4], LMH_PROTOCOL_VERSION);
    put_le16(&session->tx_header[6], opcode);
    put_le32(&session->tx_header[8], request_id);
    put_le32(&session->tx_header[12], flags);
    put_le32(&session->tx_header[16], payload_len);
    put_le32(&session->tx_header[20], payload_crc);

    session->tx_total_len = LMH_HEADER_BYTES + payload_len;
    session->tx_offset = 0U;
    session->tx_acked = 0U;
    session->tx_active = 1U;
    session->close_after_tx = close_after_tx;
    return send_pending(tpcb, session);
}

static err_t send_error(
    struct tcp_pcb *tpcb,
    lmh_tcp_session_t *session,
    uint32_t request_id,
    const char *message,
    uint8_t close_after_tx)
{
    uint32_t length = (uint32_t)strlen(message);
    if (length > LMH_TX_INLINE_BYTES) {
        length = LMH_TX_INLINE_BYTES;
    }
    xil_printf("LMH1 request %lu error: %s\r\n",
               (unsigned long)request_id, message);
    return prepare_response(
        tpcb,
        session,
        LMH_OPCODE_ERROR,
        request_id,
        0U,
        (const uint8_t *)message,
        length,
        NULL,
        0U,
        close_after_tx);
}

static void make_result(
    uint8_t result[LMH_RESULT_PREFIX_BYTES],
    uint32_t status,
    uint32_t selected_token,
    uint32_t selected_score_bits,
    uint32_t logits_bytes)
{
    put_le32(&result[0], status);
    put_le32(&result[4], selected_token);
    put_le32(&result[8], selected_score_bits);
    put_le32(&result[12], logits_bytes);
}

static err_t handle_ping(
    struct tcp_pcb *tpcb,
    lmh_tcp_session_t *session)
{
    uint8_t payload[LMH_PING_RESULT_BYTES];
    const uint64_t ready_bytes =
        weight_state.ready != 0U ? weight_state.total_bytes : 0ULL;

    put_le32(&payload[0],
             weight_state.ready != 0U ? weight_state.hidden_size : 0U);
    put_le32(&payload[4],
             weight_state.ready != 0U ? weight_state.vocab_size : 0U);
    put_le64(&payload[8], ready_bytes);
    return prepare_response(
        tpcb,
        session,
        (uint16_t)(LMH_OPCODE_PING | LMH_OPCODE_RESPONSE_BIT),
        session->request_id,
        0U,
        payload,
        sizeof(payload),
        NULL,
        0U,
        0U);
}

static void invalidate_active_upload(void)
{
    if (weight_state.upload_active != 0U) {
        weight_state.upload_active = 0U;
        weight_state.ready = 0U;
        weight_state.next_offset = 0ULL;
    }
}

static void validate_load_prefix(lmh_tcp_session_t *session)
{
    const uint8_t first =
        (session->flags & LMH_FLAG_FIRST_CHUNK) != 0U;
    const uint8_t last =
        (session->flags & LMH_FLAG_LAST_CHUNK) != 0U;
    const uint32_t hidden_size = get_le32(&session->load_prefix[8]);
    const uint32_t vocab_size = get_le32(&session->load_prefix[12]);
    const uint64_t expected_total_bytes =
        (uint64_t)hidden_size * (uint64_t)vocab_size * 2ULL;

    session->load_total_bytes = get_le64(&session->load_prefix[0]);
    session->load_offset = get_le64(&session->load_prefix[16]);
    session->load_data_bytes =
        session->payload_bytes - LMH_LOAD_PREFIX_BYTES;

    if (hidden_size == 0U || hidden_size > LMH_HIDDEN_SIZE ||
        vocab_size == 0U || vocab_size > LMH_VOCAB_SIZE) {
        session->frame_error = "LOAD_WEIGHT dimensions exceed limits";
        return;
    }
    if (session->load_total_bytes != expected_total_bytes ||
        session->load_total_bytes > (uint64_t)LMH_WEIGHT_BYTES) {
        session->frame_error = "LOAD_WEIGHT total_bytes mismatch";
        return;
    }
    if ((session->load_data_bytes & 1U) != 0U ||
        session->load_data_bytes > LMH_MAX_WEIGHT_CHUNK_BYTES) {
        session->frame_error = "LOAD_WEIGHT chunk size is invalid";
        return;
    }
    if (session->load_offset + (uint64_t)session->load_data_bytes >
        session->load_total_bytes) {
        session->frame_error = "LOAD_WEIGHT chunk exceeds tensor";
        return;
    }
    if (first != 0U) {
        if (session->load_offset != 0ULL) {
            session->frame_error = "FIRST_CHUNK offset must be zero";
            return;
        }
        weight_state.ready = 0U;
        weight_state.upload_active = 1U;
        weight_state.total_bytes = session->load_total_bytes;
        weight_state.next_offset = 0ULL;
        weight_state.hidden_size = hidden_size;
        weight_state.vocab_size = vocab_size;
    } else if (session->load_offset == 0ULL) {
        session->frame_error = "offset zero requires FIRST_CHUNK";
        return;
    }

    if (weight_state.upload_active == 0U) {
        session->frame_error = "LOAD_WEIGHT arrived before FIRST_CHUNK";
        return;
    }
    session->load_matches_upload = 1U;
    if (weight_state.total_bytes != session->load_total_bytes ||
        weight_state.hidden_size != hidden_size ||
        weight_state.vocab_size != vocab_size ||
        weight_state.next_offset != session->load_offset) {
        session->frame_error = "LOAD_WEIGHT offset or upload metadata mismatch";
        return;
    }
    if (last != 0U &&
        session->load_offset + (uint64_t)session->load_data_bytes !=
            session->load_total_bytes) {
        session->frame_error = "LAST_CHUNK does not end at total_bytes";
        return;
    }
    if (last == 0U &&
        session->load_offset + (uint64_t)session->load_data_bytes ==
            session->load_total_bytes) {
        session->frame_error = "final weight bytes require LAST_CHUNK";
        return;
    }
    session->load_valid = 1U;
}

static err_t finish_load(
    struct tcp_pcb *tpcb,
    lmh_tcp_session_t *session)
{
    uint8_t result[LMH_RESULT_PREFIX_BYTES];
    const uint8_t last =
        (session->flags & LMH_FLAG_LAST_CHUNK) != 0U;

    if (session->frame_error != NULL || session->load_valid == 0U) {
        if (session->load_matches_upload != 0U) {
            invalidate_active_upload();
        }
        return send_error(
            tpcb,
            session,
            session->request_id,
            session->frame_error != NULL
                ? session->frame_error
                : "LOAD_WEIGHT prefix is incomplete",
            0U);
    }

    Xil_DCacheFlushRange(
        LMH_WEIGHT_ADDR + (UINTPTR)session->load_offset,
        session->load_data_bytes);
    weight_state.next_offset =
        session->load_offset + (uint64_t)session->load_data_bytes;
    if (last != 0U) {
        weight_state.upload_active = 0U;
        weight_state.ready = 1U;
        xil_printf("LMH1 weight READY: %lu bytes\r\n",
                   (unsigned long)weight_state.total_bytes);
    }

    make_result(result, LMH_STATUS_OK, 0U, 0U, 0U);
    return prepare_response(
        tpcb,
        session,
        (uint16_t)(LMH_OPCODE_LOAD_WEIGHT | LMH_OPCODE_RESPONSE_BIT),
        session->request_id,
        0U,
        result,
        sizeof(result),
        NULL,
        0U,
        0U);
}

static uint8_t positive_finite_float_bits(uint32_t bits)
{
    const uint32_t exponent = bits & 0x7F800000U;
    const uint32_t magnitude = bits & 0x7FFFFFFFU;
    return (bits & 0x80000000U) == 0U &&
           magnitude != 0U &&
           exponent != 0x7F800000U;
}

static err_t run_lm_head_ip(
    uint32_t penalty_bits,
    uint8_t enable_penalty,
    uint8_t write_logits,
    uint32_t hidden_size,
    uint32_t vocab_size,
    UINTPTR hidden_addr,
    UINTPTR weight_addr,
    UINTPTR history_addr,
    UINTPTR logits_addr,
    uint32_t *selected_token,
    uint32_t *selected_score_bits,
    uint32_t *hw_time_us)
{
    XTime start;
    XTime end;
    uint32_t polls = 0U;

    if (lmh_ip_ready == 0U) {
        return ERR_IF;
    }

    XLm_head_argmax_Set_hidden(&lmh_ip, (uint64_t)hidden_addr);
    XLm_head_argmax_Set_weight(&lmh_ip, (uint64_t)weight_addr);
    XLm_head_argmax_Set_history_bitmap(
        &lmh_ip, (uint64_t)history_addr);
    XLm_head_argmax_Set_raw_logits(&lmh_ip, (uint64_t)logits_addr);
    XLm_head_argmax_Set_hidden_size(&lmh_ip, hidden_size);
    XLm_head_argmax_Set_vocab_size(&lmh_ip, vocab_size);
    XLm_head_argmax_Set_write_logits(&lmh_ip, write_logits);
    XLm_head_argmax_Set_enable_repetition_penalty(
        &lmh_ip, enable_penalty);
    XLm_head_argmax_Set_repetition_penalty(&lmh_ip, penalty_bits);

    if (write_logits != 0U) {
        Xil_DCacheInvalidateRange(
            logits_addr, vocab_size * sizeof(uint16_t));
    }

    XTime_GetTime(&start);
    XLm_head_argmax_Start(&lmh_ip);
    while (XLm_head_argmax_IsDone(&lmh_ip) == 0U) {
        ++polls;
        if (polls > LMH_IP_TIMEOUT_POLLS) {
            return ERR_TIMEOUT;
        }
    }
    XTime_GetTime(&end);

    if (XLm_head_argmax_Get_selected_token_vld(&lmh_ip) == 0U ||
        XLm_head_argmax_Get_selected_score_vld(&lmh_ip) == 0U) {
        return ERR_IF;
    }
    *selected_token = XLm_head_argmax_Get_selected_token(&lmh_ip);
    *selected_score_bits = XLm_head_argmax_Get_selected_score(&lmh_ip);
    *hw_time_us = ticks_to_us32(end - start);

    if (write_logits != 0U) {
        Xil_DCacheInvalidateRange(
            logits_addr, vocab_size * sizeof(uint16_t));
    }
    return ERR_OK;
}

static err_t handle_run(
    struct tcp_pcb *tpcb,
    lmh_tcp_session_t *session)
{
    const uint8_t *payload = (const uint8_t *)LMH_NETWORK_RX_ADDR;
    const uint32_t hidden_size = get_le32(&payload[0]);
    const uint32_t vocab_size = get_le32(&payload[4]);
    const uint32_t penalty_bits = get_le32(&payload[8]);
    const uint32_t history_words = get_le32(&payload[12]);
    const uint8_t enable_penalty =
        (session->flags & LMH_FLAG_ENABLE_PENALTY) != 0U;
    const uint8_t want_logits =
        (session->flags & LMH_FLAG_WANT_LOGITS) != 0U;
    const uint32_t expected_history_words = (vocab_size + 31U) / 32U;
    const uint32_t hidden_bytes = hidden_size * sizeof(uint16_t);
    const uint32_t logits_bytes = vocab_size * sizeof(uint16_t);
    const uint64_t expected =
        (uint64_t)LMH_RUN_PREFIX_BYTES +
        (uint64_t)hidden_size * 2ULL +
        (uint64_t)history_words * 4ULL;
    const uint8_t *hidden_payload = &payload[LMH_RUN_PREFIX_BYTES];
    const uint8_t *history_payload =
        hidden_payload + (uint64_t)hidden_size * 2ULL;
    uint8_t result[LMH_RESULT_PREFIX_BYTES];
    uint32_t selected_token = 0U;
    uint32_t selected_score_bits = 0U;
    uint32_t hw_time_us = 0U;
    UINTPTR run_hidden_addr = LMH_HIDDEN_ADDR;
    UINTPTR run_weight_addr = LMH_WEIGHT_ADDR;
    UINTPTR run_history_addr = LMH_HISTORY_ADDR;
    UINTPTR run_logits_addr = LMH_LOGITS_ADDR;
    err_t status;

    if (weight_state.ready == 0U) {
        make_result(result, LMH_STATUS_NOT_READY, 0U, 0U, 0U);
        return prepare_response(
            tpcb,
            session,
            (uint16_t)(LMH_OPCODE_RUN_TOKEN | LMH_OPCODE_RESPONSE_BIT),
            session->request_id,
            0U,
            result,
            sizeof(result),
            NULL,
            0U,
            0U);
    }
    if (hidden_size != weight_state.hidden_size ||
        vocab_size != weight_state.vocab_size) {
        return send_error(
            tpcb, session, session->request_id,
            "RUN_TOKEN dimensions do not match loaded weight", 0U);
    }
    if (enable_penalty != 0U &&
        history_words != expected_history_words) {
        return send_error(
            tpcb, session, session->request_id,
            "RUN_TOKEN history bitmap does not cover vocabulary", 0U);
    }
    if (enable_penalty == 0U &&
        history_words != 0U &&
        history_words != expected_history_words) {
        return send_error(
            tpcb, session, session->request_id,
            "RUN_TOKEN history_words must be zero or cover vocabulary", 0U);
    }
    if (expected != (uint64_t)session->payload_bytes) {
        return send_error(
            tpcb, session, session->request_id,
            "RUN_TOKEN payload length mismatch", 0U);
    }
    if (positive_finite_float_bits(penalty_bits) == 0U) {
        return send_error(
            tpcb, session, session->request_id,
            "RUN_TOKEN repetition_penalty must be positive and finite", 0U);
    }

    memcpy((void *)LMH_HIDDEN_ADDR, hidden_payload, hidden_bytes);
    Xil_DCacheFlushRange(LMH_HIDDEN_ADDR, hidden_bytes);
    if (history_words != 0U) {
        memcpy((void *)LMH_HISTORY_ADDR,
               history_payload,
               history_words * sizeof(uint32_t));
        Xil_DCacheFlushRange(
            LMH_HISTORY_ADDR, history_words * sizeof(uint32_t));
    }

    if (hidden_size <= 4U && vocab_size <= 4U) {
        memcpy(small_hidden, hidden_payload, hidden_bytes);
        memcpy(small_weight,
               (const void *)LMH_WEIGHT_ADDR,
               hidden_size * vocab_size * sizeof(uint16_t));
        if (history_words != 0U) {
            memcpy(small_history,
                   history_payload,
                   history_words * sizeof(uint32_t));
        } else {
            small_history[0] = 0U;
        }
        memset(small_logits, 0, sizeof(small_logits));
        Xil_DCacheFlushRange((UINTPTR)small_hidden, hidden_bytes);
        Xil_DCacheFlushRange(
            (UINTPTR)small_weight,
            hidden_size * vocab_size * sizeof(uint16_t));
        Xil_DCacheFlushRange(
            (UINTPTR)small_history, sizeof(small_history));
        Xil_DCacheFlushRange((UINTPTR)small_logits, logits_bytes);
        run_hidden_addr = (UINTPTR)small_hidden;
        run_weight_addr = (UINTPTR)small_weight;
        run_history_addr = (UINTPTR)small_history;
        run_logits_addr = (UINTPTR)small_logits;
    }

    status = run_lm_head_ip(
        penalty_bits,
        enable_penalty,
        want_logits,
        hidden_size,
        vocab_size,
        run_hidden_addr,
        run_weight_addr,
        run_history_addr,
        run_logits_addr,
        &selected_token,
        &selected_score_bits,
        &hw_time_us);
    if (status == ERR_TIMEOUT) {
        return send_error(
            tpcb, session, session->request_id,
            "lm_head_argmax IP timeout", 0U);
    }
    if (status != ERR_OK) {
        return send_error(
            tpcb, session, session->request_id,
            "lm_head_argmax IP failed or output is invalid", 0U);
    }

    make_result(
        result,
        LMH_STATUS_OK,
        selected_token,
        selected_score_bits,
        want_logits != 0U ? logits_bytes : 0U);
    xil_printf("LMH1 RUN_TOKEN id=%lu token=%lu hw_us=%lu logits=%lu\r\n",
               (unsigned long)session->request_id,
               (unsigned long)selected_token,
               (unsigned long)hw_time_us,
               (unsigned long)(want_logits != 0U ? logits_bytes : 0U));
    return prepare_response(
        tpcb,
        session,
        (uint16_t)(LMH_OPCODE_RUN_TOKEN | LMH_OPCODE_RESPONSE_BIT),
        session->request_id,
        0U,
        result,
        sizeof(result),
        want_logits != 0U
            ? (const uint8_t *)run_logits_addr
            : NULL,
        want_logits != 0U ? logits_bytes : 0U,
        0U);
}

static err_t finish_frame(
    struct tcp_pcb *tpcb,
    lmh_tcp_session_t *session)
{
    const uint32_t actual_crc = session->crc_state ^ 0xFFFFFFFFU;
    err_t err;

    if (actual_crc != session->expected_crc) {
        if (session->opcode == LMH_OPCODE_LOAD_WEIGHT &&
            session->load_matches_upload != 0U) {
            invalidate_active_upload();
        }
        err = send_error(
            tpcb, session, session->request_id,
            "payload CRC32 mismatch", 0U);
        reset_frame(session);
        return err;
    }

    if (session->opcode == LMH_OPCODE_PING) {
        err = handle_ping(tpcb, session);
    } else if (session->opcode == LMH_OPCODE_LOAD_WEIGHT) {
        err = finish_load(tpcb, session);
    } else {
        err = handle_run(tpcb, session);
    }
    reset_frame(session);
    return err;
}

static err_t consume_bytes(
    struct tcp_pcb *tpcb,
    lmh_tcp_session_t *session,
    const uint8_t *data,
    uint32_t length);

static err_t parse_header(
    struct tcp_pcb *tpcb,
    lmh_tcp_session_t *session)
{
    const uint16_t version = get_le16(&session->header[4]);

    session->opcode = get_le16(&session->header[6]);
    session->request_id = get_le32(&session->header[8]);
    session->flags = get_le32(&session->header[12]);
    session->payload_bytes = get_le32(&session->header[16]);
    session->expected_crc = get_le32(&session->header[20]);
    session->payload_received = 0U;
    session->crc_state = 0xFFFFFFFFU;

    if (memcmp(session->header, "LMH1", 4U) != 0) {
        return send_error(
            tpcb, session, session->request_id,
            "bad LMH1 magic", 1U);
    }
    if (version != LMH_PROTOCOL_VERSION) {
        return send_error(
            tpcb, session, session->request_id,
            "unsupported LMH1 protocol version", 1U);
    }
    if (session->opcode == LMH_OPCODE_PING) {
        if (session->flags != 0U || session->payload_bytes != 0U) {
            return send_error(
                tpcb, session, session->request_id,
                "PING requires empty payload and zero flags", 1U);
        }
    } else if (session->opcode == LMH_OPCODE_LOAD_WEIGHT) {
        if ((session->flags &
             ~(LMH_FLAG_FIRST_CHUNK | LMH_FLAG_LAST_CHUNK)) != 0U ||
            session->payload_bytes < LMH_LOAD_PREFIX_BYTES ||
            session->payload_bytes >
                LMH_LOAD_PREFIX_BYTES + LMH_MAX_WEIGHT_CHUNK_BYTES) {
            return send_error(
                tpcb, session, session->request_id,
                "invalid LOAD_WEIGHT header", 1U);
        }
    } else if (session->opcode == LMH_OPCODE_RUN_TOKEN) {
        if ((session->flags &
             ~(LMH_FLAG_ENABLE_PENALTY | LMH_FLAG_WANT_LOGITS)) != 0U ||
            session->payload_bytes < LMH_RUN_PREFIX_BYTES ||
            session->payload_bytes > LMH_NETWORK_RX_BYTES) {
            return send_error(
                tpcb, session, session->request_id,
                "invalid RUN_TOKEN header", 1U);
        }
    } else {
        return send_error(
            tpcb, session, session->request_id,
            "unknown LMH1 opcode", 1U);
    }

    if (session->payload_bytes == 0U) {
        return finish_frame(tpcb, session);
    }
    return ERR_OK;
}

static err_t consume_payload(
    struct tcp_pcb *tpcb,
    lmh_tcp_session_t *session,
    const uint8_t *data,
    uint32_t length)
{
    while (length != 0U) {
        uint32_t remaining =
            session->payload_bytes - session->payload_received;
        uint32_t take = length < remaining ? length : remaining;

        if (session->opcode == LMH_OPCODE_LOAD_WEIGHT) {
            uint32_t consumed = 0U;
            if (session->load_prefix_len < LMH_LOAD_PREFIX_BYTES) {
                uint32_t prefix_remaining =
                    LMH_LOAD_PREFIX_BYTES - session->load_prefix_len;
                uint32_t prefix_take =
                    take < prefix_remaining ? take : prefix_remaining;
                memcpy(
                    &session->load_prefix[session->load_prefix_len],
                    data,
                    prefix_take);
                session->load_prefix_len += prefix_take;
                consumed += prefix_take;
                if (session->load_prefix_len == LMH_LOAD_PREFIX_BYTES &&
                    session->load_valid == 0U &&
                    session->frame_error == NULL) {
                    validate_load_prefix(session);
                }
            }
            if (consumed < take && session->load_valid != 0U) {
                const uint64_t data_position =
                    (uint64_t)session->payload_received +
                    (uint64_t)consumed -
                    (uint64_t)LMH_LOAD_PREFIX_BYTES;
                memcpy(
                    (void *)(LMH_WEIGHT_ADDR +
                             (UINTPTR)session->load_offset +
                             (UINTPTR)data_position),
                    data + consumed,
                    take - consumed);
            }
        } else {
            memcpy(
                (void *)(LMH_NETWORK_RX_ADDR +
                         (UINTPTR)session->payload_received),
                data,
                take);
        }

        session->crc_state =
            crc32_update(session->crc_state, data, take);
        session->payload_received += take;
        data += take;
        length -= take;

        if (session->payload_received == session->payload_bytes) {
            err_t err = finish_frame(tpcb, session);
            if (err != ERR_OK) {
                return err;
            }
            if (length != 0U) {
                if (session->tx_active != 0U) {
                    return ERR_MEM;
                }
                return consume_bytes(tpcb, session, data, length);
            }
        }
    }
    return ERR_OK;
}

static err_t consume_bytes(
    struct tcp_pcb *tpcb,
    lmh_tcp_session_t *session,
    const uint8_t *data,
    uint32_t length)
{
    while (length != 0U) {
        if (session->header_len < LMH_HEADER_BYTES) {
            const uint32_t header_remaining =
                LMH_HEADER_BYTES - session->header_len;
            const uint32_t take =
                length < header_remaining ? length : header_remaining;
            memcpy(&session->header[session->header_len], data, take);
            session->header_len += take;
            data += take;
            length -= take;
            if (session->header_len == LMH_HEADER_BYTES) {
                err_t err = parse_header(tpcb, session);
                if (err != ERR_OK || active_pcb == NULL) {
                    return err;
                }
                if (session->header_len == 0U &&
                    session->tx_active != 0U &&
                    length != 0U) {
                    return ERR_MEM;
                }
            }
        } else {
            err_t err =
                consume_payload(tpcb, session, data, length);
            return err;
        }
    }
    return ERR_OK;
}

static err_t sent_callback(void *arg, struct tcp_pcb *tpcb, u16_t len)
{
    lmh_tcp_session_t *session = (lmh_tcp_session_t *)arg;
    err_t err;
    session->tx_acked += len;
    err = send_pending(tpcb, session);
    if (err != ERR_OK) {
        return err;
    }
    /*
     * 2026-07-24 zb: close malformed-header connections only after lwIP has
     * acknowledged every queued error-response byte. Closing immediately
     * after tcp_write can turn the intended response into a TCP reset.
     */
    if (session->close_after_tx != 0U &&
        session->tx_active == 0U &&
        session->tx_acked >= session->tx_total_len) {
        return close_connection(tpcb);
    }
    return ERR_OK;
}

static err_t poll_callback(void *arg, struct tcp_pcb *tpcb)
{
    lmh_tcp_session_t *session = (lmh_tcp_session_t *)arg;
    return send_pending(tpcb, session);
}

static void error_callback(void *arg, err_t err)
{
    (void)arg;
    (void)err;
    active_pcb = NULL;
    reset_session(&tcp_session);
    if (weight_state.upload_active != 0U) {
        invalidate_active_upload();
    }
}

static err_t recv_callback(
    void *arg,
    struct tcp_pcb *tpcb,
    struct pbuf *p,
    err_t err)
{
    lmh_tcp_session_t *session = (lmh_tcp_session_t *)arg;
    struct pbuf *q;
    err_t consume_status = ERR_OK;

    if (p == NULL) {
        if (weight_state.upload_active != 0U) {
            invalidate_active_upload();
        }
        reset_session(session);
        return close_connection(tpcb);
    }
    if (err != ERR_OK) {
        pbuf_free(p);
        return err;
    }

    for (q = p; q != NULL; q = q->next) {
        if (consume_status == ERR_OK) {
            consume_status = consume_bytes(
                tpcb,
                session,
                (const uint8_t *)q->payload,
                q->len);
        }
    }
    tcp_recved(tpcb, p->tot_len);
    pbuf_free(p);

    /*
     * ERR_MEM here means a client pipelined another frame before the prior
     * response was queued. The supplied CPU client is request/response
     * sequential, so this protects state without affecting normal traffic.
     */
    if (consume_status == ERR_MEM && active_pcb != NULL) {
        xil_printf("LMH1 client pipelined while TX was pending; closing\r\n");
        return close_connection(tpcb);
    }
    return consume_status;
}

static err_t accept_callback(
    void *arg,
    struct tcp_pcb *newpcb,
    err_t err)
{
    (void)arg;
    if (err != ERR_OK || newpcb == NULL) {
        return ERR_VAL;
    }
    if (active_pcb != NULL) {
        err_t close_status = tcp_close(newpcb);
        if (close_status != ERR_OK) {
            tcp_abort(newpcb);
            return ERR_ABRT;
        }
        return ERR_OK;
    }

    reset_session(&tcp_session);
    active_pcb = newpcb;
    tcp_arg(newpcb, &tcp_session);
    tcp_recv(newpcb, recv_callback);
    tcp_sent(newpcb, sent_callback);
    tcp_poll(newpcb, poll_callback, 2U);
    tcp_err(newpcb, error_callback);
    tcp_nagle_disable(newpcb);
    xil_printf("LMH1 client connected\r\n");
    return ERR_OK;
}

int transfer_data(void)
{
    if (active_pcb != NULL && tcp_session.tx_active != 0U) {
        (void)send_pending(active_pcb, &tcp_session);
    }
    return 0;
}

void print_app_header(void)
{
    xil_printf("\r\n----- Module 16 LM Head LMH1 TCP server -----\r\n");
    xil_printf("TCP port: %lu\r\n", (unsigned long)LMH_TCP_PORT);
    xil_printf("Shape: hidden=%lu vocab=%lu weight=%lu bytes\r\n",
               (unsigned long)LMH_HIDDEN_SIZE,
               (unsigned long)LMH_VOCAB_SIZE,
               (unsigned long)LMH_WEIGHT_BYTES);
}

int start_application(void)
{
    struct tcp_pcb *pcb;
    err_t err;
    int init_status;

    init_status = XLm_head_argmax_Initialize(&lmh_ip, LMH_DEVICE_ID);
    if (init_status != XST_SUCCESS) {
        xil_printf("ERROR: lm_head_argmax init failed: %d\r\n", init_status);
        return -1;
    }
    lmh_ip_ready = 1U;
    init_crc32_table();
    memset(&weight_state, 0, sizeof(weight_state));
    reset_session(&tcp_session);

    pcb = tcp_new_ip_type(IPADDR_TYPE_ANY);
    if (pcb == NULL) {
        xil_printf("ERROR: tcp_new failed\r\n");
        return -2;
    }
    err = tcp_bind(pcb, IP_ANY_TYPE, LMH_TCP_PORT);
    if (err != ERR_OK) {
        xil_printf("ERROR: unable to bind port %lu: %d\r\n",
                   (unsigned long)LMH_TCP_PORT, err);
        tcp_close(pcb);
        return -3;
    }
    pcb = tcp_listen(pcb);
    if (pcb == NULL) {
        xil_printf("ERROR: tcp_listen failed\r\n");
        return -4;
    }
    tcp_accept(pcb, accept_callback);
    xil_printf("LMH1 TCP server started @ port %lu\r\n",
               (unsigned long)LMH_TCP_PORT);
    return 0;
}
