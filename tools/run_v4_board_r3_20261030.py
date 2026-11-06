"""One qualified board campaign with mandatory Tcl markers; no automatic next case."""
from pathlib import Path
import argparse,json,subprocess,sys,hashlib,datetime,os,shutil
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/dual_board_20261030_r1'
p=argparse.ArgumentParser();p.add_argument('variant',choices=['baseline_hybrid','exp10']);p.add_argument('case',choices=['chinese','english','code','math']);p.add_argument('--complete-first-manual-transfer',action='store_true');a=p.parse_args()
base=M if a.variant=='baseline_hybrid' else M/'experiments/fusion_exp10_20261023';sys.path.insert(0,str(base/'standalone'))
import private_board as pb
original_package=pb.PACKAGE
pb.PACKAGE=R/'runtime_packages'/(a.variant+'_'+a.case)
assert not pb.PACKAGE.exists(), 'Preserve used runtime copy'
pb.PACKAGE.mkdir()
for line in (original_package/'SHA256SUMS.txt').read_text().splitlines():
    if not line.strip():continue
    digest,name=line.split('  ',1)
    with (original_package/name).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
    shutil.copy2(original_package/name,pb.PACKAGE/name)
shutil.copy2(original_package/'SHA256SUMS.txt',pb.PACKAGE/'SHA256SUMS.txt')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
out=base/'reports/board_acceptance_20261030_r3'/a.case
plan=pb.prepare(a.case,out,900)
control=out/'control';control.mkdir()
s=(base/'standalone/scripts/private_board_common.tcl').read_text();needle='    stop\n    rst -processor\n    dow $elf\n';assert s.count(needle)==1
replacement='''    if {[catch {stop} stop_message stop_options]} {
        if {![string match {*APU L2 cache is held in reset*} $stop_message]} {return -options $stop_options $stop_message}
        puts "M4_INITIAL_STOP_ALREADY_IN_RESET=$stop_message"
    }
    rst -processor
    dow $elf
'''
(control/'private_board_common.tcl').write_text(s.replace(needle,replacement))
s=(base/'standalone/scripts/private_board_entry.tcl').read_text().replace('puts stderr "M4_PRIVATE_BOARD_ERROR: $message"','puts stderr "M4_PRIVATE_BOARD_ERROR: $message"\n    puts stderr [dict get $options -errorinfo]')
(control/'private_board_entry.tcl').write_text(s)
save(out/'CONTROL_DERIVATION.json',dict(source_sha256={str(x):sha(x) for x in (base/'standalone/scripts').glob('private_board*.tcl')},runtime_sha256={str(x):sha(x) for x in control.glob('*.tcl')},only_change='Accept exact initial APU L2 already-reset stop error then original rst/dow/con; full errorinfo; require real action markers even when batch exits0',package_unchanged=True))
lock=R/'ACTIVE.lock'
with lock.open('x') as f:f.write(str(os.getpid()))
state=dict(state='EXECUTING',variant=a.variant,case=a.case,pid=os.getpid(),started=datetime.datetime.now(datetime.timezone.utc).isoformat(),automatic_next_case=False)
save(out/'EXECUTION.json',state)
def runner(argv,stdout,stderr,check):
    argv=list(argv);argv[1]=str(control/'private_board_entry.tcl').replace('\\','/')
    result=subprocess.run(argv,stdout=stdout,stderr=stderr,timeout=1100 if argv[2]=='campaign' else 240)
    stdout.flush();s=Path(stdout.name).read_text(errors='replace')
    marker={'loader':'M4_PRIVATE_LOADER_STARTED','campaign':'M4_PRIVATE_CAPTURE_COMPLETE_PENDING_HOST_VALIDATION','quiesce':'M4_PRIVATE_CPU_GEM_QUIESCED'}[argv[2]]
    if result.returncode or marker not in s or 'M4_PRIVATE_BOARD_ERROR:' in s:raise RuntimeError('Actual Tcl action failed: '+argv[2]+'; inspect '+stdout.name)
    return result
try:
    if a.complete_first_manual_transfer:
        assert a.variant=='baseline_hybrid' and a.case=='chinese'
        assert read(R/'INITIALIZATION_R3.json')['state']=='LOADER_STARTED'
        transfer=read(R/'baseline_chinese_TRANSFER_r3.json')
        assert transfer['state']=='PASS_TARGET_ARENA_TRANSFER_NOT_BOARD_ACCEPTANCE' and transfer['target_read_checks']==34 and transfer['bytes']==335544320
        assert transfer['image_sha256']==plan['image_sha256'] and transfer['manifest_sha256']==plan['manifest_sha256'] and transfer['target_crc32']==plan['arena_crc32']
        save(out/'TRANSFER.json',transfer)
        save(out/'MANUAL_CURRENT_TURN_INITIALIZATION.json',dict(source=str(R/'initialization_r3.log'),sha256=sha(R/'initialization_r3.log'),scope='Continuation of this same explicit initialization and completed TCP transfer; no prior-session retained state'))
        with (out/'campaign.log').open('x') as log:
            args=[str(pb.XSCT),str(control/'private_board_entry.tcl'),'campaign',str(pb.PACKAGE/'m14_v4_selector_test.elf'),str(out/'request.bin'),str(pb.PACKAGE/'m14_v4_single.xsa'),plan['gem'],str(out/'header.bin'),str(out/'records.bin'),str(plan['timeout_s'])]
            runner([x.replace('\\','/') for x in args],stdout=log,stderr=subprocess.STDOUT,check=True)
        result=pb.parse_capture((out/'request.bin').read_bytes(),(out/'header.bin').read_bytes(),(out/'records.bin').read_bytes());save(out/'CAPTURE_RESULT.json',result)
    else:result=pb.execute(plan,out,runner=runner)
    state.update(state='FIXED_INPUT_CAMPAIGN_RETURNED_PENDING_INDEPENDENT_REVIEW',result_state=result['state'])
except BaseException as exc:
    state.update(state='FAILED_NO_AUTOMATIC_RETRY',error=repr(exc));raise
finally:
    state['finished']=datetime.datetime.now(datetime.timezone.utc).isoformat();save(out/'EXECUTION.json',state);lock.unlink()
print(json.dumps({k:v for k,v in result.items() if k!='records_data'},ensure_ascii=False,indent=2))
