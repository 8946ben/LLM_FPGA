#include "loader_core.h"
static uint32_t table[256];
static int initialized;
uint32_t m14_crc_update(uint32_t state, const void *data, size_t bytes) {
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
uint32_t m14_crc(const void *data, size_t bytes) {
    return m14_crc_update(0xffffffffu, data, bytes)^0xffffffffu;
}
void m14_decode(m14_header *h, const uint8_t wire[32]) {
    uint32_t v[8]; unsigned i;
    for(i=0;i<8;++i) v[i]=(uint32_t)wire[4*i]|((uint32_t)wire[4*i+1]<<8)|
        ((uint32_t)wire[4*i+2]<<16)|((uint32_t)wire[4*i+3]<<24);
    h->magic=v[0]; h->version=v[1]; h->op=v[2]; h->seq=v[3];
    h->offset=v[4]; h->size=v[5]; h->total=v[6]; h->crc=v[7];
}
void m14_encode(uint8_t wire[32], const m14_header *h) {
    uint32_t v[8]={h->magic,h->version,h->op,h->seq,h->offset,h->size,h->total,h->crc};
    unsigned i,j;
    for(i=0;i<8;++i) for(j=0;j<4;++j) wire[4*i+j]=(uint8_t)(v[i]>>(8*j));
}
int m14_validate(const m14_loader *s, const m14_header *h) {
    if(h->magic!=M14_WIRE_MAGIC || h->version!=1 || h->total!=M14_WEIGHT_BYTES)
        return M14_BAD_HEADER;
    if(h->op==M14_BEGIN) return h->size==0 && h->offset==0 && h->seq==0 ? M14_OK:M14_BAD_HEADER;
    if(h->op==M14_STATUS) return h->size==0 && h->offset==0 ? M14_OK:M14_BAD_HEADER;
    if(!s->active) return M14_NOT_READY;
    if(h->seq!=s->seq || h->offset!=s->next) return M14_BAD_ORDER;
    if(h->op==M14_DATA) return h->size>0 && h->size<=M14_CHUNK_BYTES &&
        h->offset<=M14_WEIGHT_BYTES && h->size<=M14_WEIGHT_BYTES-h->offset ? M14_OK:M14_BAD_HEADER;
    if(h->op==M14_COMMIT) return h->size==0 && s->next==M14_WEIGHT_BYTES &&
        h->crc==s->expected_crc ? M14_OK:M14_BAD_ORDER;
    return M14_BAD_HEADER;
}
void m14_reply(m14_header *r, const m14_loader *s, const m14_header *h,
               uint32_t status, uint32_t crc) {
    r->magic=M14_WIRE_MAGIC; r->version=1; r->op=h->op|0x80000000u;
    r->seq=h->seq; r->offset=s->next; r->size=status;
    r->total=M14_WEIGHT_BYTES; r->crc=crc;
}
