#include "lm_head_v4_lowrank.hpp"
#include "lm_head_v4_router.hpp"
#include "lm_head_v4_topk.hpp"
#include "lm_head_v4_candidate.hpp"
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>
#include <vector>
typedef ap_uint<128> beat;
static void check(bool b,const char*m){if(!b){std::fprintf(stderr,"CHAIN_FAIL %s\n",m);std::exit(1);}}
static std::vector<beat> file(const std::string&p){std::ifstream f(p.c_str(),std::ios::binary|std::ios::ate);check(bool(f),p.c_str());unsigned bytes=f.tellg();std::vector<unsigned>w(bytes/4);f.seekg(0);f.read(reinterpret_cast<char*>(w.data()),bytes);check(bool(f),"read");std::vector<beat>out((w.size()+3)/4,beat(0));for(unsigned i=0;i<w.size();++i)out[i/4].range(32*(i%4)+31,32*(i%4))=w[i];return out;}
int main(int argc,char**argv){
    check(argc==3,"module and canonical weight");std::string m=argv[1],lr=m+"/reports/lowrank_fixture_20261021/",rt=m+"/reports/router_fixture_20261021/",tk=m+"/reports/topk_fixture_20261021/",chain=m+"/reports/selector_chain_fixture_20261021/";
    std::vector<beat>w=file(argv[2]),a=file(lr+"a.bf16.bin"),b=file(lr+"bt.bf16.bin"),centers=file(rt+"router.centers.bin"),norms=file(rt+"router.norms.bin"),ranked=file(rt+"router.ranked.bin"),counts=file(rt+"router.counts.bin");
    const char*names[]={"chinese","english","code","math"};
    for(unsigned test=0;test<4;++test){
        std::string n=names[test];std::vector<beat>h=file(lr+n+".hidden.bin"),history=file(lr+n+".history.bin"),expected=file(tk+n+".expected.bin"),gold=file(chain+n+".result.bin"),sparse=file(chain+n+".sparse.bin"),preview_gold=file(lr+n+".scores.bin");
        std::vector<beat>route(37986,beat(0xabcdef)),preview(37985,beat(0xabcdef)),candidates(37986,beat(0xabcdef)),scores(75969,beat(0xabcdef));
        ap_uint<32>status,rk,fallback,matrix_reads,list_reads,write_count;beat selected;
        lm_head_v4_router(h.data(),centers.data(),norms.data(),ranked.data(),counts.data(),route.data(),112,14336,32,524288,32,37985,&status,&selected,&rk,&fallback,&matrix_reads,&list_reads,&write_count);
        check(status==0 && fallback==0,"router status before next stage");
        ap_uint<64>factor_reads;
        lm_head_v4_lowrank(h.data(),b.data(),a.data(),history.data(),preview.data(),151936,112,14336,2430976,1187,37984,1,1.1f,&status,&factor_reads,&write_count);
        check(status==0 && factor_reads==2445312 && write_count==37984,"lowrank status before next stage");
        for(unsigned word=0;word<37984;++word)check(preview[word]==preview_gold[word],"every full-vocabulary policy preview bit");
        ap_uint<32>k,route_reads;ap_uint<64>score_reads;
        lm_head_v4_topk_union(preview.data(),route.data(),candidates.data(),37984,37985,37985,16384,&status,&k,&score_reads,&route_reads,&write_count);
        check(status==0 && k>0,"topK status before exact head");
        unsigned count=k.to_uint();std::ifstream expected_file((tk+n+".expected.bin").c_str(),std::ios::binary|std::ios::ate);
        check(bool(expected_file) && count==unsigned(expected_file.tellg())/4,"complete union count");
        for(unsigned i=0;i<count;++i)check(candidates[1+i/4].range(32*(i%4)+31,32*(i%4))==expected[i/4].range(32*(i%4)+31,32*(i%4)),"complete candidate table");
        ap_uint<32>token,processed,history_reads,score_writes,crc;ap_uint<64>index_reads,weight_reads;float score;
        lm_head_v4_candidate(h.data(),w.data(),history.data(),candidates.data(),scores.data(),37985,75968,1,1,1.1f,&status,&token,&score,&processed,&index_reads,&weight_reads,&history_reads,&score_writes,&crc);
        union{float f;unsigned u;}bits;bits.f=score;
        check(status==0 && processed==k && token==gold[0].range(31,0) && bits.u==gold[0].range(63,32) && crc==gold[0].range(95,64),"dense trace token/score/CRC");
        check(weight_reads==112ull*count && index_reads==1+2*((count+3)/4) && score_writes==(count+1)/2,"exact counters");
        for(unsigned i=0;i<count;++i)check(scores[i/2].range(64*(i%2)+63,64*(i%2))==sparse[i/2].range(64*(i%2)+63,64*(i%2)),"all candidate raw logit records bit exact");
        check(route[37985]==0xabcdef && preview[37984]==0xabcdef && candidates[37985]==0xabcdef && scores[75968]==0xabcdef,"scratch capacity guards");
        std::printf("CHAIN_EXACT_PASS %s K=%u token=%u score_bits=0x%08x crc=0x%08x\n",names[test],count,token.to_uint(),bits.u,crc.to_uint());std::fflush(stdout);
    }
    std::puts("M14_V4_SELECTOR_CHAIN_CSIM=PASS cases4 full_sparse_logits_and_dense_outputs");return 0;
}
