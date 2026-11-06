#ifndef M14_LOADER_CORE_H
#define M14_LOADER_CORE_H
#include <stddef.h>
#include <stdint.h>
#define M14_WEIGHT_BYTES 272269312u
#define M14_CHUNK_BYTES 1048576u
#define M14_WIRE_MAGIC 0x5734314du /* little-endian M14W */
#define M14_WIRE_VERSION 1u
enum { M14_BEGIN=1, M14_DATA=2, M14_COMMIT=3, M14_STATUS=4 };
enum { M14_OK=0, M14_BAD_HEADER=1, M14_BAD_ORDER=2, M14_BAD_CRC=3,
       M14_NOT_READY=4, M14_DDR_ERROR=5 };
typedef struct { uint32_t magic, version, op, seq, offset, size, total, crc; } m14_header;
typedef struct { uint32_t next, expected_crc, seq; int active, ready; } m14_loader;
uint32_t m14_crc_update(uint32_t state, const void *data, size_t bytes);
uint32_t m14_crc(const void *data, size_t bytes);
void m14_decode(m14_header *h, const uint8_t wire[32]);
void m14_encode(uint8_t wire[32], const m14_header *h);
int m14_validate(const m14_loader *s, const m14_header *h);
void m14_reply(m14_header *reply, const m14_loader *s, const m14_header *request,
               uint32_t status, uint32_t crc);
#endif
