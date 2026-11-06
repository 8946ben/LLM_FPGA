# Export the v3.1 kernel as IP version 2.2 (distinct from v3's 2.1).
set here [file normalize [file dirname [info script]]]
set module_dir [file normalize [file join $here .. ..]]
set project [file join $module_dir build board_v31_20261019 hls]
if {![file exists [file join $project solution1 syn report lm_head_v2_csynth.xml]]} {
    error "v3.1 synthesis report missing"
}
if {[file exists [file join $project solution1 impl ip component.xml]]} {
    error "Preserve existing v3.1 IP export"
}
cd [file dirname $project]
open_project [file tail $project]
open_solution solution1
config_export -format ip_catalog -rtl verilog -vendor user.org -library llm_fpga -version 2.2
export_design -format ip_catalog -rtl verilog
puts "M14_V31_EXPORT=PASS"
exit
