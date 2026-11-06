#include "partial_proto.hpp"
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>
#include <vector>
typedef ap_uint<128> Beat;
static void require(bool ok,const std::string& text) {if(!ok){std::fprintf(stderr,"CSIM_FAIL %s\n",text.c_str());std::exit(1);}}
template<class T>static std::vector<T> load(const std::string& path) {
    std::ifstream f(path.c_str(),std::ios::binary|std::ios::ate);require(bool(f),path);
    size_t n=size_t(f.tellg());require(n%sizeof(T)==0,"file shape "+path);
    std::vector<T> out(n/sizeof(T));f.seekg(0);f.read(reinterpret_cast<char*>(out.data()),n);require(bool(f),"file read "+path);return out;
}
static std::vector<Beat> load_beats(const std::string& path) {
    std::ifstream f(path.c_str(),std::ios::binary|std::ios::ate);require(bool(f),path);
    size_t n=size_t(f.tellg());require(n%16==0,"beat file shape");f.seekg(0);std::vector<Beat> out(n/16);
    unsigned long long buffer[2*4096];
    for(size_t start=0;start<out.size();start+=4096) {
        size_t count=out.size()-start;if(count>4096)count=4096;
        f.read(reinterpret_cast<char*>(buffer),count*16);require(bool(f),"beat read");
        for(size_t j=0;j<count;++j) {out[start+j].range(63,0)=buffer[j*2];out[start+j].range(127,64)=buffer[j*2+1];}
    }
    return out;
}
static unsigned get(const std::vector<Beat>& a,unsigned base,unsigned i) {return a[base+(i>>2)].range((i&3)*32+31,(i&3)*32).to_uint();}
struct Result {ap_uint<32> status,token,score,k,crc;ap_uint<64> preview;};
static Result call(const Beat* meta,const Beat* tiled,const Beat* canonical,Beat* out,unsigned capacity=P_WS_BEATS,unsigned debug=1) {
    Result r;lm_head_v4_partial_proto(meta,tiled,canonical,out,capacity,debug,&r.status,&r.token,&r.score,&r.k,&r.crc,&r.preview);return r;
}
static void run_case(const std::string& root,const std::string& name,const std::string& label,
                     const std::vector<Beat>& tiled,const std::vector<Beat>& canonical,unsigned debug) {
    std::string dir=root+"/"+name;
    std::vector<Beat> meta=load_beats(dir+".meta.bin"),out(P_WS_BEATS+1);
    for(size_t i=0;i<out.size();++i)out[i]=~Beat(0);
    std::vector<unsigned> dims=load<unsigned>(dir+".dims.bin"),preview=load<unsigned>(dir+".preview.bin"),keys=load<unsigned>(dir+".keys.bin"),ids=load<unsigned>(dir+".ids.bin"),raw=load<unsigned>(dir+".raw.bin"),expected=load<unsigned>(dir+".expected.bin");
    Result result=call(meta.data(),tiled.data(),canonical.data(),out.data(),P_WS_BEATS,debug);
    require(result.status==0,"status "+label);require(result.k==ids.size(),"K "+label);
    require(result.token==expected[0]&&result.score==expected[1]&&result.crc==expected[2],"token/score/CRC "+label);
    require(result.preview==149ull*64*128,"scheduled preview beats "+label);
    for(unsigned i=0;i<P_D;++i)require(get(out,P_DIMS,i)==dims[i],"channel order "+label);
    for(unsigned i=0;i<P_V;++i) {require(get(out,P_PREVIEW,i)==preview[i],"full preview bits "+label);require(get(out,P_KEY,i)==keys[i],"full policy key bits "+label);}
    require(get(out,P_TABLE,0)==0x4449344du && get(out,P_TABLE,2)==ids.size() && get(out,P_TABLE,3)==P_V,"table header "+label);
    for(unsigned i=0;i<ids.size();++i) {
        require(get(out,P_TABLE+1,i)==ids[i],"candidate ID "+label);
        if(debug) {require(get(out,P_SCORES,2*i)==ids[i],"raw ID "+label);require(get(out,P_SCORES,2*i+1)==raw[i],"full candidate raw bits "+label);}
    }
    if(!debug)require(out[P_SCORES]==~Beat(0),"production raw writes disabled");
    if(debug && (ids.size()&1))require(out[P_SCORES+ids.size()/2].range(127,64)==0,"raw tail padding");
    require(out[P_WS_BEATS]==~Beat(0),"workspace end guard "+label);
    std::vector<unsigned> actual;actual.push_back(result.token.to_uint());actual.push_back(result.score.to_uint());actual.push_back(result.crc.to_uint());actual.push_back(result.k.to_uint());
    for(unsigned i=0;i<P_D;++i)actual.push_back(get(out,P_DIMS,i));
    for(unsigned i=0;i<P_V;++i)actual.push_back(get(out,P_PREVIEW,i));
    for(unsigned i=0;i<P_V;++i)actual.push_back(get(out,P_KEY,i));
    for(unsigned i=0;i<ids.size();++i)actual.push_back(get(out,P_TABLE+1,i));
    if(debug)for(unsigned i=0;i<ids.size();++i)actual.push_back(get(out,P_SCORES,2*i+1));
    std::ofstream f((root+"/actual_"+label+".bin").c_str(),std::ios::binary);f.write(reinterpret_cast<const char*>(actual.data()),actual.size()*4);require(bool(f),"actual write");
    std::printf("CSIM_CASE_PASS %s debug=%u K=%u token=%u\n",label.c_str(),debug,result.k.to_uint(),result.token.to_uint());std::fflush(stdout);
}
int main(int argc,char** argv) {
    require(argc==2,"fixture root arg");std::string root=argv[1];
    std::ifstream paths((root+"/weight_paths.txt").c_str());require(bool(paths),"weight paths");
    std::string tile_path,row_path;std::getline(paths,tile_path);std::getline(paths,row_path);
    std::vector<Beat> tiled=load_beats(tile_path),canonical=load_beats(row_path);
    run_case(root,"old_chinese","A0",tiled,canonical,1);
    run_case(root,"old_english","B0",tiled,canonical,1);
    run_case(root,"old_chinese","A1",tiled,canonical,1);
    const char* others[]={"old_code","old_math","new_chinese","new_english","new_code","new_math"};
    for(unsigned i=0;i<6;++i)run_case(root,others[i],others[i],tiled,canonical,1);
    run_case(root,"zero_hidden","all_ties",tiled,canonical,1);
    run_case(root,"old_chinese","production",tiled,canonical,0);
    Result bad=call(0,0,0,0,P_WS_BEATS-1,1);require(bad.status==1&&bad.k==0&&bad.preview==0,"capacity before reads");
    bad=call(0,0,0,0,P_WS_BEATS,2);require(bad.status==1&&bad.k==0&&bad.preview==0,"flag before reads");
    std::vector<Beat> meta=load_beats(root+"/old_chinese.meta.bin");
    for(unsigned kind=0;kind<3;++kind) {
        std::vector<Beat> broken=meta;
        if(kind==0)broken[0].range(15,0)=0x7fc0u;
        if(kind==1)broken[112].range(31,0)=0x7fc00000u;
        if(kind==2)broken[112].range(31,0)=0xbf800000u;
        bad=call(broken.data(),0,0,0);require(bad.status==2&&bad.k==0&&bad.preview==0,"metadata numeric before W reads");
    }
    std::vector<unsigned> dims=load<unsigned>(root+"/old_chinese.dims.bin");
    unsigned address=dims[0]*128;Beat original=tiled[address];tiled[address].range(15,0)=0x7fc0u;
    std::vector<Beat> out(P_WS_BEATS+1);out[P_WS_BEATS]=0xabcdefu;
    bad=call(meta.data(),tiled.data(),0,out.data());tiled[address]=original;
    require(bad.status==2&&bad.k==0&&bad.preview==0&&out[P_WS_BEATS]==0xabcdefu,"nonfinite preview prevents canonical reads");
    std::printf("PARTIAL_PROTO_CSIM_ALL_PASS valid=11 unique=9 negative=6\n");return 0;
}
