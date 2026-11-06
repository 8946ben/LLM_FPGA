from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/dual_board_20261030_r1';D=R/'control_r3'
assert not D.exists();D.mkdir()
s=(R/'control_r2/private_board_common.tcl').read_text()
needle='''    stop
    rst -processor
    dow $elf
'''
assert s.count(needle)==1
replacement='''    if {[catch {stop} stop_message stop_options]} {
        if {![string match {*APU L2 cache is held in reset*} $stop_message]} {
            return -options $stop_options $stop_message
        }
        puts "M4_INITIAL_STOP_ALREADY_IN_RESET=$stop_message"
    }
    rst -processor
    dow $elf
'''
(D/'private_board_common.tcl').write_text(s.replace(needle,replacement))
(D/'private_board_entry.tcl').write_bytes((R/'control_r2/private_board_entry.tcl').read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(D/'DERIVATION.json').write_text(json.dumps(dict(state='INITIAL_RESET_STOP_HANDLING_ONLY',reason='Actual r2 trace: full init and private signature/MIG/idle passed; initial A53 stop failed because L2 already held reset. Permit only this exact reset condition, then execute original rst -processor/dow/con. No change to ELF/bit/XSA/FP32/DDR layout.',derived={p.name:sha(p) for p in D.glob('*.tcl')},historical_failure_preserved=True),indent=2)+'\n')
print(D)
