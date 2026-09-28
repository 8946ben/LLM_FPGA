proc stage_d_fail {message options_dict} {
    puts stderr "STAGE_D_ERROR: $message"
    if {[dict exists $options_dict -errorinfo]} {
        puts stderr [dict get $options_dict -errorinfo]
    }
    exit 1
}

set workspace_dir "D:/program/LLM_FPGA/realFpga/vitis/workspace"
set xsa_file "D:/program/LLM_FPGA/realFpga/results/20260724_stage_c/lm_head_axu9eg.xsa"
set platform_name "lm_head_axu9eg_platform"

puts "STAGE_D_PLATFORM_BEGIN"
if {[catch {
    setws $workspace_dir
    puts "WORKSPACE=$workspace_dir"
    puts "XSA=$xsa_file"

    platform create \
        -name $platform_name \
        -hw $xsa_file \
        -proc psu_cortexa53_0 \
        -os standalone
    platform active $platform_name
    platform write
    platform generate

    puts "PLATFORM_LIST=[platform list]"
    puts "PLATFORM_REPORT_BEGIN"
    puts [platform report]
    puts "PLATFORM_REPORT_END"
} message options_dict]} {
    stage_d_fail $message $options_dict
}
puts "STAGE_D_PLATFORM_PASS"
exit 0
