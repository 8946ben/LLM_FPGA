#include "lm_head_v4_topk.hpp"
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <numeric>
#include <string>
#include <vector>
typedef ap_uint<128> beat;
const unsigned V=151936,B=V/4,T=1+V/4;
static void check(bool ok,const char* msg){if(!ok){std::fprintf(stderr,"TOPK_CSIM_FAIL %s\n",msg);std::exit(1);}}
template<class A>static std::vector<A> file(const std::string& path){std::ifstream f(path.c_str(),std::ios::binary|std::ios::ate);check(bool(f),path.c_str());size_t n=f.tellg();check(n%sizeof(A)==0,"file length");std::vector<A>x(n/sizeof(A));f.seekg(0);f.read(reinterpret_cast<char*>(x.data()),n);check(bool(f),"file read");return x;}
static std::vector<beat> pack(const std::vector<unsigned>& words){std::vector<beat>x((words.size()+3)/4,~beat(0));for(size_t i=0;i<words.size();++i)x[i/4].range(32*(i%4)+31,32*(i%4))=words[i];return x;}
static std::vector<beat> route(const std::vector<unsigned>& ids){std::vector<unsigned>w;w.push_back(0x4449344du);w.push_back(0x00040001u);w.push_back(ids.size());w.push_back(V);w.insert(w.end(),ids.begin(),ids.end());return pack(w);}
struct Result{ap_uint<32>status,count,route_reads,writes;ap_uint<64>score_reads;};
static Result run(const beat* s,const beat*r,beat*o,unsigned k,unsigned sc,unsigned rc,unsigned oc){Result x;lm_head_v4_topk_union(s,r,o,sc,rc,oc,k,&x.status,&x.count,&x.score_reads,&x.route_reads,&x.writes);return x;}
static void exact(const std::vector<beat>& s,const std::vector<beat>& r,const std::vector<unsigned>& expected,unsigned k,const char* name){
    std::vector<beat> out(T+1,beat(0xabcdefu));Result x=run(s.data(),r.data(),out.data(),k,B,r.size(),T);
    check(x.status==LMH4_TOPK_OK,"status");check(x.count==expected.size(),"union count");
    check(x.score_reads==5ull*B,"four histogram passes plus final marking scan");
    check(x.route_reads==r.size(),"one routed table pass");check(x.writes==1+(expected.size()+3)/4,"header and payload writes");
    check(out[0].range(31,0)==0x4449344du && out[0].range(47,32)==1 && out[0].range(63,48)==4 && out[0].range(95,64)==expected.size() && out[0].range(127,96)==V,"output M4ID header");
    for(size_t i=0;i<expected.size();++i)check(out[1+i/4].range(32*(i%4)+31,32*(i%4)).to_uint()==expected[i],"full stable union IDs");
    unsigned used=1+(expected.size()+3)/4;check(out[used]==0xabcdefu,"no extra write beyond actual union");check(out[T]==0xabcdefu,"capacity guard");
    for(size_t i=expected.size();i<((expected.size()+3)/4)*4;++i)check(out[1+i/4].range(32*(i%4)+31,32*(i%4))==0,"padding zero");
    std::printf("TOPK_EXACT_PASS %s topK=%u unionK=%u\n",name,k,unsigned(expected.size()));std::fflush(stdout);
}
int main(int argc,char**argv){
    check(argc==2,"fixture argument");std::string root=argv[1];const char* names[]={"chinese","english","code","math"};unsigned exact_cases=0,negative=0;
    for(unsigned c=0;c<4;++c){std::string n=names[c];exact(pack(file<unsigned>(root+"/"+n+".scores.bin")),pack(file<unsigned>(root+"/"+n+".routes.bin")),file<unsigned>(root+"/"+n+".expected.bin"),16384,names[c]);++exact_cases;}
    std::vector<unsigned> zero(V);for(unsigned i=0;i<V;++i)zero[i]=(i&1)?0x80000000u:0;
    std::vector<unsigned> ids;ids.push_back(151935);std::vector<beat> routed=route(ids),scores=pack(zero);const unsigned budgets[]={1,129,16384,V};
    for(unsigned j=0;j<4;++j){unsigned k=budgets[j];std::vector<unsigned> expected(k);std::iota(expected.begin(),expected.end(),0);if(k<V)expected.push_back(151935);exact(scores,routed,expected,k,"signed_zero_ties");++exact_cases;}
    // Configuration, malformed route, insufficient output, and late NaN must not write an output header/payload.
    for(unsigned kind=0;kind<10;++kind){
        std::vector<beat> r=routed;unsigned k=16384,sc=B,rc=r.size(),oc=T;
        if(kind==0)k=0;if(kind==1)k=V+1;if(kind==2)sc=B-1;if(kind==3)rc=0;
        if(kind==4)r[0].range(31,0)=0;if(kind==5)r[1].range(31,0)=V;if(kind==6)oc=1;
        if(kind==8){std::vector<unsigned> bad;bad.push_back(127);bad.push_back(127);r=route(bad);rc=r.size();}
        if(kind==9){std::vector<unsigned> bad;bad.push_back(128);bad.push_back(127);r=route(bad);rc=r.size();}
        std::vector<beat> out(T+1,beat(0xabcdefu));if(kind==7)scores[B-1].range(127,96)=0x7fc00000u;
        Result x=run(scores.data(),r.data(),out.data(),k,sc,rc,oc);
        check(x.status!=LMH4_TOPK_OK && x.writes==0 && x.count==0 && out[0]==0xabcdefu,"negative no output writes");
        if(kind>=3 && kind!=7)check(x.status==LMH4_TOPK_BAD_ROUTE && x.score_reads==0,"malformed route rejected before score reads");
        if(kind==7)check(x.status==LMH4_TOPK_NUMERIC && x.score_reads==B,"nonfinite first pass only");++negative;
    }
    std::printf("M14_V4_TOPK_CSIM=PASS exact_cases=%u invalid_cases=%u\n",exact_cases,negative);return 0;
}
