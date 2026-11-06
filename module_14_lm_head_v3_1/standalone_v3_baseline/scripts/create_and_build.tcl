proc fail {message options_dict} {
    puts stderr "M14_V2_STANDALONE_ERROR: $message"
    if {[dict exists $options_dict -errorinfo]} {
        puts stderr [dict get $options_dict -errorinfo]
    }
    exit 1
}

set script_dir [file dirname [file normalize [info script]]]
set standalone_dir [file dirname $script_dir]
set module_dir [file dirname $standalone_dir]
set workspace_dir [file join $standalone_dir workspace]
set xsa_file [file join $module_dir reports board_build m14_v2_single.xsa]
set platform_name m14_v2_platform
set domain_name standalone_domain

if {[catch {
    if {![file exists $xsa_file]} {
        error "XSA is missing: $xsa_file"
    }
    file mkdir $workspace_dir
    setws $workspace_dir

    if {![file isdirectory [file join $workspace_dir $platform_name]]} {
        platform create -name $platform_name -hw $xsa_file \
            -proc psu_cortexa53_0 -os standalone
    }
    platform active $platform_name
    platform write
    platform generate

    puts "M14_V2_STANDALONE_PLATFORM=PASS"
} message options_dict]} {
    fail $message $options_dict
}
exit 0
