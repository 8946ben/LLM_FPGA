set module_dir [file normalize [file dirname [info script]]]
set repo_dir [file normalize [file join $module_dir ".."]]
set weight_path [file normalize [file join $repo_dir "artifacts" "model.embed_tokens.weight.fp16.npy"]]
set fixture_root [file normalize [file join $repo_dir "artifacts" "module16_hls_fixtures"]]

set step_index "all"
foreach argument $argv {
    if {[string is integer -strict $argument]} {
        set step_index $argument
    }
}

set build_dir [file join $module_dir "build"]
file mkdir $build_dir
cd $build_dir
open_project -reset lm_head_csim
set_top lm_head_argmax
add_files [file join $module_dir "src" "lm_head_kernel.cpp"] -cflags "-I[file join $module_dir include]"
add_files -tb [file join $module_dir "tb" "lm_head_tb.cpp"] -cflags "-I[file join $module_dir include]"
open_solution -reset solution1
set_part {xcu280-fsvh2892-2L-e}
create_clock -period 4 -name default

if {$step_index eq "all"} {
    set csim_args [format {--trace-all %s %s} $weight_path $fixture_root]
} else {
    set step_name [format "step_%02d" $step_index]
    set fixture_dir [file join $fixture_root $step_name]
    set expected_file [file join $fixture_dir "expected_token.txt"]
    set expected_handle [open $expected_file r]
    set expected_token [string trim [read $expected_handle]]
    close $expected_handle
    set csim_args [format {--trace %s %s %s %s %s} \
        $weight_path \
        [file join $fixture_dir "hidden.fp16.bin"] \
        [file join $fixture_dir "golden_logits.fp16.bin"] \
        [file join $fixture_dir "history_bitmap.u32.bin"] \
        $expected_token]
}
csim_design -clean -argv $csim_args
exit
