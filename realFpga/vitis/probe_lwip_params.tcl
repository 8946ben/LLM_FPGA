proc stage_f_fail {message options_dict} {
    puts stderr "STAGE_F_BSP_PROBE_ERROR: $message"
    if {[dict exists $options_dict -errorinfo]} {
        puts stderr [dict get $options_dict -errorinfo]
    }
    exit 1
}

set workspace_dir "D:/program/LLM_FPGA/realFpga/vitis/workspace"
set platform_name "lm_head_axu9eg_platform"
set domain_name "standalone_domain"

puts "STAGE_F_BSP_PROBE_BEGIN"
if {[catch {
    setws $workspace_dir
    platform active $platform_name
    domain active $domain_name
    puts [bsp listparams -lib lwip211]
} message options_dict]} {
    stage_f_fail $message $options_dict
}
puts "STAGE_F_BSP_PROBE_PASS"
exit 0
