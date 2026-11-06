#include "lm_head_v4_candidate.hpp"
#include "accepted_numeric_core.hpp"
using namespace lmh4_detail;
namespace {
bool validate_table(const ap_uint<128>* table,ap_uint<32> capacity,ap_uint<32>& count,ap_uint<64>& reads) {
    if(capacity<1)return false;
    const ap_uint<128> header=table[0];++reads;
    count=header.range(95,64);
    if(header.range(31,0)!=0x4449344du || header.range(47,32)!=1 || header.range(63,48)!=4 ||
       header.range(127,96)!=LMH4_VOCAB || count==0 || count>LMH4_VOCAB)return false;
    if(capacity<1+(count+3)/4)return false;
    const unsigned words=(count.to_uint()+3u)>>2;
    ap_uint<32> previous=0;bool bad=false;
validate_beat_loop:
    for(unsigned word=0;word<words;++word) {
#pragma HLS PIPELINE II=1
#pragma HLS LOOP_TRIPCOUNT min=1 max=37984
        const ap_uint<128> packed=table[word+1];
        const ap_uint<160> joined=(ap_uint<160>(packed)<<32)|previous;
        bool word_bad=false;
validate_four_lanes:
        for(int lane=0;lane<4;++lane) {
#pragma HLS UNROLL
            const unsigned row=word*4+lane;
            const ap_uint<32> id=joined.range(lane*32+63,lane*32+32);
            const ap_uint<32> prior=joined.range(lane*32+31,lane*32);
            const bool active=row<count;
            word_bad|=active && (id>=LMH4_VOCAB || (row!=0 && id<=prior));
        }
        // An incomplete final beat has no successor, so its unused lane3 is
        // never compared against a later valid ID. Padding remains ignored.
        previous=packed.range(127,96);bad|=word_bad;
    }
    reads+=words;
    return !bad;
}
void gather_rows(const ap_uint<128>* weight,const ap_uint<128>* table,ap_uint<32> count,
                 hls::stream<ap_uint<128> >& weights,hls::stream<ap_uint<32> >& ids) {
    ap_uint<128> packed=0;
gather_row_loop:
    for(ap_uint<32> row=0;row<count;++row) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=151936
        if((row&3)==0)packed=table[1+(row>>2)];
        const int lane=row.to_uint()&3;const ap_uint<32> id=packed.range(32*lane+31,32*lane);
        ids.write(id);
        const ap_uint<64> base=ap_uint<64>(id)*LMH_V2_HIDDEN_WORDS;
gather_word_loop:
        for(int word=0;word<LMH_V2_HIDDEN_WORDS;++word) {
#pragma HLS PIPELINE II=1
            weights.write(weight[base+word]);
        }
    }
}
void candidate_policy(hls::stream<float>& raw,hls::stream<ap_uint<32> >& ids,const ap_uint<128>* history,
    ap_uint<128>* outputs,ap_uint<32> count,bool write,bool enable,float penalty,
    ap_uint<32>& best_token,float& best_score,ap_uint<32>& history_reads,bool& numeric_error) {
    ap_uint<128> history_word=0,packed=0;ap_uint<32> cached=0xffffffffu;
    best_token=0;best_score=0;history_reads=0;numeric_error=false;
candidate_policy_loop:
    for(ap_uint<32> row=0;row<count;++row) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=151936
        const ap_uint<32> id=ids.read();const float value=raw.read();
        if(write) {
            ap_uint<64> record=0;record.range(31,0)=id;record.range(63,32)=float_to_bits(value);
            const int lane=row.to_uint()&1;packed.range(lane*64+63,lane*64)=record;
            if(lane==1 || row+1==count){outputs[row>>1]=packed;packed=0;}
        }
        bool seen=false;
        if(enable){
            const ap_uint<32> block=id>>7;
            if(block!=cached){history_word=history[block];cached=block;++history_reads;}
            seen=history_word[id.to_uint()&127]!=0;
        }
        const bool valid=finite_float(value);numeric_error|=!valid;
        float policy_score=valid?value:bits_to_float(0xff800000u);
        if(valid && enable && seen)policy_score=value<0?value*penalty:value/penalty;
        if(valid && !finite_float(policy_score)){numeric_error=true;policy_score=bits_to_float(0xff800000u);}
        if(row==0 || policy_score>best_score || (policy_score==best_score && id<best_token)){
            best_token=id;best_score=policy_score;
        }
    }
}
void candidate_dataflow(const ap_uint<128>* weight,const ap_uint<128>* table,
    const float cache[LMH_V2_H_LANES][LMH_V2_HIDDEN_WORDS],const ap_uint<128>* history,
    ap_uint<128>* outputs,ap_uint<32> count,bool write,bool enable,float penalty,
    ap_uint<32>& best_token,float& best_score,ap_uint<32>& history_reads,bool& numeric_error) {
#pragma HLS DATAFLOW
    hls::stream<ap_uint<128> > weights("weights");
    hls::stream<ap_uint<32> > ids("ids");
    hls::stream<accumulator_slice_t> contexts("contexts");
    hls::stream<float> raw("raw");
#pragma HLS STREAM variable=weights depth=128
#pragma HLS STREAM variable=ids depth=32
#pragma HLS STREAM variable=contexts depth=32
#pragma HLS STREAM variable=raw depth=32
    gather_rows(weight,table,count,weights,ids);
    dot_product_rows(weights,cache,count,contexts);
    reduce_rows(contexts,raw,count);
    candidate_policy(raw,ids,history,outputs,count,write,enable,penalty,best_token,best_score,history_reads,numeric_error);
}
}
extern "C" void lm_head_v4_candidate(
    const ap_uint<128>* hidden,const ap_uint<128>* weight,const ap_uint<128>* history,
    const ap_uint<128>* candidate_table,ap_uint<128>* candidate_scores,
    ap_uint<32> candidate_capacity_beats,ap_uint<32> score_capacity_beats,
    ap_uint<32> write_scores,ap_uint<32> enable_penalty,float penalty,
    ap_uint<32>* status,ap_uint<32>* token,float* score,ap_uint<32>* processed,
    ap_uint<64>* index_read_beats,ap_uint<64>* weight_read_beats,
    ap_uint<32>* history_read_beats,ap_uint<32>* score_write_beats,ap_uint<32>* output_crc) {
#pragma HLS INTERFACE m_axi port=hidden offset=slave bundle=hidden depth=112 max_read_burst_length=64 num_read_outstanding=4
#pragma HLS INTERFACE m_axi port=weight offset=slave bundle=weight depth=17016832 max_read_burst_length=16 num_read_outstanding=16 latency=64
#pragma HLS INTERFACE m_axi port=history offset=slave bundle=history depth=1187 max_read_burst_length=16 num_read_outstanding=4
#pragma HLS INTERFACE m_axi port=candidate_table offset=slave bundle=candidate depth=37985 max_read_burst_length=64 num_read_outstanding=4
#pragma HLS INTERFACE m_axi port=candidate_scores offset=slave bundle=scores depth=75968 max_write_burst_length=64 num_write_outstanding=8
#pragma HLS INTERFACE s_axilite port=hidden bundle=control
#pragma HLS INTERFACE s_axilite port=weight bundle=control
#pragma HLS INTERFACE s_axilite port=history bundle=control
#pragma HLS INTERFACE s_axilite port=candidate_table bundle=control
#pragma HLS INTERFACE s_axilite port=candidate_scores bundle=control
#pragma HLS INTERFACE s_axilite port=candidate_capacity_beats bundle=control
#pragma HLS INTERFACE s_axilite port=score_capacity_beats bundle=control
#pragma HLS INTERFACE s_axilite port=write_scores bundle=control
#pragma HLS INTERFACE s_axilite port=enable_penalty bundle=control
#pragma HLS INTERFACE s_axilite port=penalty bundle=control
#pragma HLS INTERFACE s_axilite port=status bundle=control
#pragma HLS INTERFACE s_axilite port=token bundle=control
#pragma HLS INTERFACE s_axilite port=score bundle=control
#pragma HLS INTERFACE s_axilite port=processed bundle=control
#pragma HLS INTERFACE s_axilite port=index_read_beats bundle=control
#pragma HLS INTERFACE s_axilite port=weight_read_beats bundle=control
#pragma HLS INTERFACE s_axilite port=history_read_beats bundle=control
#pragma HLS INTERFACE s_axilite port=score_write_beats bundle=control
#pragma HLS INTERFACE s_axilite port=output_crc bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
    *status=LMH4_BAD_CONFIG;*token=0;*score=0;*processed=0;*index_read_beats=0;
    *weight_read_beats=0;*history_read_beats=0;*score_write_beats=0;*output_crc=0;
    if(write_scores>1 || enable_penalty>1 || (enable_penalty && (!finite_float(penalty)||penalty<1)))return;
    ap_uint<32> count=0;ap_uint<64> reads=0;
    if(!validate_table(candidate_table,candidate_capacity_beats,count,reads)){*index_read_beats=reads;*status=LMH4_BAD_TABLE;return;}
    *index_read_beats=reads;
    if(write_scores && score_capacity_beats<(count+1)/2)return;
    float cache[LMH_V2_H_LANES][LMH_V2_HIDDEN_WORDS];
#pragma HLS ARRAY_PARTITION variable=cache complete dim=1
    load_hidden(hidden,cache);
    ap_uint<32> best=0,hreads=0;float value=0;bool error=false;
    candidate_dataflow(weight,candidate_table,cache,history,candidate_scores,count,write_scores!=0,enable_penalty!=0,penalty,best,value,hreads,error);
    *index_read_beats=reads+(count+3)/4;*weight_read_beats=ap_uint<64>(count)*LMH_V2_HIDDEN_WORDS;
    *history_read_beats=hreads;
    if(write_scores)*score_write_beats=(count+1)/2;
    *processed=count;
    *token=best;*score=value;*status=error?LMH4_NUMERIC_ERROR:LMH4_OK;
    if(!error)*output_crc=crc32_token_score(best,float_to_bits(value));
}
