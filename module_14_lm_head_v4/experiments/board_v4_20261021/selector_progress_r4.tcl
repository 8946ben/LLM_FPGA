# Simulator control only. Same compiled DUT, testbench, inputs and golden traces.
set selector_complete 0
for {set selector_window 1} {$selector_window <= 10000} {incr selector_window} {
    run 100 us
    puts "SELECTOR_SIM_WINDOW_FINISHED=$selector_window requested_through_us=[expr {$selector_window*100}] wall=[clock format [clock seconds] -format {%Y-%m-%dT%H:%M:%S}]"
    flush stdout
    # A result report alone is insufficient: require all final runtime trailers.
    set selector_report ../report/verilog/result.transaction.rpt
    set selector_complete [file exists $selector_report]
    foreach selector_name {plmem status stage child_status route_count candidate_count dense_fallback token score output_crc} {
        set selector_file ../tv/rtldatafile/rtl.lm_head_v4_selector.autotvout_${selector_name}.dat
        if {!$selector_complete || ![file exists $selector_file] || [file size $selector_file] < 32} {
            set selector_complete 0
            break
        }
        set selector_fd [open $selector_file rb]
        seek $selector_fd -32 end
        set selector_tail [read $selector_fd]
        close $selector_fd
        if {[string first {[[[/runtime]]]} $selector_tail] < 0} {
            set selector_complete 0
            break
        }
    }
    if {$selector_complete} {break}
}
if {!$selector_complete} {error "Selector simulation exceeded 10000 windows without complete RTL traces"}
puts "SELECTOR_SIM_OUTPUTS_COMPLETE_PENDING_STRICT_COMPARE"
flush stdout
quit
