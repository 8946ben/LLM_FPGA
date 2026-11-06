"""Record the user's pause without starting tools or touching hardware."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, shutil
M=Path(__file__).resolve().parents[1]
R=M/'reports';out=R/'pause_20261021'
out.mkdir(exist_ok=True)
now=datetime.now(timezone(timedelta(hours=8))).isoformat()
names=['hls_selector_csim_r2_20261021.log','hls_selector_csynth_r2_20261021.log',
       'hls_selector_full_cosim_r1_20261021.log','selector_bd_create_r1_20261021.log',
       'selector_system_build_r1_20261021.log','host_tests_selector_20261021.log',
       'selector_control_test_20261021.log','SELECTOR_CONTROL_REGISTER_AUDIT.json',
       'SELECTOR_PRIVATE_IP_MANIFEST.json','SELECTOR_LOCAL_IP_REVISION_REPAIR.json']
evidence={}
for name in names:
    p=R/name
    if p.exists():
        shutil.copy2(p,out/name)
        evidence[name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
runs=[]
for p in sorted((M/'board/build/m14_v4/m14_v4.runs').glob('*/runme.log')):
    dst=out/'vivado_runs'/p.parent.name;dst.mkdir(parents=True,exist_ok=True)
    shutil.copy2(p,dst/'runme.log')
    runs.append({'run':p.parent.name,'dcps':[v.name for v in p.parent.glob('*.dcp')],
                 'log_sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
state=dict(state='PAUSED_BY_USER',updated=now,reason='User: 先安全暂停',hardware_access='NONE',
    full_rtl='INTERRUPTED_BEFORE_RTL_SIMULATION_NO_PASS',
    full_rtl_last_stage='C reference valid1/preflight_invalid1; generating RTL testbench',
    system='INTERRUPTED_DURING_CHILD_IP_SYNTHESIS_NO_TOP_DCP_NO_ROUTE_NO_BIT_XSA',
    completed=dict(csim={'valid':6,'preflight_invalid':24,'stage_errors':5},host_tests=32,
                   control_fake_mmio_tests=25,hls_estimated_ns=3.650,
                   hls_resources={'BRAM_18K':153,'DSP':247,'FF':88775,'LUT':92410},
                   frozen_ip_files=301,bd_validation='PASS'),
    evidence=evidence,vivado_runs=runs,auto_resume=False,
    resume='Read doc/LM_HEAD_V4_HANDOFF_20261021.md; require explicit user resume; no board operations')
(out/'CHECKPOINT.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=M/'PROGRESS.json';d=json.loads(p.read_text(encoding='utf-8'))
d.update(updated=now,stage='PAUSED_BY_USER_INTEGRATED_HLS_PASS_RTL_AND_SYSTEM_INTERRUPTED',
         active_work='NONE: user pause; own HLS/Vivado trees stopped; no board',
         runtime_processes='NONE: no active EDA task; old WB/heartbeats remain stopped',
         next='Wait for explicit user resume; see handoff and reports/pause_20261021/CHECKPOINT.json',
         dependencies=['FullV integrated RTL official PASS and cycle report pending; interrupted during TB generation',
                       'Complete system synthesis/P&R/200MHz STA/CDC/DRC/bit-XSA audit pending',
                       'Actual PS BSP/ELF and target-readback asset loader pending',
                       'New arithmetic independent quality not certified; opened holdouts not reusable',
                       'User pause; no FPGA board access authorized; upstream direct weights deferred'])
d['milestones']['P4']='INTEGRATED_CSIM_HLS_BD_PASS; full RTL/system implementation interrupted by user; no board'
d['integrated_selector'].update(state='CSIM_CSYNTH_IP_BD_PASS_PAUSED_BEFORE_RTL_AND_SYSTEM_ACCEPTANCE',
    hls_estimated_ns=3.65,resources=state['completed']['hls_resources'],control_fake_mmio_tests=25,
    rtl=state['full_rtl'],system=state['system'],private_system_signature='0x4D345301 (not public ABI/build)',
    frozen_ip_manifest='reports/SELECTOR_PRIVATE_IP_MANIFEST.json')
for name in names+['pause_20261021/CHECKPOINT.json']:
    rel='reports/'+name
    if rel not in d['evidence']:d['evidence'].append(rel)
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('V4_PAUSE_CHECKPOINT_SAVED; no tool launches; no hardware access')
