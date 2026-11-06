"""Freeze a future bounded runner's inputs. No remote upload/compilation/execution."""
from pathlib import Path
import ast,datetime,hashlib,json
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4'
E=M/'experiments/d64_native_memory_20261103_r1';R=M/'reports/d64_native_memory_20261103_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    gate=json.loads((R/'GATE_PREPARATION_PLAN.json').read_text(encoding='utf-8'))
    assert gate['state']=='PREPARED_NOT_COMPILED_OR_QUALIFIED'
    for name,digest in gate['sources'].items():assert sha(ROOT/name)==digest,name
    original=M/'reports/memory_growth_diagnosis_20261103_r1/sources'
    copy_map={
        'memory_probe_pkg.sv':M/'experiments/memory_full_startup_20261103_r1/memory_probe_pkg.sv',
        'd64_native_memory.sv':E/'d64_native_memory.sv',
        'native_gate_tb.sv':E/'native_gate_tb.sv',
        'file_agent/mem_model.sv':M/'experiments/memory_burst_model_20261103_r3/mem_model.sv'}
    for name in ['file_agent_pkg.sv','file_read_agent.sv','file_write_agent.sv']:
        copy_map['file_agent/'+name]=original/'file_agent'/name
    ast.parse((E/'run_gate.py').read_text())
    sources={p.relative_to(ROOT).as_posix():sha(p) for p in [*copy_map.values(),E/'run_gate.py',ROOT/'tools/review_d64_native_gate_20261104.py']}
    out=dict(state='PREPARED_NOT_EXECUTED',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        gate_plan_sha256=sha(R/'GATE_PREPARATION_PLAN.json'),sources=sources,
        compile_copy_map={name:p.relative_to(ROOT).as_posix() for name,p in copy_map.items()},
        project_order=['memory_probe_pkg.sv','file_agent/file_agent_pkg.sv','d64_native_memory.sv','native_gate_tb.sv'],
        cases=gate['cases'],guards=gate['planned_guards'],
        authorization='MANUAL_GATE_AUTHORIZATION.json does not exist. Requires independently reviewed current full RTL PASS, exact review/workflow/plan SHA, current process/group/lock empty and explicit manual decision.',
        runner_status='Python syntax/static preparation only. Runner lifecycle controls not yet qualified. No model/tool/testbench/runtime qualification.',
        required_before_launch=['Independent local review of runner guards and owned-group cleanup',
                                'Current full call independent numeric/FIFO PASS and current empty group/lock',
                                'Freeze manual gate authorization with actual PASS hashes; no automatic generation'],
        eda='NOT_RUN',board='NOT_RUN',automatic_next_stage=False)
    target=R/'EXECUTION_PREPARATION_PLAN.json';assert not target.exists()
    assert not (R/'MANUAL_GATE_AUTHORIZATION.json').exists() and not (R/'WORKFLOW.json').exists()
    target.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(dict(state=out['state'],sources=len(sources),cases=len(out['cases']),authorization='ABSENT',eda='NOT_RUN'),indent=2))
if __name__=='__main__':main()
