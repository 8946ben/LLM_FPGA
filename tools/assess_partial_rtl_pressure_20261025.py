"""Analytical diagnostic only: does not launch EDA or predict completion."""
from pathlib import Path
from fractions import Fraction
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/partial_rtl_20261024_r1';P=R/'full_r3/observations/20261025_r3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
snapshot=json.loads((P/'RUNTIME_SNAPSHOT.json').read_text());plan=json.loads((R/'full_r3/PLAN.json').read_text());assert plan['expected']['K']==4109
assert snapshot['pressure_model']['random_delay_max_cycles']==256
# Abstract serial read-data model. Overlapping dist entries are interpreted by
# additive weights: mass9 at0, mass1 at256, mass2 uniform across0..256.
mean=(Fraction(9*0+256,1)+2*Fraction(0+256,2))/12
preview=149*64*128;exact=4109*112;beats=preview+exact
result=dict(state='ANALYTICAL_PRESSURE_SCALE_ONLY_NOT_QUALIFICATION',preview_weight_beats=preview,exact_weight_beats=exact,total_weight_read_beats=beats,
    distribution_model=dict(assumption='Additive dist weights; independent samples; serial one delay per data beat',mean_delay_cycles=float(mean),mean_delay_fraction=str(mean)),
    abstract_read_channel=dict(mean_idle_cycles=float(beats*mean),mean_transfer_plus_idle_cycles=float(beats*(1+mean)),simulation_clock_ns=5,
                              mean_transfer_plus_idle_sim_ms=float(beats*(1+mean)*Fraction(5,1000000)),maximum_inserted_idle_cycles=beats*256),
    facts='Complete configured C reference uses149tiles*64channels*128beats and4109candidate rows*112beats. No new quality or hardware test.',
    exclusions=['Not measured AXI counts or final latency','Does not account for all arbitration/compute/stalls/overlap','No remaining-time or completion-percent estimate','Cannot prove useful pipeline progress or rule out deadlock','Not physical DDR bandwidth or normal FPGA/LLM decode speed'],
    input_sha256={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in [P/'RUNTIME_SNAPSHOT.json',P/'lm_head_v4_partial_proto_env.sv',P/'axi_slave_seq_lib.sv',R/'full_r3/PLAN.json',M/'experiments/partial_hw_20261024/r3/partial_proto.cpp',M/'experiments/partial_hw_20261024/r3/derived/lm_head_v4_candidate.cpp']},source_sha256=sha(Path(__file__)))
(R/'PRESSURE_SCALE_MODEL.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(state=result['state'],weight_beats=beats,abstract_sim_ms=result['abstract_read_channel']['mean_transfer_plus_idle_sim_ms'])))
