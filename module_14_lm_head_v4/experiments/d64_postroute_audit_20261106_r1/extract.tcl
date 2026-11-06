set_param general.maxThreads 2
set here [file dirname [file normalize [info script]]]
set module [file normalize [file join $here .. ..]]
set out [file join $module reports d64_postroute_audit_20261106_r1 netlist]
file mkdir $out
open_checkpoint [file join $module reports d64_system_200m_20261106_r4 hardware post_route.dcp]
set f [open [file join $out dsp_cones.tsv] w]
array set seen {}
proc emit_net {net} {
 global f seen
 if {[info exists seen($net)]} {return}
 set seen($net) 1
 set drivers [get_pins -quiet -leaf -of_objects [get_nets $net] -filter {DIRECTION == OUT}]
 if {[llength $drivers] != 1} {puts $f "LEAF\t$net\t[llength $drivers]";return}
 set pin [lindex $drivers 0]
 set c [get_cells -of_objects $pin]
 set ref [get_property REF_NAME $c]
 set init "-"
 set inputs {}
 if {[string match LUT* $ref] || $ref eq "INV"} {
  if {[string match LUT* $ref]} {set init [get_property INIT $c]}
  foreach p [lsort [get_pins -of_objects $c -filter {DIRECTION == IN}]] {
   set n [get_nets -of_objects $p]
   lappend inputs "[get_property REF_PIN_NAME $p]=$n"
   emit_net $n
  }
 }
 puts $f "NODE\t$net\t$ref\t$c\t$init\t[join $inputs ,]"
}
foreach c [lsort [get_cells -hier -filter {REF_NAME == DSP48E2}]] {
 puts $f "DSP\t$c\t[get_property PREG $c]\t[get_property OPMODEREG $c]\t[get_property IS_OPMODE_INVERTED $c]"
 for {set i 0} {$i < 9} {incr i} {
  set p [get_pins [format {%s/OPMODE[%d]} $c $i]]
  set n [get_nets -of_objects $p]
  puts $f "BIT\t$c\t$i\t$n"
  emit_net $n
 }
}
close $f
set f [open [file join $out io.tsv] w]
foreach p [lsort [get_ports]] {puts $f "$p\t[get_property PACKAGE_PIN $p]\t[get_property IOSTANDARD $p]\t[get_property DRIVE $p]\t[get_property SLEW $p]"}
close $f
set f [open [file join $out reset_fanin.txt] w]
foreach p [all_fanin -flat -startpoints_only -to [get_ports c0_ddr4_reset_n_0]] {puts $f $p}
close $f
report_exceptions -file [file join $out exceptions.rpt]
puts "D64_POSTROUTE_NETLIST_AUDIT_EXTRACTED=PASS"
close_design
exit
