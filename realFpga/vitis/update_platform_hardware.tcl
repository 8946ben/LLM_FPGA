proc update_platform_fail {message options_dict} {
    puts stderr "H4_PLATFORM_UPDATE_ERROR: $message"
    if {[dict exists $options_dict -errorinfo]} {
        puts stderr [dict get $options_dict -errorinfo]
    }
    exit 1
}

set workspace_dir "D:/program/LLM_FPGA/realFpga/vitis/workspace"
set xsa_file "D:/program/LLM_FPGA/realFpga/results/20260724_stage_c/lm_head_axu9eg.xsa"
set platform_name "lm_head_axu9eg_platform"
set domain_name "standalone_domain"

puts "H4_PLATFORM_UPDATE_BEGIN"
if {[catch {
    if {![file exists $xsa_file]} {
        error "New hardware handoff is missing: $xsa_file"
    }

    setws $workspace_dir
    platform active $platform_name
    puts "H4_PLATFORM_XSA=$xsa_file"
    platform config -updatehw $xsa_file
    platform write
    domain active $domain_name
    platform generate -domains $domain_name

    puts "H4_PLATFORM_REPORT_BEGIN"
    puts [platform report]
    puts "H4_PLATFORM_REPORT_END"
} message options_dict]} {
    update_platform_fail $message $options_dict
}
puts "H4_PLATFORM_UPDATE_PASS"
exit 0
