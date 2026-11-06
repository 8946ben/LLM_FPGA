#include "lm_head_v4_lowrank.hpp"
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>
#include <vector>
typedef ap_uint<128> beat;
static void check(bool b,const char*m){if(!b){std::fprintf(stderr,"LOWRANK_RTL_FAIL %s\n",m);std::exit(1);}}
static std::vector<beat> file(const std::string&p){std::ifstream f(p.c_str(),std::ios::binary|std::ios::ate);check(bool(f),"file");unsigned bytes=f.tellg();std::vector<unsigned>w(bytes/4);f.seekg(0);f.read(reinterpret_cast<char*>(w.data()),bytes);check(bool(f),"read");std::vector<beat>out((w.size()+3)/4,beat(0));for(unsigned i=0;i<w.size();++i)out[i/4].range(32*(i%4)+31,32*(i%4))=w[i];return out;}
int main(int argc,char**argv){
    check(argc==2,"fixtures");std::string root=argv[1];std::vector<beat>h=file(root+"/chinese.hidden.bin"),b=file(root+"/bt.bf16.bin"),a=file(root+"/a.bf16.bin"),hist=file(root+"/chinese.history.bin"),gold=file(root+"/chinese.scores.bin"),out(37984,beat(0xabcdef));
    ap_uint<32>status,writes;ap_uint<64>reads;
    lm_head_v4_lowrank(h.data(),b.data(),a.data(),hist.data(),out.data(),256,112,14336,2430976,1187,37984,1,1.1f,&status,&reads,&writes);
    check(status==0 && reads==14336+256*16 && writes==64,"real counts");for(unsigned i=0;i<64;++i)check(out[i]==gold[i],"real all256 preview bits");check(out[64]==0xabcdef,"real guard");std::puts("LOWRANK_RTL_REAL=PASS rows256");
    for(unsigned i=0;i<h.size();++i)h[i]=0;for(unsigned i=0;i<b.size();++i)b[i]=0;
    for(unsigned i=0;i<a.size();++i)a[i]=0;for(unsigned i=0;i<out.size();++i)out[i]=0xabcdef;
    lm_head_v4_lowrank(h.data(),b.data(),a.data(),hist.data(),out.data(),3,112,14336,2430976,1187,37984,0,1.1f,&status,&reads,&writes);
    check(status==0 && writes==1 && out[0]==0 && out[1]==0xabcdef,"repeat zero and padding");std::puts("LOWRANK_RTL_REPEAT=PASS rows3");
    h[111].range(127,112)=0x7fc0;for(unsigned i=0;i<out.size();++i)out[i]=0xabcdef;
    lm_head_v4_lowrank(h.data(),b.data(),a.data(),hist.data(),out.data(),3,112,14336,2430976,1187,37984,1,1.1f,&status,&reads,&writes);
    check(status==LMH4_LR_NUMERIC && reads==0 && writes==0 && out[0]==0xabcdef,"late hidden NaN no output");std::puts("M14_V4_LOWRANK_RTL_TESTBENCH=PASS transactions3");return 0;
}
