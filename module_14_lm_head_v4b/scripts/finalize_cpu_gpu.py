"""Read-only numerical/source recount, then write the CPU/GPU phase report.

No fitting, generation, accelerator calls or board activity. Invoked by page sync
only after the frozen final evaluator has actually produced its completion file.
"""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,math
import numpy as np
M=Path(__file__).resolve().parents[1];ROOT=M.parent;O=M/'reports/quantization_20261023_r1'
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8*2**20),b''):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,obj):
    p=Path(p);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');tmp.replace(p)
def main():
    if not (O/'FINAL_QUALITY.json').exists():return
    if (O/'RESULT.json').exists():
        result=read(O/'RESULT.json');assert result['final_quality_sha256']==sha(O/'FINAL_QUALITY.json');return
    final=read(O/'FINAL_QUALITY.json');D=M/'data/final_quality_20261023';folder=M/'data/hidden_final_20261023/holdout';manifest=read(folder/'MANIFEST.json')
    entry=read(D/'EVALUATION_ENTRY_LOCK.json');selection=read(O/'SELECTION_LOCK.json')
    assert manifest['state']=='PASS' and manifest['prompts']==1000 and manifest['excluded_prompts']==0
    assert sha(O/'SELECTION_LOCK.json')==entry['selection_lock_sha256']==final['selection_lock_sha256']
    assert sha(D/'holdout.jsonl')==entry['corpus_sha256']==manifest['settings']['corpus_sha256']
    assert sha(folder/'MANIFEST.json')==final['collection_manifest_sha256']
    for path,h in entry['sources'].items():assert sha(ROOT/path)==h,path
    labels=[];scores=[];category=[];groups=[];decode=[]
    for item in manifest['records']:
        path=folder/item['npz'];assert sha(path)==item['npz_sha256']
        with np.load(path,allow_pickle=False) as a:
            labels.extend(a['dense_token']);scores.extend(a['dense_score_bits'])
        category.extend([item['category']]*item['steps']);groups.extend([item['group_sha256']]*item['steps']);decode.extend([False]+[True]*(item['steps']-1))
    labels=np.asarray(labels,dtype='u4');scores=np.asarray(scores,dtype='u4');category=np.asarray(category);groups=np.asarray(groups);decode=np.asarray(decode)
    assert len(set(groups))==1000 and len(labels)==final['predictions'] and int(decode.sum())==final['decode_predictions']
    reservation=read(D/'MANIFEST.json');prior_groups=set();prior_prompts=set()
    for relative,expected in reservation['prior_prompt_files_sha256'].items():
        path=ROOT/relative;assert sha(path)==expected
        for line in path.read_text(encoding='utf-8').splitlines():
            if line.strip():r=json.loads(line);prior_groups.add(r['group_sha256']);prior_prompts.add(r['prompt_sha256'])
    fresh=[json.loads(line) for line in (D/'holdout.jsonl').read_text(encoding='utf-8').splitlines()]
    assert not {r['group_sha256'] for r in fresh}&prior_groups
    assert not {r['prompt_sha256'] for r in fresh}&prior_prompts
    assert {c:sum(r['category']==c for r in fresh) for c in ['chinese','english','code','math']}==reservation['counts']
    reviews=[]
    for result in final['results']:
        path=O/result['arrays'];assert sha(path)==result['arrays_sha256']
        with np.load(path,allow_pickle=False) as a:
            hits=a['token']==labels;np.testing.assert_array_equal(a['hits'],hits)
            np.testing.assert_array_equal(a['policy_dense_winner_rank']<(result['K'] if result['kind']=='refine' else 1),hits)
            if result['kind']=='refine':np.testing.assert_array_equal(a['score_bits'][hits],scores[hits])
            for name,mask in [('all',np.ones(len(labels),dtype=bool)),('decode',decode),('prefill',~decode)]:
                q=result['quality'][name];assert q['steps']==int(mask.sum()) and q['misses']==int((~hits[mask]).sum())
                for c,sub in q['by_category'].items():
                    cmask=mask&(category==c);assert sub['steps']==int(cmask.sum()) and sub['misses']==int((~hits[cmask]).sum())
            passing=float(hits[decode].mean())>=.999 and all(float(hits[decode&(category==c)].mean())>=.999 for c in sorted(set(category)))
            assert passing==result['quality_gate']
            assert len(result['errors'])==int((~hits).sum())
        reviews.append(dict(id=result['id'],arrays_sha=True,independent_counts=True,rank_membership=True,quality_gate=passing))
    timing=read(O/'GPU_TIMING_RAW.json')['records'];bench=read(O/'GPU_BENCHMARK.json')
    for method in bench['methods']:
        values=np.asarray([r['wall_ms'] for r in timing if r['method']==method['id']],dtype='f8')
        assert len(values)==120 and len(values)==method['samples']
        assert math.isclose(float(np.mean(values)),method['mean_ms'],rel_tol=1e-12)
        assert math.isclose(float(np.median(values)),method['median_ms'],rel_tol=1e-12)
        assert math.isclose(float(np.sort(values)[math.ceil(.95*len(values))-1]),method['p95_ms'],rel_tol=1e-12)
    review=dict(state='PASS_INDEPENDENT_FINAL_COUNTS_SOURCE_AND_TIMING_REVIEW',checked=datetime.now(timezone(timedelta(hours=8))).isoformat(),review_script_sha256=sha(Path(__file__)),
      final_points=reviews,fresh_prompt_groups=1000,prior_overlap=0,original_frozen_sources_match=True,timing_samples=len(timing),
      final_quality_sha256=sha(O/'FINAL_QUALITY.json'),scope='Posthoc independent evidence audit; no model/quality rerun or retuning')
    write(O/'FINAL_INDEPENDENT_REVIEW.json',review)
    result=dict(state='COMPLETE_CPU_GPU_AND_NEW_QUALITY_PHASE',quality_state=final['state'],
      completed=review['checked'],RTN_points=32,new_calibrated_method_points=8,reused_RTN_controls=4,
      preview_K_calibration_points=12,calibration_predictions_per_point=5095,
      complete_cpu_gpu_fixture_raw_proofs=40*4,gpu_timing_samples=len(timing),
      final_prompts=1000,final_predictions=final['predictions'],final_decode_predictions=final['decode_predictions'],
      selected=selection['selected'],quality=final['results'],gpu=bench['methods'],
      final_quality_sha256=sha(O/'FINAL_QUALITY.json'),independent_review_sha256=sha(O/'FINAL_INDEPENDENT_REVIEW.json'),
      integer_MAC_study='NOT_RUN',residual_codebook_rotation='NOT_RUN',natural_text_nll='NOT_RUN',closed_loop_generation='NOT_RUN',
      csim='NOT_RUN',hls='NOT_RUN',rtl='NOT_RUN',system_implementation='NOT_RUN',board='NOT_RUN',
      next='Assess qualified candidates for separate v4b hardware development. No automatic EDA/board stage, no retuning on opened final group.')
    write(O/'RESULT.json',result)
    rows=[]
    for r in final['results']:
        rows.append(f"| {r['id']} | {r['quality']['decode']['misses']}/{r['quality']['decode']['steps']} | {r['quality']['decode']['recall']*100:.4f}% | {'PASS' if r['quality_gate'] else 'FAIL — NO RETUNE'} |")
    text=f'''# v4b 首轮CPU/GPU与全新问题质量阶段

完成时间：{result['completed']}。状态：{final['state']}。独立来源/数组/计时复核PASS。

工程父版本v3.1；v4并行且冻结资产不改。本轮未访问或探测板卡。

## 已完成的实际实验

- 原8步全raw/policy SHA、token/score/CRC与四类完整CPU/GPU数值；全部5095校准dense token/score bits复现。
- 32点RTN、4个GPTQ、4个AWQ-style新点（另4个RTN控制复用）；每点真实packed W/独立解包/四类完整raw位核验与5095预测。
- 12个量化预筛K校准点，按预声明字节目标锁点，不按新问题或GPU速度换点。
- 6方案×4固定输入×30次=720次同轮GPU测量，另每组合3次warmup；真实packed与完整在线Top-K/gather/精算管线数值证明。
- 全新1000问题，{final['predictions']}次预测、{final['decode_predictions']}decode、零排除。中400/英250/DS-1000代码100/数学250；全部旧保留组/快照规范化去重，来源及入口先锁定。

## 锁点的新质量结果

| 锁点 | decode错选/漏选 | decode一致率 | 整体及各类decode≥99.9% |
| --- | ---: | ---: | --- |
'''+ '\n'.join(rows)+'''

直接量化一致率与量化预筛候选召回分别验证；精算路径全部实际执行候选BF16计算，不仅统计membership。首输出、各类、整题一致率和区间、错误明细见FINAL_QUALITY.json。

## 验证边界与后续

GPU结果是本机独立M14参考，使用新qualified CUDA算术及真实packed buffer；不与旧Eager绝对速率混连，不是优化生产GPU推理/FPGA/TTFT。作业执行总耗时不算推理速度。权重字节和读取预算不等于实际AXI流量。

新问题只评估锁定配置一次，任何失败均保留；不得在已打开组调参再认证。该质量是固定canonical dense轨迹的条件下一token一致性，不是无损证明、自然文本PPL、自由生成或任务解答正确率。DS-1000参考代码/测试未执行。

整数MAC、离群残差、码本/旋转、自然文本NLL与闭环生成尚未执行。新v4b内核/descriptor/IP身份/布局仍待开发；Csim/HLS/RTL/200MHz实现/BSP/ELF/板卡均NOT_RUN。下一步是合格候选的硬件可行性评审，当前有限流程不自动启动EDA或板测。
'''
    (O/'RESULT.md').write_text(text,encoding='utf-8')
if __name__=='__main__':main()
