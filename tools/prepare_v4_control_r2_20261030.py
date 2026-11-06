from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/dual_board_20261030_r1/control_r2'
assert not R.exists();R.mkdir()
src=M/'standalone/scripts'
s=(src/'private_board_common.tcl').read_text()
# Add trace evidence only; no reset/ELF/AXI changes at this stage.
s+='''
proc audit_board_stage {command op} {
    puts "M4_TARGET_COMMAND=$command"
    flush stdout
}
foreach command {connect targets rst fpga loadhw stop dow con lmh4_require_ready lmh4_stop_gem} {
    trace add execution $command enter audit_board_stage
}
'''
(R/'private_board_common.tcl').write_text(s)
s=(src/'private_board_entry.tcl').read_text().replace('puts stderr "M4_PRIVATE_BOARD_ERROR: $message"','puts stderr "M4_PRIVATE_BOARD_ERROR: $message"\n    puts stderr [dict get $options -errorinfo]')
(R/'private_board_entry.tcl').write_text(s)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(R/'DERIVATION.json').write_text(json.dumps(dict(state='DIAGNOSTIC_ENTRY_ONLY_NO_KERNEL_CHANGE',original={str(p.relative_to(ROOT)):sha(p) for p in src.glob('private_board*.tcl')},derived={p.name:sha(p) for p in R.glob('*.tcl')},reason='Original Windows batch exit0 did not prove successful Tcl; require action-specific success marker before advancing; trace actual commands and errorinfo'),indent=2)+'\n')
print(R)
