"""Independent review of saved actual event files, resource traces and hashes."""
from pathlib import Path
import hashlib,json,datetime
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4'
R=M/'reports/d64_resource_recovery_20261102_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 plan=json.loads((R/'PLAN.json').read_text());w=json.loads((R/'WORKFLOW.json').read_text())
 assert w['state']=='TOOL_PASS_AWAITING_INDEPENDENT_REVIEW' and not w['process_after']
 assert not (R/'ACTIVE.lock').exists()
 for n,h in plan['source_sha256'].items():assert sha(ROOT/n)==h,n
 original=M/'reports/sim_memory_bank_20261026_r1/memory_events.csv'
 actual=R/'packed_unit/memory_events.csv'
 assert actual.read_text().splitlines()==original.read_text().splitlines()
 assert len(actual.read_text().splitlines())==2093
 log=(R/'packed_unit/simulate.log').read_text()
 assert any(x.startswith('PACKED_LANES_PASS lanes=16 last_bank=17 padding_rejected=1 reinit=1 four_state=1') for x in log.splitlines())
 expected='0,534773760\n1,534773760\n2,534773760\n'
 metrics={}
 for name in ['byte_bench','packed_bench']:
  assert (R/name/'bench_events.csv').read_text()==expected
  samples=[json.loads(x) for x in (R/name/'simulate_resources.jsonl').read_text().splitlines()]
  peak=max(x['group_rss_kib'] for x in samples)
  assert peak==w['cases'][name]['simulate']['peak_group_rss_kib']
  assert all(x['available_kib']>=32*1024*1024 for x in samples)
  metrics[name]={'peak_group_rss_kib':peak,'elapsed_s':w['cases'][name]['simulate']['elapsed_s'],
   'resource_sha256':sha(R/name/'simulate_resources.jsonl'),'checksum_sha256':sha(R/name/'bench_events.csv')}
 result={'state':'PASS_PACKED_BANK_SEMANTICS_AND_FINITE_BENCHMARK','reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'events_equal':2093,'original_events_sha256':sha(original),'actual_events_sha256':sha(actual),'additional_packed_lane_assertions':'PASS',
  'benchmark':metrics,'group_peak_reduction_percent':100*(1-metrics['packed_bench']['peak_group_rss_kib']/metrics['byte_bench']['peak_group_rss_kib']),
  'limits':['Peak includes XSim frontend and kernel, sampled at 1 second; not exact allocation size',
    '4MiB single-run memory benchmark is not full-input memory qualification or M14/FPGA performance',
    'Old final protection trigger remains unresolved; missing terminal resource sample cannot be reconstructed'],
  'process_after':[],'full_m14':'NOT_RUN','board':'NOT_RUN','automatic_next_stage':False}
 (R/'INDEPENDENT_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
