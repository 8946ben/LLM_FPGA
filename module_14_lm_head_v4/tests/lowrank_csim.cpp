#include "lm_head_v4_lowrank.hpp"
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>
#include <vector>
typedef ap_uint<128> beat;
static void check(bool ok,const char* msg){if(!ok){std::fprintf(stderr,"LOWRANK_FAIL %s\n",msg);std::exit(1);}}
static std::vector<beat> file(const std::string& path){
    std::ifstream f(path.c_str(),std::ios::binary|std::ios::ate);check(bool(f),path.c_str());unsigned bytes=f.tellg();check(bytes%16==0,"length");
    std::vector<unsigned> w(bytes/4);f.seekg(0);f.read(reinterpret_cast<char*>(w.data()),bytes);check(bool(f),"read");
    std::vector<beat> out(bytes/16);for(unsigned i=0;i<w.size();++i)out[i/4].range(32*(i%4)+31,32*(i%4))=w[i];return out;
}
struct Result{ap_uint<32>status,writes;ap_uint<64>reads;};
static Result run(const beat*h,const beat*b,const beat*a,const beat*hist,beat*out,unsigned rows,
                  unsigned hc=112,unsigned bc=14336,unsigned ac=2430976,unsigned yc=1187,unsigned oc=37984,
                  unsigned enable=1,float penalty=1.1f){
    Result r;lm_head_v4_lowrank(h,b,a,hist,out,rows,hc,bc,ac,yc,oc,enable,penalty,&r.status,&r.reads,&r.writes);return r;
}
int main(int argc,char**argv){
    check(argc==2 || argc==3,"fixture directory");const bool rtl=argc==3;std::string root=argv[1];
    const std::vector<beat>b=file(root+"/bt.bf16.bin"),a=file(root+"/a.bf16.bin");
    const char* names[]={"chinese","english","code","math"};unsigned exact=0,invalid=0,numeric=0;
    for(unsigned c=0;c<(rtl?1:4);++c){
        std::string n=names[c];std::vector<beat>h=file(root+"/"+n+".hidden.bin"),hist=file(root+"/"+n+".history.bin"),gold=file(root+"/"+n+".scores.bin");
        unsigned rows=rtl?256:151936;std::vector<beat>out((rows+3)/4+1,beat(0xabcdef));
        Result r=run(h.data(),b.data(),a.data(),hist.data(),out.data(),rows,112,14336,rows*16,1187,(rows+3)/4);
        check(r.status==LMH4_LR_OK && r.reads==14336+rows*16 && r.writes==(rows+3)/4,"real status/counts");
        for(unsigned i=0;i<(rows+3)/4;++i)check(out[i]==gold[i],"all policy preview bits");check(out.back()==0xabcdef,"output guard");
        std::printf("LOWRANK_EXACT_PASS %s rows=%u\n",names[c],rows);std::fflush(stdout);++exact;
    }
    std::vector<beat>h(112,beat(0)),hist(1187,beat(0)),zero_b(14336,beat(0)),small_a(48,beat(0)),out(3,beat(0xabcdef));
    Result repeat=run(h.data(),zero_b.data(),small_a.data(),hist.data(),out.data(),3,112,14336,48,1187,1,0);
    check(repeat.status==LMH4_LR_OK && out[0]==0 && out[1]==0xabcdef,"repeat call clears contexts and pads");++exact;
    if(!rtl)for(unsigned kind=0;kind<10;++kind){
        unsigned rows=3,hc=112,bc=14336,ac=48,yc=1187,oc=1,en=1;float penalty=1.1f;
        if(kind==0)rows=0;if(kind==1)rows=151937;if(kind==2)hc=111;if(kind==3)bc=14335;
        if(kind==4)ac=47;if(kind==5)yc=0;if(kind==6)oc=0;if(kind==7)penalty=0.5f;
        if(kind==8){union{unsigned u;float f;}x;x.u=0x7fc00000;penalty=x.f;}if(kind==9){union{unsigned u;float f;}x;x.u=0x7f800000;penalty=x.f;}
        out.assign(3,beat(0xabcdef));Result r=run(0,0,0,0,out.data(),rows,hc,bc,ac,yc,oc,en,penalty);
        check(r.status==LMH4_LR_BAD_CONFIG && r.reads==0 && r.writes==0 && out[0]==0xabcdef,"invalid preflight no reads/writes");++invalid;
    }
    for(unsigned kind=0;kind<(rtl?1:3);++kind){
        std::vector<beat>bad_h=h,bad_b=zero_b,bad_a=small_a;out.assign(3,beat(0xabcdef));
        if(kind==0)bad_h[111].range(127,112)=0x7fc0;if(kind==1)bad_b.back().range(127,112)=0x7f80;if(kind==2)bad_a.back().range(127,112)=0x7fc0;
        Result r=run(bad_h.data(),bad_b.data(),bad_a.data(),hist.data(),out.data(),3,112,14336,48,1187,1);
        check(r.status==LMH4_LR_NUMERIC,"nonfinite status");
        if(kind<2)check(r.writes==0 && out[0]==0xabcdef,"hidden/B rejection before preview");
        else check(r.writes==1,"A scan completes but output invalid by status");++numeric;
    }
    std::printf("M14_V4_LOWRANK_CSIM=PASS exact=%u invalid=%u numeric=%u rtl_subset=%u\n",exact,invalid,numeric,rtl?1:0);return 0;
}
