#include "loader_core.h"
#include <string.h>
static uint32_t table[256];
static int initialized;
uint32_t m4a_crc_update(uint32_t state, const void *data, size_t bytes) {
    const uint8_t *p = (const uint8_t *)data;
    if (!initialized) {
        uint32_t i, j;
        for (i=0; i<256; ++i) {
            uint32_t v=i;
            for (j=0; j<8; ++j) v=(v>>1)^((v&1)?0xedb88320u:0);
            table[i]=v;
        }
        initialized=1;
    }
    while (bytes--) state=table[(state^*p++)&255]^(state>>8);
    return state;
}
uint32_t m4a_crc(const void *data, size_t bytes) {
    return m4a_crc_update(0xffffffffu, data, bytes)^0xffffffffu;
}
void m4a_target_copy(void *dest, const volatile void *data, size_t bytes) {
    uint8_t *out=(uint8_t *)dest;
    const volatile uint8_t *source=(const volatile uint8_t *)data;
    size_t i=0;
    while(i<bytes && (((uintptr_t)(source+i))&7u)) {out[i]=source[i];++i;}
    while(bytes-i>=sizeof(uint64_t)) {
        uint64_t word=*(const volatile uint64_t *)(source+i);
        memcpy(out+i,&word,sizeof(word));i+=sizeof(word);
    }
    while(i<bytes) {out[i]=source[i];++i;}
}
int m4a_target_window(uint64_t offset, uint64_t bytes, uint64_t *address) {
    if(!address || offset>M4A_IMAGE_BYTES || bytes>M4A_IMAGE_BYTES-offset)return 0;
    *address=M4A_TARGET_BASE+offset;
    return 1;
}
int m4a_reply_ack(unsigned *acked, unsigned total, unsigned bytes) {
    if(!acked || total<32 || total>32+M4A_READ_MAX || *acked>total || bytes>total-*acked)return 0;
    *acked+=bytes;return *acked==total;
}
uint32_t m4a_target_crc_update(uint32_t state, const volatile void *data, size_t bytes) {
    static uint64_t scratch_words[2048]; /* 16 KiB in PS software memory. */
    uint8_t *scratch=(uint8_t *)scratch_words;
    const volatile uint8_t *source=(const volatile uint8_t *)data;
    while(bytes) {
        size_t n=bytes>sizeof(scratch_words) ? sizeof(scratch_words):bytes;
        m4a_target_copy(scratch,source,n);
        state=m4a_crc_update(state,scratch,n);
        source+=n; bytes-=n;
    }
    return state;
}
void m4a_decode(m4a_header *h, const uint8_t wire[32]) {
    uint32_t v[8]; unsigned i;
    for(i=0;i<8;++i) v[i]=(uint32_t)wire[4*i]|((uint32_t)wire[4*i+1]<<8)|
        ((uint32_t)wire[4*i+2]<<16)|((uint32_t)wire[4*i+3]<<24);
    h->magic=v[0]; h->version=v[1]; h->op=v[2]; h->seq=v[3];
    h->offset=v[4]; h->size=v[5]; h->total=v[6]; h->crc=v[7];
}
void m4a_encode(uint8_t wire[32], const m4a_header *h) {
    uint32_t v[8]={h->magic,h->version,h->op,h->seq,h->offset,h->size,h->total,h->crc};
    unsigned i,j;
    for(i=0;i<8;++i) for(j=0;j<4;++j) wire[4*i+j]=(uint8_t)(v[i]>>(8*j));
}
int m4a_validate(const m4a_loader *s, const m4a_header *h) {
    if(h->magic!=M4A_WIRE_MAGIC || h->version!=M4A_WIRE_VERSION || h->total!=M4A_IMAGE_BYTES)
        return M4A_BAD_HEADER;
    if(h->op==D64_ATTACH_READ_ONLY) return h->size==0 && h->offset==0 && h->seq==0 && h->crc==0 && !s->active ? M4A_OK:M4A_BAD_HEADER;
    if(h->op==M4A_BEGIN) return h->size==0 && h->offset==0 && h->seq==0 ? M4A_OK:M4A_BAD_HEADER;
    if(h->op==M4A_STATUS) return h->size==0 && h->offset==0 ? M4A_OK:M4A_BAD_HEADER;
    /* READ has no request payload. crc carries the requested byte count;
     * response crc covers the actual returned target bytes. */
    if(h->op==M4A_READ) {
        if((!s->ready && !s->read_only) || s->active)return M4A_NOT_READY;
        return h->size==0 && h->crc>0 && h->crc<=M4A_READ_MAX &&
            h->offset<=M4A_IMAGE_BYTES && h->crc<=M4A_IMAGE_BYTES-h->offset ? M4A_OK:M4A_BAD_HEADER;
    }
    if(!s->active) return M4A_NOT_READY;
    if(h->seq!=s->seq || h->offset!=s->next) return M4A_BAD_ORDER;
    if(h->op==M4A_DATA) return h->size>0 && h->size<=M4A_CHUNK_BYTES &&
        h->offset<=M4A_IMAGE_BYTES && h->size<=M4A_IMAGE_BYTES-h->offset ? M4A_OK:M4A_BAD_HEADER;
    if(h->op==M4A_COMMIT) return h->size==0 && s->next==M4A_IMAGE_BYTES &&
        h->crc==s->expected_crc ? M4A_OK:M4A_BAD_ORDER;
    return M4A_BAD_HEADER;
}
void m4a_reply(m4a_header *r, const m4a_loader *s, const m4a_header *h,
               uint32_t status, uint32_t crc) {
    r->magic=M4A_WIRE_MAGIC; r->version=M4A_WIRE_VERSION; r->op=h->op|0x80000000u;
    r->seq=h->seq; r->offset=h->op==M4A_READ ? h->offset:s->next; r->size=status;
    r->total=M4A_IMAGE_BYTES; r->crc=crc;
}
