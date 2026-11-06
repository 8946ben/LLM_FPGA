#include "lm_head_v4_topk.hpp"
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>
#include <vector>
typedef ap_uint<128> beat;
const unsigned V=151936,B=V/4,T=1+V/4;
static void check(bool ok,const char* m){if(!ok){std::fprintf(stderr,"TOPK_COSIM_FAIL %s\n",m);std::exit(1);}}
static std::vector<unsigned> file(const std::string& name){std::ifstream f(name.c_str(),std::ios::binary|std::ios::ate);check(bool(f),name.c_str());size_t n=f.tellg();check(n%4==0,"file length");std::vector<unsigned>x(n/4);f.seekg(0);f.read(reinterpret_cast<char*>(x.data()),n);check(bool(f),"file read");return x;}
struct Result{ap_uint<32>status,count,route_reads,writes;ap_uint<64>score_reads;};
static Result run(const std::vector<beat>& s,const std::vector<beat>& r,std::vector<beat>& o,unsigned rc){Result x;lm_head_v4_topk_union(s.data(),r.data(),o.data(),B,rc,T,16384,&x.status,&x.count,&x.score_reads,&x.route_reads,&x.writes);return x;}
static void verify(const Result& x,const std::vector<beat>& output,const std::vector<unsigned>& ids,unsigned rc){
    check(x.status==LMH4_TOPK_OK && x.count==ids.size(),"status/count");check(x.score_reads==5ull*B && x.route_reads==rc,"real read counters");check(x.writes==1+(ids.size()+3)/4,"writes");
    check(output[0].range(31,0)==0x4449344du && output[0].range(95,64)==ids.size(),"header");
    for(size_t i=0;i<ids.size();++i)check(output[1+i/4].range((i%4)*32+31,(i%4)*32).to_uint()==ids[i],"full union ID vector");
    check(output[1+(ids.size()+3)/4]==0xabcdefu,"no output past logical padded table");
}
int main(int argc,char**argv){
    check(argc==2,"fixture path");std::string root=argv[1];
    // Full declared AXI depths are deliberately allocated for the RTL adapter.
    std::vector<beat> scores(B),routes(T),output(T,beat(0xabcdefu));
    std::vector<unsigned> words=file(root+"/english.scores.bin");check(words.size()==V,"score length");
    for(size_t i=0;i<words.size();++i)scores[i/4].range((i%4)*32+31,(i%4)*32)=words[i];
    words=file(root+"/english.routes.bin");unsigned rc=(words.size()+3)/4;
    for(size_t i=0;i<words.size();++i)routes[i/4].range((i%4)*32+31,(i%4)*32)=words[i];
    Result x=run(scores,routes,output,rc);verify(x,output,file(root+"/english.expected.bin"),rc);
    std::printf("TOPK_COSIM_CASE_PASS real_english\n");std::fflush(stdout);
    for(unsigned i=0;i<B;++i){scores[i]=0;scores[i].range(63,32)=0x80000000u;scores[i].range(127,96)=0x80000000u;}
    routes[0]=0;routes[0].range(31,0)=0x4449344du;routes[0].range(47,32)=1;routes[0].range(63,48)=4;routes[0].range(95,64)=1;routes[0].range(127,96)=V;routes[1]=V-1;
    std::fill(output.begin(),output.end(),beat(0xabcdefu));std::vector<unsigned> expected;
    for(unsigned i=0;i<16384;++i)expected.push_back(i);expected.push_back(V-1);
    x=run(scores,routes,output,2);verify(x,output,expected,2);
    std::printf("TOPK_COSIM_CASE_PASS repeated_call_zero_ties\n");std::fflush(stdout);
    scores[B-1].range(127,96)=0x7fc00000u;std::fill(output.begin(),output.end(),beat(0xabcdefu));
    x=run(scores,routes,output,2);check(x.status==LMH4_TOPK_NUMERIC && x.count==0 && x.writes==0 && x.score_reads==B,"nonfinite status/counters");
    for(unsigned i=0;i<T;++i)check(output[i]==0xabcdefu,"nonfinite must not write output");
    std::printf("M14_V4_TOPK_COSIM_TB=PASS cases=3\n");return 0;
}
