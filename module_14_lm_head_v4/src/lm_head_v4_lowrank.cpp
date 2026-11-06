#include "lm_head_v4_lowrank.hpp"
#include "accepted_numeric_core.hpp"
using namespace lmh4_detail;
namespace {
// B has just 128 output rows: preserving the accepted dot order here is
// inexpensive. The large A scan deliberately uses a separate pipelined tree.
bool project_b(const ap_uint<128>* b,const float hidden[8][112],float z[16][8]) {
#pragma HLS INLINE off
    bool bad=false;
project_b_row:
    for(unsigned row=0;row<128;++row){
        float p[8][16];
#pragma HLS ARRAY_PARTITION variable=p complete dim=1
        for(unsigned lane=0;lane<8;++lane){
#pragma HLS UNROLL
            for(unsigned s=0;s<16;++s){
#pragma HLS UNROLL
                p[lane][s]=0.0f;
            }
        }
project_b_word:
        for(unsigned word=0;word<112;++word){
#pragma HLS PIPELINE II=1
#pragma HLS DEPENDENCE variable=p inter RAW distance=16 true
            const ap_uint<128> packed=b[row*112+word];
            bool word_bad=false;
            for(unsigned lane=0;lane<8;++lane){
#pragma HLS UNROLL
                const float coefficient=bf16_to_float(packed.range(16*lane+15,16*lane));
                word_bad|=!finite_float(coefficient);
                const float product=hidden[lane][word]*coefficient;
                p[lane][word&15]=p[lane][word&15]+product;
            }
            bad|=word_bad;
        }
        const float value=reduce_partials(p);z[row>>3][row&7]=value;bad|=!finite_float(value);
    }
    return !bad;
}
void read_a(const ap_uint<128>* a,unsigned rows,hls::stream<ap_uint<128> >& words){
read_a_word:
    for(unsigned index=0;index<rows*16;++index){
#pragma HLS PIPELINE II=1
#pragma HLS LOOP_TRIPCOUNT min=16 max=2430976
        words.write(a[index]);
    }
}
void product_context(hls::stream<ap_uint<128> >& words,const float z[16][8],unsigned rows,
                     hls::stream<ap_uint<512> >& contexts,hls::stream<bool>& finite){
    float slots[16];
#pragma HLS ARRAY_PARTITION variable=slots complete
    bool bad=false;
product_word:
    for(unsigned index=0;index<rows*16;++index){
#pragma HLS PIPELINE II=1
#pragma HLS LOOP_TRIPCOUNT min=16 max=2430976
        const unsigned word=index&15;const ap_uint<128> packed=words.read();
        float products[8];
#pragma HLS ARRAY_PARTITION variable=products complete
        bool word_bad=false;
        for(unsigned lane=0;lane<8;++lane){
#pragma HLS UNROLL
            const float coefficient=bf16_to_float(packed.range(16*lane+15,16*lane));
            word_bad|=!finite_float(coefficient);products[lane]=z[word][lane]*coefficient;
        }
        const float p01=products[0]+products[1],p23=products[2]+products[3];
        const float p45=products[4]+products[5],p67=products[6]+products[7];
        const float p03=p01+p23,p47=p45+p67;
        const float value=p03+p47;slots[word]=value;bad|=word_bad;
        if(word==15){
            ap_uint<512> context=0;
            for(unsigned s=0;s<16;++s){
#pragma HLS UNROLL
                context.range(32*s+31,32*s)=float_to_bits(s==15?value:slots[s]);
            }
            contexts.write(context);
        }
    }
    finite.write(!bad);
}
void tree_context(hls::stream<ap_uint<512> >& contexts,unsigned rows,hls::stream<float>& raw){
tree_row:
    for(unsigned row=0;row<rows;++row){
#pragma HLS PIPELINE II=1
#pragma HLS LOOP_TRIPCOUNT min=1 max=151936
        const ap_uint<512> context=contexts.read();
        float p[16],a[8],b[4],c[2];
#pragma HLS ARRAY_PARTITION variable=p complete
#pragma HLS ARRAY_PARTITION variable=a complete
#pragma HLS ARRAY_PARTITION variable=b complete
#pragma HLS ARRAY_PARTITION variable=c complete
        for(unsigned i=0;i<16;++i){
#pragma HLS UNROLL
            p[i]=bits_to_float(context.range(32*i+31,32*i).to_uint());
        }
        for(unsigned i=0;i<8;++i){
#pragma HLS UNROLL
            a[i]=p[2*i]+p[2*i+1];
        }
        for(unsigned i=0;i<4;++i){
#pragma HLS UNROLL
            b[i]=a[2*i]+a[2*i+1];
        }
        for(unsigned i=0;i<2;++i){
#pragma HLS UNROLL
            c[i]=b[2*i]+b[2*i+1];
        }
        raw.write(c[0]+c[1]);
    }
}
void write_preview(hls::stream<float>& raw,const ap_uint<128>* history,ap_uint<128>* output,
                   unsigned rows,bool enable,float penalty,bool& ok){
    bool bad=false;ap_uint<128> packed=0,hist=0;
write_policy_row:
    for(unsigned row=0;row<rows;++row){
#pragma HLS PIPELINE II=1
#pragma HLS LOOP_TRIPCOUNT min=1 max=151936
        const float value=raw.read();if(enable && (row&127)==0)hist=history[row>>7];
        const bool seen=enable && hist[row&127]!=0;
        const float result=seen?(value<0?value*penalty:value/penalty):value;
        bad|=!finite_float(result);packed.range(32*(row&3)+31,32*(row&3))=float_to_bits(result);
        if((row&3)==3 || row+1==rows){output[row>>2]=packed;packed=0;}
    }
    ok=!bad;
}
void join_flags(hls::stream<bool>& finite,bool scores_ok,bool& ok){
#pragma HLS INLINE off
    const bool factors_ok=finite.read();ok=scores_ok && factors_ok;
}
void scan_a(const ap_uint<128>* a,const float z[16][8],const ap_uint<128>* history,
            ap_uint<128>* output,unsigned rows,bool enable,float penalty,bool& ok){
#pragma HLS DATAFLOW
    hls::stream<ap_uint<128> > words("a_words");
    hls::stream<ap_uint<512> > contexts("rank128_context");
    hls::stream<float> raw("preview_raw");hls::stream<bool> finite("factor_finite");
#pragma HLS STREAM variable=words depth=64
#pragma HLS STREAM variable=contexts depth=4
#pragma HLS STREAM variable=raw depth=64
#pragma HLS STREAM variable=finite depth=2
    read_a(a,rows,words);product_context(words,z,rows,contexts,finite);tree_context(contexts,rows,raw);
    bool scores_ok;write_preview(raw,history,output,rows,enable,penalty,scores_ok);
    join_flags(finite,scores_ok,ok);
}
}
extern "C" void lm_head_v4_lowrank(
    const ap_uint<128>* hidden,const ap_uint<128>* b_transposed,const ap_uint<128>* a_factor,
    const ap_uint<128>* history,ap_uint<128>* policy_preview,
    ap_uint<32> rows,ap_uint<32> hidden_capacity,ap_uint<32> b_capacity,
    ap_uint<32> a_capacity,ap_uint<32> history_capacity,ap_uint<32> output_capacity,
    ap_uint<32> enable_penalty,float penalty,ap_uint<32>* status,
    ap_uint<64>* factor_read_beats,ap_uint<32>* output_write_beats){
#pragma HLS INTERFACE m_axi port=hidden offset=slave bundle=hidden depth=112
#pragma HLS INTERFACE m_axi port=b_transposed offset=slave bundle=b depth=14336 max_read_burst_length=64 num_read_outstanding=8
#pragma HLS INTERFACE m_axi port=a_factor offset=slave bundle=a depth=2430976 max_read_burst_length=64 num_read_outstanding=16
#pragma HLS INTERFACE m_axi port=history offset=slave bundle=history depth=1187
#pragma HLS INTERFACE m_axi port=policy_preview offset=slave bundle=output depth=37984 max_write_burst_length=64 num_write_outstanding=8
#pragma HLS INTERFACE s_axilite port=hidden bundle=control
#pragma HLS INTERFACE s_axilite port=b_transposed bundle=control
#pragma HLS INTERFACE s_axilite port=a_factor bundle=control
#pragma HLS INTERFACE s_axilite port=history bundle=control
#pragma HLS INTERFACE s_axilite port=policy_preview bundle=control
#pragma HLS INTERFACE s_axilite port=rows bundle=control
#pragma HLS INTERFACE s_axilite port=hidden_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=b_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=a_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=history_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=output_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=enable_penalty bundle=control
#pragma HLS INTERFACE s_axilite port=penalty bundle=control
#pragma HLS INTERFACE s_axilite port=status bundle=control
#pragma HLS INTERFACE s_axilite port=factor_read_beats bundle=control
#pragma HLS INTERFACE s_axilite port=output_write_beats bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
    *status=LMH4_LR_BAD_CONFIG;*factor_read_beats=0;*output_write_beats=0;
    const unsigned n=rows.to_uint();const bool enable=enable_penalty!=0;
    if(n==0 || n>151936 || hidden_capacity<112 || b_capacity<14336 || a_capacity<n*16 ||
       output_capacity<(n+3)/4 || (enable && (history_capacity<(n+127)/128 || !finite_float(penalty) || penalty<1)))return;
    float h[8][112],z[16][8];
#pragma HLS ARRAY_PARTITION variable=h complete dim=1
#pragma HLS ARRAY_PARTITION variable=z complete dim=2
    load_hidden(hidden,h);bool bad=false;
check_hidden:
    for(unsigned word=0;word<112;++word){
#pragma HLS PIPELINE II=1
        bool word_bad=false;
        for(unsigned lane=0;lane<8;++lane){
#pragma HLS UNROLL
            word_bad|=!finite_float(h[lane][word]);
        }
        bad|=word_bad;
    }
    if(bad){*status=LMH4_LR_NUMERIC;return;}
    const bool z_ok=project_b(b_transposed,h,z);*factor_read_beats=14336;
    if(!z_ok){*status=LMH4_LR_NUMERIC;return;}
    bool ok;scan_a(a_factor,z,history,policy_preview,n,enable,penalty,ok);
    *factor_read_beats=14336+n*16;*output_write_beats=(n+3)/4;
    *status=ok?LMH4_LR_OK:LMH4_LR_NUMERIC;
}
