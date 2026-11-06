#include "lm_head_v4_selector.hpp"
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>
#include <vector>
typedef ap_uint<128> beat;
const unsigned long long WINDOW=335544320ull,DESC=1048576;
static unsigned long long historyOffset=0;
static void check(bool b,const char*m){if(!b){std::fprintf(stderr,"SELECTOR_FAIL %s\n",m);std::exit(1);}}
static std::vector<beat> file(const std::string&p){std::ifstream f(p.c_str(),std::ios::binary|std::ios::ate);check(bool(f),p.c_str());unsigned bytes=f.tellg();check(bytes%4==0,"file words");std::vector<unsigned>w(bytes/4);f.seekg(0);f.read(reinterpret_cast<char*>(w.data()),bytes);check(bool(f),"read");std::vector<beat>v((w.size()+3)/4,beat(0));for(unsigned i=0;i<w.size();++i)v[i/4].range(32*(i%4)+31,32*(i%4))=w[i];return v;}
static void load(std::vector<beat>&arena,unsigned long long offset,const std::string&p){
    std::ifstream f(p.c_str(),std::ios::binary|std::ios::ate);check(bool(f),p.c_str());unsigned long long bytes=f.tellg();check(bytes%16==0 && offset+bytes<=WINDOW,"file region");f.seekg(0);
    std::vector<unsigned>words(262144);unsigned long long target=offset/16;
    while(bytes){unsigned n=bytes<1048576?unsigned(bytes):1048576;f.read(reinterpret_cast<char*>(words.data()),n);check(bool(f),"region read");for(unsigned i=0;i<n/16;++i){beat b=0;for(unsigned j=0;j<4;++j)b.range(32*j+31,32*j)=words[i*4+j];arena[target++]=b;}bytes-=n;}
}
struct Result{ap_uint<32>status,stage,child,route_count,k,fallback,token,crc;float score;};
static Result run(beat*arena,unsigned long long window=WINDOW,unsigned long long offset=DESC,unsigned command=SEL_RUN){Result r;lm_head_v4_selector(arena,arena?arena+historyOffset/16:0,window,offset,command,&r.status,&r.stage,&r.child,&r.route_count,&r.k,&r.fallback,&r.token,&r.score,&r.crc);return r;}
static void descriptor(std::vector<beat>&a,const std::vector<beat>&d){for(unsigned i=0;i<d.size();++i)a[DESC/16+i]=d[i];}
static void no_result(const Result&r){check(r.token==0 && r.score==0.0f && r.crc==0,"failure/validate publishes no token");}
int main(int argc,char**argv){
    check(argc==2 || argc==3,"module path");bool rtl=argc==3;std::string m=argv[1],fixture=m+"/fixture/",lr=fixture,rt=fixture,chain=fixture;
    std::vector<beat>initial=file(fixture+"descriptor_debug.bin"),production=file(fixture+"descriptor_production.bin");
    unsigned long long off[13],size[13];for(unsigned i=0;i<13;++i){off[i]=initial[2+i].range(63,0).to_uint64();size[i]=initial[2+i].range(127,64).to_uint64();}
    historyOffset=off[2];
    std::vector<beat>a(WINDOW/16,beat(0xabcdef));descriptor(a,initial);
    load(a,off[0],std::string("D:/program/LLM_FPGA/artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin"));
    load(a,off[3],lr+"a.bf16.bin");load(a,off[4],lr+"bt.bf16.bin");
    load(a,off[5],rt+"router.centers.bin");load(a,off[6],rt+"router.norms.bin");load(a,off[7],rt+"router.ranked.bin");load(a,off[8],rt+"router.counts.bin");
    unsigned valid=0,negative=0,errors=0;
    const char*names[]={"chinese","english","code","math"};
    const unsigned order[]={0,1,0,2,3};
    for(unsigned turn=0;turn<(rtl?1:5);++turn){unsigned c=order[turn];
        std::string n=names[c];load(a,off[1],lr+n+".hidden.bin");load(a,off[2],lr+n+".history.bin");
        const bool debug=c!=3;descriptor(a,debug?initial:production);
        std::vector<beat>gold=file(chain+n+".result.bin"),preview=file(lr+n+".scores.bin"),sparse=file(chain+n+".sparse.bin"),expected=file(m+"/fixture/"+n+".expected.bin");
        Result r=run(a.data());union{float f;unsigned u;}bits;bits.f=r.score;
        check(r.status==0 && r.stage==SEL_DONE && r.child==0 && r.token==gold[0].range(31,0) && bits.u==gold[0].range(63,32) && r.crc==gold[0].range(95,64),"final dense token/score/CRC");
        check(r.fallback==0,"real no fallback");unsigned k=r.k.to_uint();std::ifstream ids((m+"/fixture/"+n+".expected.bin").c_str(),std::ios::binary|std::ios::ate);check(k==unsigned(ids.tellg())/4,"union count");
        for(unsigned word=0;word<37984;++word)check(a[off[9]/16+word]==preview[word],"full preview exact");
        for(unsigned row=0;row<k;++row){
            check(a[off[11]/16+1+row/4].range(32*(row%4)+31,32*(row%4))==expected[row/4].range(32*(row%4)+31,32*(row%4)),"all candidate IDs");
            if(debug)check(a[off[12]/16+row/2].range(64*(row%2)+63,64*(row%2))==sparse[row/2].range(64*(row%2)+63,64*(row%2)),"all raw sparse logits");
        }
        for(unsigned i=0;i<13;++i)check(a[(off[i]+size[i])/16]==0xabcdef,"buffer end guard");
        std::printf("SELECTOR_REAL_PASS %s K=%u token=%u score_bits=0x%08x production=%u\n",names[c],k,r.token.to_uint(),bits.u,debug?0:1);std::fflush(stdout);++valid;
    }
    // One RTL preflight error after the production-sized valid call proves
    // overlap rejection without poisoning/publishing the preceding result.
    descriptor(a,initial);a[DESC/16+2+10].range(63,0)=off[11];beat oldr=a[off[10]/16],oldm=a[off[11]/16];
    Result overlap=run(a.data());check(overlap.status==SEL_OVERLAP && overlap.stage==SEL_PREFLIGHT && a[off[10]/16]==oldr && a[off[11]/16]==oldm,"overlap no scratch writes");no_result(overlap);++negative;
    if(!rtl){
        for(unsigned which=0;which<23;++which){
            descriptor(a,initial);unsigned command=SEL_RUN;unsigned long long window=WINDOW,desc=DESC;unsigned expected=SEL_BAD_DESCRIPTOR;
            beat&h=a[DESC/16];beat&cfg=a[DESC/16+1];
            if(which==0)h.range(31,0)=0;if(which==1)h.range(47,32)=3;if(which==2)h.range(63,48)=12;if(which==3)h.range(95,64)=224;if(which==4)h.range(127,96)=1;
            if(which==5){cfg.range(31,0)=8;expected=SEL_BAD_CONFIG;}if(which==6){cfg.range(95,64)=16383;expected=SEL_BAD_CONFIG;}
            if(which==7){cfg.range(127,96)=1;expected=SEL_BAD_CONFIG;}if(which==8){cfg.range(63,32)=0x3f000000;expected=SEL_BAD_CONFIG;}
            if(which==9){cfg.range(63,32)=0x7fc00000;expected=SEL_BAD_CONFIG;}
            if(which==10){a[DESC/16+2].range(63,0)=off[0]+1;expected=SEL_BAD_REGION;}
            if(which==11){a[DESC/16+2].range(127,64)=size[0]-16;expected=SEL_BAD_REGION;}
            if(which==12){a[DESC/16+2].range(63,0)=0xfffffffffffffff0ull;expected=SEL_BAD_REGION;}
            if(which==13){a[DESC/16+2].range(127,64)=0xfffffffffffffff0ull;expected=SEL_BAD_REGION;}
            if(which==14){a[DESC/16+2+2].range(63,0)=DESC;expected=SEL_OVERLAP;}
            if(which==15){cfg.range(31,0)=6;expected=SEL_BAD_REGION;}
            if(which==16){a[DESC/16+2+12].range(127,64)=0;expected=SEL_BAD_REGION;}
            if(which==17)desc=DESC+1;if(which==18)desc=0xfffffffffffffff0ull;
            if(which==19)window=WINDOW+16;if(which==20)window=WINDOW-1;if(which==21)window=0;
            if(which==22){command=2;expected=SEL_BAD_CONFIG;}
            Result r=run(a.data(),window,desc,command);check(r.status==expected && r.stage==SEL_PREFLIGHT && r.child==0,"descriptor/capacity/overflow/config rejection");no_result(r);check(a[off[10]/16]==oldr && a[off[11]/16]==oldm,"preflight preserves old scratch");++negative;
        }
        descriptor(a,production);Result v=run(a.data(),WINDOW,DESC,SEL_VALIDATE_ONLY);check(v.status==0 && v.stage==SEL_PREFLIGHT,"validate production");no_result(v);++valid;
        descriptor(a,initial);a[DESC/16+2+1].range(63,0)=off[0]+size[0];v=run(a.data(),WINDOW,DESC,SEL_VALIDATE_ONLY);check(v.status==0,"adjacent intervals legal");++valid;
        // Router metadata failure must not reach lowrank, Top-K or exact.
        descriptor(a,initial);beat norm=a[off[6]/16];a[off[6]/16].range(31,0)=0x7fc00000;
        Result r=run(a.data());check(r.status==SEL_CHILD_FAILED && r.stage==SEL_ROUTE_STAGE && r.child==3 && a[off[11]/16]==0,"router failure gate");no_result(r);a[off[6]/16]=norm;++errors;
        // B/late-A numeric failures leave the final candidate header invalid.
        beat b=a[off[4]/16];a[off[4]/16].range(15,0)=0x7fc0;
        r=run(a.data());check(r.status==SEL_CHILD_FAILED && r.stage==SEL_LOWRANK_STAGE && r.child==2 && a[off[11]/16]==0,"B failure gates Top-K");no_result(r);a[off[4]/16]=b;++errors;
        unsigned long long last=(off[3]+size[3])/16-1;beat aa=a[last];a[last].range(127,112)=0x7fc0;
        r=run(a.data());check(r.status==SEL_CHILD_FAILED && r.stage==SEL_LOWRANK_STAGE && r.child==2 && a[off[11]/16]==0,"partial preview failure gates Top-K");no_result(r);a[last]=aa;++errors;
        std::vector<beat>gold=file(chain+"math.result.bin");unsigned poison=gold[0].range(31,0).to_uint();last=off[0]/16+112ull*poison;beat w=a[last];a[last].range(15,0)=0x7fc0;
        r=run(a.data());check(r.status==SEL_CHILD_FAILED && r.stage==SEL_EXACT_STAGE && r.child==3,"exact failure gates final publish");no_result(r);a[last]=w;++errors;
        beat lengths[32];for(unsigned i=0;i<32;++i){lengths[i]=a[off[8]/16+i];a[off[8]/16+i]=0;}
        a[DESC/16+1].range(31,0)=3;r=run(a.data());check(r.status==SEL_FALLBACK_FORBIDDEN && r.stage==SEL_ROUTE_STAGE && r.fallback==1 && r.k==0 && a[off[11]/16]==0,"explicit fallback policy");no_result(r);++errors;
        for(unsigned i=0;i<32;++i)a[off[8]/16+i]=lengths[i];
    }
    std::printf("M14_V4_SELECTOR_CSIM=PASS valid=%u preflight_invalid=%u stage_errors=%u rtl_subset=%u\n",valid,negative,errors,rtl?1:0);return 0;
}
