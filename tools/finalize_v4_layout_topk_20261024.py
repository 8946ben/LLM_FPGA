"""Static QA, current roadmap and bookkeeping for the completed stage B."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote,urlparse
from datetime import datetime
import hashlib,json,re,subprocess
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'module_14_lm_head_v4/reports/layout_topk_20261024_r1'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.ids=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='a' and a.get('href'):self.links.append(a['href'])
def main():
    page=ROOT/'doc/design/V4LayoutTopK.html';parser=Links();parser.feed(page.read_text(encoding='utf-8'))
    assert len(parser.ids)==len(set(parser.ids));checked=[]
    for link in parser.links:
        parsed=urlparse(link);assert not parsed.scheme,'New page has no network dependency'
        target=(page.parent/unquote(parsed.path)).resolve();assert target.exists(),target;checked.append(link)
    node='C:/Program Files/nodejs/node.exe'
    ui=subprocess.run([node,str(ROOT/'tools/check_v4_layout_topk_20261024.js')],capture_output=True,text=True,check=True)
    data=read(R/'TOP_T_PROOF.json');numeric=read(R/'NUMERIC_PROOF.json');real={(x['case'],x['id']):x for x in numeric['records'] if x['id'].startswith('partial')}
    for rec in data['records']:
        tag=rec['tag'];case=tag.rsplit('_d',1)[0];params=tag.rsplit('_d',1)[1];key='partial_dynamic_d'+params
        with __import__('numpy').load(R/real[case,key]['array']) as z:expected=hashlib.sha256(z['top'].tobytes()).hexdigest()
        assert rec['methods']['heap']['ordered_ids_sha256']==expected and rec['methods']['radix']['ordered_ids_sha256']==expected
    write(R/'PAGE_REVIEW.json',dict(state='PASS_STATIC_LINKS_JS_DOM_AND_TOP_HASHES',page_sha256=sha(page),local_links=checked,
        ui=json.loads(ui.stdout),top_hash_pairs=16,visual='NOT_RUN',qa_script_sha256=sha(Path(__file__)),ui_script_sha256=sha(ROOT/'tools/check_v4_layout_topk_20261024.js')))
    roadmap=ROOT/'doc/design/V4_NEXT_TASKS_20261024.md'
    if not (R/'ROADMAP_BEFORE_STAGE_B.md').exists():(R/'ROADMAP_BEFORE_STAGE_B.md').write_bytes(roadmap.read_bytes())
    roadmap.write_text('''# lm_head v4 后续任务规划 · 2026-10-24

当前：阶段A质量/全557补测与阶段B布局/Top-T离线评审已完成。阶段C最小Csim/HLS原型尚未运行；没有自动EDA或板卡下阶段。

## 1. 已完成的证据

- [新旧557配置GPU汇总](V4Validation.html#gpu-summary)：原320题/4775decode，新1000题/14956decode；同环境旧4＋新4固定输入，每组每配置120次。追加551点是已打开新组的补充分析，原首轮6点的标签前冻结身份保留。旧门槛/失败结论不改。
- [布局与Top-T交互评审](V4LayoutTopK.html)：两种完整权重分块、两种稳定Top-T、32组流式归约预览及24组完整数值对照通过。全部地址和访问模型由独立脚本复核；这是离线模型，不是HLS或实测DDR流量。
- [第一阶段原始报告](../../module_14_lm_head_v4/reports/layout_topk_20261024_r1/RESULT.md)。此前规划快照保留在该报告目录ROADMAP_BEFORE_STAGE_B.md。

## 2. 当前工程候选

|用途|方案|原校准整体/最低类别召回|新题整体/最低类别召回|本轮原/新固定输入GPU次/s|
|---|---|---|---|---|
|主候选|动态d64/Top4096|99.9162% / 99.6596%|99.9465% / 99.8381%|117.66 / 118.28|
|质量余量备选|动态d128/Top1024|99.9791% / 99.9149%|100% / 100%|109.56 / 111.96|
|已有方法对照|聚类C128/R4/L16384|99.6859% / 99.3333%|99.4450% / 99.0000%|118.07 / 115.83|
|完整词表对照|dense|100% / 100%|100% / 100%|65.97 / 65.85|

门槛是整体及中/英/代码/数学各类decode召回≥99%；数值实现逐位正确性仍为100%。固定dense轨迹召回不是闭环生成或任务正确率；观察零漏选不等于总体无损。GPU速度仅4固定输入、完整Eager M14参考，不是整网decode、TTFT或FPGA预测。

C256/R4/L16384在新题最低类别98.6667%，不作为优先硬件候选；R2同样未过新质量。d64/Top1024虽新题通过但原校准分项失败，不因新组表现替换主候选。L32768/65536未显示比原聚类更好的质量，不按几个百分点GPU速率变化选择更大列表。低秩/融合与桶/LSH研究结果保留，不继续大规模盲扫。

## 3. 阶段B结论：先采用哪种工程路径

建议主配置先试“双份权重＋1024词分块预览＋FP32流式相邻树＋radix阈值选择”。

- 双份B1024拟定arena528.75MiB，共享B1024为269.00MiB，均处于已有2GiB高地址窗口。新布局是离线提案，旧320MiB loader/profile不能直接复用；新descriptor/身份/软件需后续开发。
- 共享权重精算按128位拍取8个相邻词，本轮8输入读取放大4.73–7.16倍，且请求数更多。双份布局用容量换取候选精算的连续行访问。共享可作容量受限备选，不把它判为所有系统都不可用。
- B1024使d64预览请求75968→9536，代价为末块80KiB额外读取和28KiB流式树栈；d128树栈32KiB。实际II、banking和浮点流水待HLS，不能由容量除法断言综合资源。
- heap与radix均逐项正确；radix先试4轮直方图＋1轮ID发出，键缓存可放DDR。CPU耗时不决定硬件排名；堆保留有限备选，不并行开发多套完整系统。

阶段B达到PASS_TO_MINIMAL_PROTOTYPE；不代表硬件资格通过。

## 4. 阶段C：下一个有限任务

只实现d64/Top4096一个主候选；d128仅保留接口容量余量，不同时综合第二套完整系统。

1. 新隔离实验目录冻结布局、候选顺序、FP32相邻归约、history penalty、平局和错误合同。布局重排不能改变通道归约顺序；保留canonical精算H8/interleave16数值语义。
2. 最小内核按动态通道选择、分块预览、radix阈值/位图去重、候选精算分职责组织，是否物理拆IP由数据流评审决定。预览乘法向量宽度先以128位读取能力约束，不预承诺II=1或DSP数。
3. Csim做8固定状态、A→B→A、T平局/零/边界、错误门控和完整中间数组/输出逐位核对。只改变布局/等价实现时不重采质量；若改参数或近似算术，另立质量流程。
4. 顺序HLS，报告各阶段真实II、延迟、BRAM/DSP/端口、突发和总调用模型。特别检查堆依赖或radix外存扫描、stream carry FP32流水和bitmap OR冲突。若资源/II不合格，保留失败，最多比较预声明工程备选，不自动无限扩扫。
5. 根据真实结果决定是否进入完整RTL；不能将乘法项/8、字节/16或旧GPU速率当作FPGA性能。

交付：冻结入口、隔离源码、Csim逐位证明、HLS报告、阶段成本和继续/停止结论。当前该阶段NOT_RUN。

## 5. 后续系统与板卡阶段

最小原型通过后再做完整RTL逐位核对→新私有IP/200MHz实现与STA/CDC/DRC→匹配bit/XSA/PS init/BSP/ELF/loader与SHA离线包。每阶段以真实产物为准，不继承旧核资格。

板卡测试仅在用户另行确认连接和独占安排后启动。验收新身份/PLDDR通路、canonical SHA及回读CRC/sentinel、四类/多步完整数值、≥30次计时和1000次变输入稳定调用；区分历史v3.1与同板同轮对照。主展示完整M14 median/P95和等效输出率，整网decode/TTFT接入后另测。

## 6. 持续约束

全部现有质量组已打开，不利用它们调参再认证；冻结/封存的v3.1/v4/v4b及实验10原99.9%失败结论不改。v4b量化仍并行，稀疏＋量化融合未来另立研究，后端不同的GPU速度不直接排名。不连接/探测/操作FPGA，不恢复wb/luyou/心跳。
''',encoding='utf-8')
    # Regenerate only the active validation page; exact embedded data comparison
    # makes navigation changes distinct from historical experiment results.
    validation=ROOT/'doc/design/V4Validation.html';before=validation.read_text(encoding='utf-8')
    beforeblocks={k:v for k,v in re.findall(r'<script id="([^"]+)" type="application/json">(.*?)</script>',before,re.S)}
    before_sha=sha(validation)
    import render_v4_validation;render_v4_validation.render()
    after=validation.read_text(encoding='utf-8');afterblocks={k:v for k,v in re.findall(r'<script id="([^"]+)" type="application/json">(.*?)</script>',after,re.S)}
    assert beforeblocks==afterblocks,'Historical experiment/chart payload changed'
    assert 'href="V4LayoutTopK.html"' in after
    write(R/'NAVIGATION_REVIEW.json',dict(state='PASS_ACTIVE_NAV_ONLY_PAYLOAD_IDENTICAL',before_sha256=before_sha,after_sha256=sha(validation),
        identical_json_block_ids=list(beforeblocks),no_journal_edit=True,archived_pages_untouched=True))
    result=read(R/'RESULT.json');result['final_review_sha256']={n:sha(R/n) for n in ['PAGE_REVIEW.json','NAVIGATION_REVIEW.json']};write(R/'RESULT.json',result)
    write(R/'PROGRESS.json',dict(stage='STAGE_B_COMPLETE',updated=datetime.now().astimezone().isoformat(),
        no_background_job=True,next='Minimal Csim/HLS finite task not started',board='NOT_RUN',EDA='NOT_RUN'))
    print(json.dumps(dict(state='PASS',links=len(checked),ui=json.loads(ui.stdout),chart_payload_unchanged=True)))

if __name__=='__main__':main()
