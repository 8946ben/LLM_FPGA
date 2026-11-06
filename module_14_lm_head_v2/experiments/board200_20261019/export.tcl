# Export only the existing production-sized candidate synthesis, no reset.
set here [file normalize [file dirname [info script]]]
set module_dir [file normalize [file join $here .. ..]]
set project [file join $module_dir build board200_20261019 hls]
if {![file exists [file join $project solution1 syn report lm_head_v2_csynth.xml]]} {
    error "Candidate synthesis report missing"
}
if {[file exists [file join $project solution1 impl ip component.xml]]} {
    error "Preserve existing candidate IP export"
}
cd [file dirname $project]
open_project [file tail $project]
open_solution solution1
config_export -format ip_catalog -rtl verilog -vendor user.org -library llm_fpga -version 2.1
export_design -format ip_catalog -rtl verilog
puts "M14_BOARD200_EXPORT=PASS"
exit
