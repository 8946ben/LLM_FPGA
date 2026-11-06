"""Synthetic host/Tcl command orchestration only. No XSCT, socket or board."""
from pathlib import Path
import json, subprocess, sys, tempfile, tkinter, unittest
from unittest.mock import patch
M=Path(__file__).resolve().parents[1];sys.path.insert(0,str(M/'standalone'))
import private_board as b

class TclTests(unittest.TestCase):
    def setUp(self):
        self.t=tkinter.Tcl()
        self.t.eval('''
set ::events {}
array set ::regs {0xa0020008 0x4d345301 0xa0020000 1 0xa0000000 4 0xff0e0000 12 0xff0e0014 0}
set ::fail_clear 0
proc mrd {args} {
    if {[lsearch -exact $args -bin] >= 0} {
        set i [lsearch -exact $args -file];set p [lindex $args [expr {$i+1}]]
        set f [open $p wb];puts -nonewline $f [string repeat x [expr {4*[lindex $args end]}]];close $f
        return
    }
    set a [format 0x%x [lindex $args end-1]]
    if {![info exists ::regs($a)]} {error "Unexpected MMIO read $a"}
    return [expr {$::regs($a)}]
}
proc mwr {args} {
    set a [format 0x%x [lindex $args end-1]];set v [lindex $args end]
    lappend ::events [list write $a $v]
    if {$::fail_clear && $a eq "0xff0e0000"} {return}
    set ::regs($a) $v
}
foreach name {connect disconnect stop con targets rst loadhw dow fpga} {
    proc $name {args} [format {lappend ::events [linsert $args 0 %s]} $name]
}
proc after {args} {}
''')
        self.t.call('source',str(M/'standalone/scripts/private_board_common.tcl'))

    def test_source_has_no_side_effects(self):self.assertEqual(self.t.eval('llength $::events'),'0')
    def test_u32(self):
        for x in ('0xffffffff','4294967295'):self.assertEqual(int(self.t.call('lmh4_u32',x)),0xffffffff)
        for x in ('-1','4294967296','xx','123;error no'):
            with self.subTest(x=x),self.assertRaises(tkinter.TclError):self.t.call('lmh4_u32',x)
    def test_identity_rejects_before_writes(self):
        self.t.eval('set ::regs(0xa0020008) 0')
        with self.assertRaises(tkinter.TclError):self.t.call('lmh4_require_ready',0)
        self.assertEqual(self.t.eval('llength $::events'),'0')
    def test_uncalibrated_and_busy(self):
        self.t.eval('set ::regs(0xa0020000) 0')
        with self.assertRaises(tkinter.TclError):self.t.call('lmh4_require_ready',0)
        self.t.eval('set ::regs(0xa0020000) 1;set ::regs(0xa0000000) 1')
        with self.assertRaises(tkinter.TclError):self.t.call('lmh4_require_ready',0)
    def test_gem_stop_and_readback(self):
        self.t.call('lmh4_stop_gem','0xff0e0000',0)
        self.assertEqual(int(self.t.eval('expr {$::regs(0xff0e0000)&12}')),0)
        self.assertIn('0xff0e002c',self.t.eval('set ::events'))
    def test_stuck_tx_or_failed_clear_blocks_download(self):
        self.t.eval('set ::regs(0xff0e0014) 8')
        with self.assertRaises(tkinter.TclError):self.t.call('lmh4_stop_gem','0xff0e0000',0)
        self.t.eval('set ::regs(0xff0e0014) 0;set ::fail_clear 1')
        with self.assertRaises(tkinter.TclError):self.t.call('lmh4_stop_gem','0xff0e0000',0)
        self.assertNotIn('dow',self.t.eval('set ::events'))
    def test_loader_init_globals_and_no_large_jtag_data(self):
        with tempfile.TemporaryDirectory() as d:
            paths=[Path(d)/n for n in ('bit','init.tcl','elf','xsa')]
            for p in paths:p.touch()
            paths[1].write_text('set ::init_seen 0\nset psu_mock_data 7\nproc psu_init {} {global psu_mock_data;set ::init_seen $psu_mock_data}\nproc psu_ps_pl_isolation_removal {} {}\nproc psu_ps_pl_reset_config {} {}\nproc psu_post_config {} {}\n')
            self.t.call('lmh4_loader_start',*map(str,paths))
            self.assertEqual(self.t.eval('set ::init_seen'),'7')
            self.assertNotIn('-data',self.t.eval('set ::events'))
    def test_campaign_stops_dma_before_download_and_bounds_capture(self):
        with tempfile.TemporaryDirectory() as d:
            paths=[Path(d)/n for n in ('elf','request','xsa','header','records')]
            for p in paths[:3]:p.touch()
            self.t.eval('set ::regs(0x51000034) 3;set ::regs(0x51000038) 1')
            self.t.call('lmh4_run_campaign',*map(str,paths[:3]),'0xff0e0000',*map(str,paths[3:]),1)
            events=self.t.eval('set ::events')
            self.assertLess(events.index('stop'),events.index('write 0xff0e002c'))
            self.assertLess(events.index('write 0xff0e0000'),events.index('dow '))
            self.assertEqual(paths[3].stat().st_size,128);self.assertEqual(paths[4].stat().st_size,128)
    def test_campaign_failed_dma_never_downloads(self):
        with tempfile.TemporaryDirectory() as d:
            paths=[Path(d)/n for n in ('elf','request','xsa','header','records')]
            for p in paths[:3]:p.touch()
            self.t.eval('set ::fail_clear 1')
            with self.assertRaises(tkinter.TclError):
                self.t.call('lmh4_run_campaign',*map(str,paths[:3]),'0xff0e0000',*map(str,paths[3:]),1)
            self.assertNotIn('dow ',self.t.eval('set ::events'))

