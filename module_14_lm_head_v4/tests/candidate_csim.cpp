#include "lm_head_v4_candidate.hpp"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <set>
#include <string>
#include <vector>
typedef ap_uint<128> beat;
static unsigned bits(float x){union{float f;unsigned u;}v;v.f=x;return v.u;}
static void require(bool ok,const char* what){if(!ok){std::fprintf(stderr,"CSIM_FAIL %s\n",what);std::exit(1);}}
template<class T>static std::vector<T> file(const std::string& name){
    std::ifstream f(name.c_str(),std::ios::binary|std::ios::ate);require(bool(f),name.c_str());
    const std::streamoff n=f.tellg();require(n%sizeof(T)==0,"file shape");std::vector<T> v(n/sizeof(T));f.seekg(0);f.read(reinterpret_cast<char*>(v.data()),n);require(bool(f),"read");return v;
}
static std::vector<beat> packed_bf16(const std::vector<unsigned short>& v){
    require(v.size()%8==0,"bf16 beat shape");std::vector<beat> b(v.size()/8);
    for(size_t i=0;i<v.size();++i)b[i/8].range(16*(i%8)+15,16*(i%8))=v[i];return b;
}
static std::vector<beat> table(const std::vector<unsigned>& ids){
    std::vector<beat> t(1+(ids.size()+3)/4);t[0].range(31,0)=0x4449344du;t[0].range(47,32)=1;
    t[0].range(63,48)=4;t[0].range(95,64)=ids.size();t[0].range(127,96)=LMH4_VOCAB;
    // Invalid ID padding must be ignored past valid K, including 1/2/3 tails.
    for(size_t i=1;i<t.size();++i)t[i]=~beat(0);
    for(size_t i=0;i<ids.size();++i)t[1+i/4].range(32*(i%4)+31,32*(i%4))=ids[i];return t;
}
struct Result{ap_uint<32> status,token,processed,history,outputs,crc;ap_uint<64> indices,weights;float score;};
static Result invoke(const beat* h,const beat* w,const beat* hist,const beat* t,beat* o,unsigned tc,unsigned oc,unsigned debug=1,unsigned enable=1,float penalty=1.1f){
    Result r;lm_head_v4_candidate(h,w,hist,t,o,tc,oc,debug,enable,penalty,&r.status,&r.token,&r.score,&r.processed,&r.indices,&r.weights,&r.history,&r.outputs,&r.crc);return r;
}
static unsigned crc(unsigned token,unsigned score){
    unsigned c=0xffffffffu;unsigned values[2]={token,score};
    for(int j=0;j<2;++j)for(int b=0;b<4;++b){c^=(values[j]>>(8*b))&255;for(int i=0;i<8;++i)c=(c>>1)^((c&1)?0xedb88320u:0);}
    return c^0xffffffffu;
}
static void exact_case(const std::vector<beat>& h,const std::vector<beat>& w,const std::vector<beat>& hist,
    const std::vector<float>& raw,const std::vector<float>& scores,const std::vector<unsigned>& ids,const char* label){
    std::vector<beat> t=table(ids);unsigned beats=(ids.size()+1)/2;std::vector<beat> output(beats+1);output[beats]=0xabcdefu;
    Result r=invoke(h.data(),w.data(),hist.data(),t.data(),output.data(),t.size(),beats);
    require(r.status==LMH4_OK,"status");require(r.processed==ids.size(),"processed");
    require(r.indices==1+2*((ids.size()+3)/4),"index includes validation second read");require(r.weights==ids.size()*112ull,"weight beats");
    std::set<unsigned> blocks;unsigned best=ids[0];
    for(size_t i=0;i<ids.size();++i){
        unsigned id=ids[i];blocks.insert(id>>7);if(scores[id]>scores[best] || (scores[id]==scores[best]&&id<best))best=id;
        int lane=i&1;unsigned got_id=output[i/2].range(lane*64+31,lane*64).to_uint();
        unsigned got_raw=output[i/2].range(lane*64+63,lane*64+32).to_uint();
        require(got_id==id,"global ID output");require(got_raw==bits(raw[id]),"raw score bits equal canonical full logits");
    }
    require(r.token==best && bits(r.score)==bits(scores[best]),"penalty winner and score bits");
    require(r.crc==crc(best,bits(scores[best])),"production token score crc");
    require(r.history==blocks.size(),"global history cache beats");require(r.outputs==beats,"sparse output beats");
    require(output[beats]==0xabcdefu,"no write beyond padded capacity");
    if(ids.size()&1)require(output[beats-1].range(127,64)==0,"odd output padding zero");
    std::printf("CSIM_EXACT_PASS %s K=%u token=%u\n",label,unsigned(ids.size()),best);std::fflush(stdout);
}
int main(int argc,char**argv){
    require(argc==2,"asset directory arg");std::string root=argv[1];
    std::vector<beat> weights=packed_bf16(file<unsigned short>(root+"/shared_vocab_weight.bf16.bin"));
    unsigned exact=0;
    for(unsigned step=0;step<8;++step){
        char name[40];std::sprintf(name,"/trace/step_%02u/",step);std::string dir=root+name;
        std::vector<beat> h=packed_bf16(file<unsigned short>(dir+"hidden.bf16.bin"));
        std::vector<unsigned> words=file<unsigned>(dir+"history_bitmap.u32.bin");std::vector<beat> hist((words.size()+3)/4);
        for(size_t i=0;i<words.size();++i)hist[i/4].range((i%4)*32+31,(i%4)*32)=words[i];
        std::vector<float> raw=file<float>(dir+"raw_logits.fp32.bin"),scores=file<float>(dir+"processed_scores.fp32.bin");
        const unsigned edge[]={0,1,31,32,127,128,255,256,65535,65536,151934,151935};std::vector<unsigned> ids(edge,edge+12);
        exact_case(h,weights,hist,raw,scores,ids,"boundaries");++exact;
        ids.clear();for(unsigned j=0;j<2049;++j)ids.push_back((j*73+step*19)%LMH4_VOCAB);std::sort(ids.begin(),ids.end());
        exact_case(h,weights,hist,raw,scores,ids,"noncontiguous_odd2049");++exact;
        if(step==0){ids.clear();for(unsigned j=0;j<LMH4_VOCAB;++j)ids.push_back(j);exact_case(h,weights,hist,raw,scores,ids,"all_vocab_identity");++exact;}
        if(step==0){
            std::vector<beat> t=table(std::vector<unsigned>(1,127));Result r=invoke(h.data(),weights.data(),hist.data(),t.data(),0,t.size(),0,0);
            require(r.status==LMH4_OK && r.outputs==0 && r.token==127,"debug off no output pointer");
            r=invoke(h.data(),weights.data(),hist.data(),t.data(),0,t.size(),0,0,0,0.5f);
            require(r.status==LMH4_OK && r.history==0 && r.outputs==0 && bits(r.score)==bits(raw[127]),"penalty off ignores history and disabled penalty parameter");
        }
    }
    // Malformed jobs use null hidden/weight: validation must precede their reads.
    std::vector<unsigned> valid;valid.push_back(31);valid.push_back(128);valid.push_back(151935);
    unsigned negative=0;
    for(unsigned kind=0;kind<9;++kind){
        std::vector<beat> t=table(valid);unsigned tc=t.size(),oc=2;
        if(kind==0)t[0].range(31,0)=0;
        if(kind==1)t[0].range(47,32)=2;
        if(kind==2)t[0].range(95,64)=0;
        if(kind==3)t[0].range(127,96)=100;
        if(kind==4)t[1].range(63,32)=31;
        if(kind==5)t[1].range(95,64)=LMH4_VOCAB;
        if(kind==6)t[1].range(95,64)=1;
        if(kind==7)tc=1;
        if(kind==8)oc=1;
        Result r=invoke(0,0,0,t.data(),0,tc,oc);
        require(r.status!=LMH4_OK && r.weights==0 && r.processed==0 && r.outputs==0,"invalid job no compute/write");++negative;
    }
    Result empty=invoke(0,0,0,0,0,0,0);require(empty.status==LMH4_BAD_TABLE && empty.indices==0,"zero header capacity");++negative;
    Result invalid=invoke(0,0,0,0,0,0,0,0,1,0.5f);require(invalid.status==LMH4_BAD_CONFIG && invalid.indices==0,"invalid penalty before table");++negative;
    invalid=invoke(0,0,0,0,0,0,0,2,1);require(invalid.status==LMH4_BAD_CONFIG && invalid.indices==0,"invalid debug flag before table");++negative;
    invalid=invoke(0,0,0,0,0,0,0,0,2);require(invalid.status==LMH4_BAD_CONFIG && invalid.indices==0,"invalid penalty flag before table");++negative;
    // Nonzero first ID, history blocks, explicit tie and NaN coverage boundary.
    std::vector<unsigned> tie;tie.push_back(31);tie.push_back(32);tie.push_back(127);tie.push_back(128);tie.push_back(151935);
    std::vector<beat> h(112),hist(1187),t=table(tie),output(3);
    for(size_t i=0;i<tie.size();++i)for(unsigned word=0;word<112;++word)weights[tie[i]*112+word]=0;
    weights[0].range(15,0)=0x7fc0; // unselected bad row is deliberately outside coverage
    Result r=invoke(h.data(),weights.data(),hist.data(),t.data(),output.data(),t.size(),3);
    require(r.status==LMH4_OK && r.token==31 && r.history==3,"tie/global history/skipped NaN");
    weights[31*112].range(15,0)=0x7fc0;r=invoke(h.data(),weights.data(),hist.data(),t.data(),output.data(),t.size(),3);
    require(r.status==LMH4_NUMERIC_ERROR && r.crc==0,"selected NaN status and CRC invalidation");
    std::printf("M14_V4_CSIM=PASS exact_cases=%u invalid_cases=%u special_cases=4\n",exact,negative);return 0;
}
