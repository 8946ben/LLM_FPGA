# Run after packaging stage, before seal; never connects to a board.
if {$argc != 1} {error "usage: verify_delivery_ip.tcl delivery_root"}
set root [file normalize [lindex $argv 0]]
create_project -in_memory m14_v31_delivery_catalog -part xczu9eg-ffvb1156-2-i
set_property ip_repo_paths [list [file join $root module_14_lm_head_v3_1 ip_repo lm_head_v2]] [current_project]
update_ip_catalog
set defs [get_ipdefs -all -filter {VLNV == "user.org:llm_fpga:lm_head_v2:2.2"}]
if {[llength $defs] != 1} {error "Expected unique v3.1 IP2.2"}
create_ip -vlnv user.org:llm_fpga:lm_head_v2:2.2 -module_name m14_v31_delivery_ip
puts "M14_V31_DELIVERY_IP_VLNV=[get_property VLNV [lindex $defs 0]]"
puts "M14_V31_DELIVERY_IP_CATALOG=PASS"
close_project
exit
