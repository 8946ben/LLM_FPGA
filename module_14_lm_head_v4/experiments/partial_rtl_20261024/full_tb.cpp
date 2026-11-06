// Reuse reviewed complete-array postchecks, with one full nonzero transaction.
// Three repeated full-weight C transaction dumps are deliberately avoided.
#define main archived_csim_main
#include "../partial_hw_20261024/proto_tb.cpp"
#undef main
int main(int argc,char** argv) {
    require(argc==2,"fixture root");std::string root=argv[1];
    std::ifstream paths((root+"/weight_paths.txt").c_str());std::string tiled_path,row_path;
    std::getline(paths,tiled_path);std::getline(paths,row_path);
    std::vector<Beat> tiled=load_beats(tiled_path),canonical=load_beats(row_path);
    run_case(root,"old_chinese","RTL_full_chinese",tiled,canonical,1);
    std::printf("PARTIAL_FULL_RTL_REFERENCE_PASS calls=1 full_arrays=1\n");return 0;
}
