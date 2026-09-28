proc stage_d_fail {message options_dict} {
    puts stderr "STAGE_D_ERROR: $message"
    if {[dict exists $options_dict -errorinfo]} {
        puts stderr [dict get $options_dict -errorinfo]
    }
    exit 1
}

set workspace_dir "D:/program/LLM_FPGA/realFpga/vitis/workspace"
set platform_name "lm_head_axu9eg_platform"
set domain_name "standalone_domain"
set app_name "lm_head_net_diag"

puts "STAGE_D_NET_APP_CREATE_BEGIN"
if {[catch {
    setws $workspace_dir
    platform active $platform_name
    domain active $domain_name

    puts "BSP_ADD_LWIP_BEGIN"
    bsp setlib -name lwip211
    bsp write
    bsp regenerate
    platform write
    platform generate -domains $domain_name
    puts "BSP_ADD_LWIP_END"

    puts "APPLICATION_TEMPLATES_BEGIN"
    puts [repo -apps]
    puts "APPLICATION_TEMPLATES_END"

    app create \
        -name $app_name \
        -platform $platform_name \
        -domain $domain_name \
        -template "lwIP Echo Server"

    puts "APP_LIST=[app list]"
    puts "BSP_LIBRARIES_BEGIN"
    puts [bsp getlibs]
    puts "BSP_LIBRARIES_END"
} message options_dict]} {
    stage_d_fail $message $options_dict
}
puts "STAGE_D_NET_APP_CREATE_PASS"
exit 0
