#include "lm_head_v4_router.hpp"
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>
#include <vector>
typedef ap_uint<128> beat;
static void check(bool ok,const char*msg){if(!ok){std::fprintf(stderr,"ROUTER_FAIL %s\n",msg);std::exit(1);}}
static std::vector<beat> file(const std::string& path){
    std::ifstream f(path.c_str(),std::ios::binary|std::ios::ate);check(bool(f),path.c_str());unsigned bytes=f.tellg();check(bytes%4==0,"length");
    std::vector<unsigned>w(bytes/4);f.seekg(0);f.read(reinterpret_cast<char*>(w.data()),bytes);check(bool(f),"read");
    std::vector<beat>out((w.size()+3)/4,beat(0));for(unsigned i=0;i<w.size();++i)out[i/4].range(32*(i%4)+31,32*(i%4))=w[i];return out;
}
struct Result{ap_uint<32>status,count,fallback,matrix_reads,list_reads,writes;beat routes;};
static Result run(const beat*h,const beat*c,const beat*n,const beat*ids,const beat*counts,beat*out,
                  unsigned hc=112,unsigned cc=14336,unsigned nc=32,unsigned ic=524288,unsigned lc=32,unsigned oc=37985){
    Result r;lm_head_v4_router(h,c,n,ids,counts,out,hc,cc,nc,ic,lc,oc,&r.status,&r.routes,&r.count,&r.fallback,&r.matrix_reads,&r.list_reads,&r.writes);return r;
}
static void match(const std::vector<beat>& out,const std::vector<beat>& gold,unsigned count){
    for(unsigned i=0;i<count;++i)check(out[1+i/4].range(32*(i%4)+31,32*(i%4))==gold[1+i/4].range(32*(i%4)+31,32*(i%4)),"every global candidate ID");
    check(out[0]==gold[0],"M4ID header");check(out[1+(count+3)/4]==0xabcdef,"write bound");
}
int main(int argc,char**argv){
    check(argc==2 || argc==3,"fixture argument");bool rtl=argc==3;std::string root=argv[1];
    std::vector<beat> c=file(root+"/router.centers.bin"),n=file(root+"/router.norms.bin"),ids=file(root+"/router.ranked.bin"),counts=file(root+"/router.counts.bin");
    const char* names[]={"chinese","english","code","math"};unsigned exact=0,invalid=0,numeric=0;
    for(unsigned row=0;row<(rtl?1:4);++row){
        std::string s=names[row];std::vector<beat>h=file(root+"/"+s+".hidden.bin"),gold=file(root+"/"+s+".table.bin"),routes=file(root+"/"+s+".routes.bin"),out(37986,beat(0xabcdef));
        Result r=run(h.data(),c.data(),n.data(),ids.data(),counts.data(),out.data());
        check(r.status==LMH4_ROUTE_OK && r.routes==routes[0] && r.fallback==0 && r.matrix_reads==14336,"real routing and matrix reads");
        unsigned k=gold[0].range(95,64).to_uint();check(r.count==k && r.writes==1+(k+3)/4,"real counts");match(out,gold,k);
        std::printf("ROUTER_EXACT_PASS %s K=%u\n",names[row],k);std::fflush(stdout);++exact;
    }
    // All equal distances must choose smaller cluster IDs; ranked lists need
    // not be sorted, duplicate IDs across lists must merge, specials mandatory.
    std::vector<beat>h(112,beat(0)),zeros(14336,beat(0)),norm(32,beat(0)),lists(524288,beat(0)),lengths(32,beat(0)),out(37986,beat(0xabcdef));
    for(unsigned i=0;i<128;++i)lengths[i/4].range(32*(i%4)+31,32*(i%4))=1;
    for(unsigned i=0;i<4;++i)lists[i*4096].range(31,0)=4-i;
    Result tie=run(h.data(),zeros.data(),norm.data(),lists.data(),lengths.data(),out.data());
    check(tie.status==LMH4_ROUTE_OK && tie.count==18 && tie.fallback==0,"stable ties and specials");
    for(unsigned i=0;i<4;++i){check(tie.routes.range(32*i+31,32*i)==i,"cluster ID tie");check(out[1+i/4].range(32*(i%4)+31,32*(i%4))==i+1,"sorted candidates");}++exact;
    lengths[0].range(31,0)=0;out.assign(37986,beat(0xabcdef));
    Result full=run(h.data(),zeros.data(),norm.data(),lists.data(),lengths.data(),out.data());
    check(full.status==LMH4_ROUTE_OK && full.count==151936 && full.fallback==1 && full.list_reads==32,"explicit empty cluster full PL-DDR fallback");
    for(unsigned i=0;i<151936;++i)check(out[1+i/4].range(32*(i%4)+31,32*(i%4))==i,"all fallback IDs");check(out[37985]==0xabcdef,"fallback guard");++exact;
    lengths[0].range(31,0)=1;
    if(!rtl)for(unsigned kind=0;kind<6;++kind){
        unsigned cap[]={112,14336,32,524288,32,37985};cap[kind]=0;out.assign(37986,beat(0xabcdef));
        Result r=run(0,0,0,0,0,out.data(),cap[0],cap[1],cap[2],cap[3],cap[4],cap[5]);
        check(r.status==LMH4_ROUTE_BAD_CONFIG && r.matrix_reads==0 && r.list_reads==0 && r.writes==0 && out[0]==0xabcdef,"config preflight");++invalid;
    }
    if(!rtl)for(unsigned kind=0;kind<4;++kind){
        std::vector<beat>bad_lists=lists,bad_lengths=lengths,bad_norm=norm;out.assign(37986,beat(0xabcdef));unsigned oc=37985;
        if(kind==0)bad_lengths[0].range(31,0)=16385;if(kind==1)bad_norm[0].range(31,0)=0x7fc00000;
        if(kind==2)bad_lists[0].range(31,0)=151936;if(kind==3)oc=1;
        Result r=run(h.data(),zeros.data(),bad_norm.data(),bad_lists.data(),bad_lengths.data(),out.data(),112,14336,32,524288,32,oc);
        check(r.status==(kind==3?LMH4_ROUTE_BAD_CONFIG:LMH4_ROUTE_BAD_TABLE) && r.writes==0 && out[0]==0xabcdef,"malformed model metadata/list/output capacity");++invalid;
    }
    if(!rtl)for(unsigned kind=0;kind<2;++kind){
        std::vector<beat>bad_h=h,bad_c=zeros;out.assign(37986,beat(0xabcdef));
        if(kind==0)bad_h[111].range(127,112)=0x7fc0;else bad_c.back().range(127,112)=0x7fc0;
        Result r=run(bad_h.data(),bad_c.data(),norm.data(),lists.data(),lengths.data(),out.data());check(r.status==LMH4_ROUTE_NUMERIC && r.writes==0,"nonfinite hidden/centers");++numeric;
    }
    std::printf("M14_V4_ROUTER_CSIM=PASS exact=%u invalid=%u numeric=%u rtl_subset=%u\n",exact,invalid,numeric,rtl?1:0);return 0;
}
