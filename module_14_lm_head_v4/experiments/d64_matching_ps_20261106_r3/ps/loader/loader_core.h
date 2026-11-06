#ifndef M4A_LOADER_CORE_H
#define M4A_LOADER_CORE_H
#include <stddef.h>
#include <stdint.h>
#define M4A_IMAGE_BYTES 603979776u
#define M4A_CHUNK_BYTES 1048576u
#define M4A_WIRE_MAGIC 0x41343644u /* little-endian D64A; private arena protocol */
#define M4A_WIRE_VERSION 1u
enum { M4A_BEGIN=1, M4A_DATA=2, M4A_COMMIT=3, M4A_STATUS=4, M4A_READ=5, D64_ATTACH_READ_ONLY=6 };
#define M4A_READ_MAX 512u
#define M4A_TARGET_BASE UINT64_C(0x400000000)
enum { M4A_OK=0, M4A_BAD_HEADER=1, M4A_BAD_ORDER=2, M4A_BAD_CRC=3,
       M4A_NOT_READY=4, M4A_DDR_ERROR=5 };
typedef struct { uint32_t magic, version, op, seq, offset, size, total, crc; } m4a_header;
typedef struct { uint32_t next, expected_crc, seq; int active, ready, read_only; } m4a_loader;
uint32_t m4a_crc_update(uint32_t state, const void *data, size_t bytes);
uint32_t m4a_crc(const void *data, size_t bytes);
/* Single-threaded loader: read actual non-cacheable target in aligned words,
 * then CRC a bounded PS scratch copy. Unaligned head/tail remain byte loads. */
uint32_t m4a_target_crc_update(uint32_t state, const volatile void *data, size_t bytes);
void m4a_target_copy(void *dest, const volatile void *source, size_t bytes);
int m4a_target_window(uint64_t offset, uint64_t bytes, uint64_t *address);
int m4a_reply_ack(unsigned *acked, unsigned total, unsigned bytes);
void m4a_decode(m4a_header *h, const uint8_t wire[32]);
void m4a_encode(uint8_t wire[32], const m4a_header *h);
int m4a_validate(const m4a_loader *s, const m4a_header *h);
void m4a_reply(m4a_header *reply, const m4a_loader *s, const m4a_header *request,
               uint32_t status, uint32_t crc);
#endif
