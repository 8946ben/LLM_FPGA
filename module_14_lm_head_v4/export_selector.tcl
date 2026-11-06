# Package an existing private synthesis; never program/connect hardware.
set module [file dirname [file normalize [info script]]]
set run selector_csynth_r2
if {[info exists ::env(LMH4_SELECTOR_EXPORT_RUN)]} {set run $::env(LMH4_SELECTOR_EXPORT_RUN)}
if {![regexp {^[a-zA-Z0-9_-]+$} $run]} {error "bad run"}
set project [file join $module build $run hls]
if {![file exists [file join $project solution1 syn report lm_head_v4_selector_csynth.xml]]} {error "Synthesis not complete"}
cd [file dirname $project]
open_project hls
open_solution solution1
export_design -format ip_catalog -vendor user.org -library hls -version 4.0
puts "M14_V4_SELECTOR_PRIVATE_EXPORT=PASS"
exit
