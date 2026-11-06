# Existing-project counterpart of create_bd.tcl's single-bit GPIO/UI-reset fix.
set here [file dirname [file normalize [info script]]]
set module [file normalize [file join $here .. ..]]
set project_dir [file join $module board build m14_board_v31_20261019]
open_project [file join $project_dir m14_board_v31_20261019.xpr]
open_bd_design [get_files */m14_v31_system.bd]
set_property CONFIG.C_GPIO_WIDTH 1 [get_bd_cells calib_gpio]
set gate [get_bd_pins calib_gate/Op1]
disconnect_bd_net [get_bd_nets -of_objects $gate] $gate
connect_bd_net [get_bd_pins rst_ui_ddr/peripheral_aresetn] $gate
validate_bd_design
save_bd_design
generate_target all [get_files */m14_v31_system.bd]
reset_run impl_1
reset_run synth_1
update_compile_order -fileset sources_1
close_project
source [file join $here build.tcl]
