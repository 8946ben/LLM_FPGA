if {$argc != 1} {
    error "Usage: vivado -mode batch -source verify_m14_v2_ip.tcl -tclargs <ip_repository>"
}

set ip_repository [file normalize [lindex $argv 0]]
if {![file exists [file join $ip_repository component.xml]]} {
    error "component.xml was not found in $ip_repository"
}

create_project -in_memory -part xczu9eg-ffvb1156-2-i
set_property ip_repo_paths $ip_repository [current_project]
update_ip_catalog

set matches [get_ipdefs -all -filter {NAME == lm_head_v2}]
if {[llength $matches] != 1} {
    error "Expected exactly one lm_head_v2 IP definition, found [llength $matches]: $matches"
}

set ipdef [lindex $matches 0]
puts "M14_V2_IP_VERIFY=PASS"
puts "M14_V2_IP_VLNV=[get_property VLNV $ipdef]"
puts "M14_V2_IP_NAME=[get_property NAME $ipdef]"
puts "M14_V2_IP_VERSION=[get_property VERSION $ipdef]"
puts "M14_V2_IP_REPOSITORY=$ip_repository"
close_project