class HostTests(unittest.TestCase):
    def test_execute_flag_requires_new_exclusive_confirmation(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'must_not_exist'
            r=subprocess.run([sys.executable,str(M/'standalone/private_board.py'),'--execute','--out',str(out)],capture_output=True)
            self.assertEqual(r.returncode,2);self.assertFalse(out.exists())
    def test_abort_transfer_never_runs_campaign(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d);(out/'request.bin').write_bytes(b'test')
            plan=dict(state='PREPARED_ONLY_NO_BOARD',source_sha256={},package_sha256={},request_sha256='h',
                      image='image',manifest='manifest',image_sha256='h',manifest_sha256='h',arena_crc32='00000000',host='MOCK',port=1415,gem='0xff0e0000',timeout_s=1)
            actions=[]
            def runner(cmd,**kw):actions.append(cmd[2])
            with patch.object(b,'sha',return_value='h'):
                with self.assertRaises(ValueError):b.execute(plan,out,runner=runner,transport=lambda *a,**kw:{'state':'FAIL'})
            self.assertEqual(actions,['loader','quiesce'])
            self.assertTrue((out/'FAILURE.json').exists());self.assertFalse((out/'CAPTURE_RESULT.json').exists())
    def test_initialize_failure_never_uploads(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d);(out/'request.bin').write_bytes(b'test')
            plan=dict(state='PREPARED_ONLY_NO_BOARD',source_sha256={},package_sha256={},request_sha256='h',image='image',manifest='manifest',image_sha256='h',manifest_sha256='h')
            def runner(*a,**kw):raise RuntimeError('MOCK init failure')
            with patch.object(b,'sha',return_value='h'),patch.object(b,'upload') as upload:
                with self.assertRaises(RuntimeError):b.execute(plan,out,runner=runner,transport=upload)
                upload.assert_not_called()
    def test_success_sequence_and_forward_slash_tool_arguments(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d);(out/'request.bin').write_bytes(b'test')
            plan=dict(state='PREPARED_ONLY_NO_BOARD',source_sha256={},package_sha256={},request_sha256='h',
                      image='image',manifest='manifest',image_sha256='h',manifest_sha256='h',arena_crc32='00000000',host='MOCK',port=1415,gem='0xff0e0000',timeout_s=1,scope='SYNTHETIC_ONLY')
            actions=[]
            def runner(cmd,**kw):
                self.assertTrue(all('\\' not in s for s in cmd));actions.append(cmd[2])
                if cmd[2]=='campaign':
                    (out/'header.bin').write_bytes(b'fake');(out/'records.bin').write_bytes(b'fake')
            def transport(*a,**kw):
                actions.append('tcp')
                return dict(state='PASS_TARGET_ARENA_TRANSFER_NOT_BOARD_ACCEPTANCE',image_sha256='h',manifest_sha256='h',target_crc32='00000000',bytes=335544320,target_read_checks=34)
            with patch.object(b,'sha',return_value='h'),patch.object(b,'parse_capture',return_value={'state':'PASS_SYNTHETIC_TEST_ONLY'}):
                b.execute(plan,out,runner=runner,transport=transport)
            self.assertEqual(actions,['loader','tcp','campaign'])
            self.assertFalse((out/'FAILURE.json').exists())

if __name__=='__main__':unittest.main()
