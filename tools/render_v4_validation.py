"""Render the offline scenario page from the journal's canonical snapshot."""
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
def render():
    source=(ROOT/'开发日志.html').read_text(encoding='utf-8')
    data=json.loads(re.search(r'<script id="dev-log-data" type="application/json">(.*?)</script>',source,re.S)[1])
    payload=json.dumps(data['v4_validation'],ensure_ascii=False,indent=2,allow_nan=False).replace('<',r'\u003c')
    template=(ROOT/'doc/design/templates/V4Validation.html').read_text(encoding='utf-8')
    template=re.sub(r'<!-- TEMPLATE_ONLY_START -->.*?<!-- TEMPLATE_ONLY_END -->','',template,flags=re.S)
    from render_v4_gpu_summary import render as gpu_summary
    summary=gpu_summary()
    layout_result=ROOT/'module_14_lm_head_v4/reports/layout_topk_20261024_r1/RESULT.json'
    if layout_result.exists() and json.loads(layout_result.read_text(encoding='utf-8')).get('state')=='STAGE_B_COMPLETE_PASS_TO_MINIMAL_PROTOTYPE':
        summary+='''<section class="panel" id="layout-topk-review"><h2>下一阶段：布局与 Top-T 离线评审已完成</h2><p>固定 d64/Top4096 为主候选，d128/Top1024 为备选；两种布局、两种稳定 Top-T 和流式归约已做逐位核对。建议评估双份权重、1024词分块、radix 阈值选择的最小硬件原型。</p><p><a href="V4LayoutTopK.html">查看交互报告：DDR 容量、8 输入读取量、每一步操作与数值证明 →</a></p><p>以上是离线模型；HLS、RTL、新200MHz系统和板卡尚未运行，GPU汇总图数据保持原结果。</p></section>'''
    hardware_result=ROOT/'module_14_lm_head_v4/reports/partial_hw_20261024_r1/RESULT.json'
    if hardware_result.exists():
        hardware=json.loads(hardware_result.read_text(encoding='utf-8'))
        if hardware.get('state') in {'CSIM_PASS_HLS_ESTIMATE_PASS_RTL_PENDING','CSIM_PASS_HLS_TIMING_OR_RESOURCE_FAIL_NO_RTL'}:
            summary=summary.replace('以上是离线模型；HLS、RTL、新200MHz系统和板卡尚未运行，GPU汇总图数据保持原结果。','以上为已完成布局阶段的离线模型；后续最小硬件原型结果见下方入口，GPU汇总图数据保持原结果。')
            summary+='''<section class="panel" id="partial-hardware-review"><h2>最小硬件原型：STHL Csim / HLS 已完成</h2><p>d64/Top4096 的11次有效调用及6项错误门控通过，r1/r2/r3完整数值输出一致；接口与缓存调度修正、实际资源/II及HLS时序估计均有原始报告。RTL、布局布线和板卡速度尚未验证。</p><p><a href="V4PartialHardware.html">查看硬件原型报告：r2 / r3 对照与验证边界 →</a></p></section>'''
    rendered=template.replace('__VALIDATION_DATA__',payload)
    anchor='<section class="panel" id="experiments">'
    assert rendered.count(anchor)==1
    rendered=rendered.replace(anchor,summary+'\n'+anchor)
    (ROOT/'doc/design/V4Validation.html').write_text(rendered,encoding='utf-8')
if __name__=='__main__':render();print('V4 validation scenarios synchronized from journal snapshot; no hardware access')
