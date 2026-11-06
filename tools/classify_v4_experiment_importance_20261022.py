"""Classify research value and minimum acceptance scope; documentation only."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import copy,json,re,sys
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=ROOT/'开发日志.html';s=p.read_text(encoding='utf-8');m=re.search(r'(<script id="dev-log-data" type="application/json">)(.*?)(</script>)',s,re.S);d=json.loads(m[2]);previous=copy.deepcopy(d['entries']);v=d['v4_validation']
    definitions={
      'quality':dict(level='必须完成',kind='核心研究 / 方案决策',
        reason='直接决定稀疏化是否值得采用、选择哪种方案，以及质量损失换来了多少速度收益。这是研究主结论。',
        minimum='必须完成三稀疏方案与dense的质量对照；必须用实际FPGA结果验证dense与拟采用方案的数值正确性和速度收益。质量不合格的方案不因GPU更快而进入发布。',
        extension='仅聚类/仅低秩若未达到冻结质量门槛，其全套FPGA实现和测速可按论文论证需要追加，不为凑齐四条曲线强制开发。GPU只是参考，不能替代最终板端收益。',
        order='研究主线优先；真实FPGA部分等待用户新的独占安排。'),
      'k-sensitivity':dict(level='建议完成',kind='性能解释 / 后续优化',
        reason='解释混合方案在不同候选规模下的成本与尾部时延，帮助决定以后优化低秩扫描、候选精算还是DDR读取；不改变当前三方案质量对比的结论。',
        minimum='建议保留四组真实输入的整次M14耗时，并同时记录K；按原计划先准备P95/max边界。',
        extension='单独为精算子核增加计时、更多K点及精细趋势拟合，可在整次收益确认后再做；缺少这些不阻塞最小方案验证。',
        order='实验1的基本收益结论之后推进，可与工程验收共用输入。'),
      'debug-comparison':dict(level='可做可不做',kind='辅助诊断 / 开销量化',
        reason='量化debug开销通常不改变生产方案选择；生产版本关闭debug，已有数值证据可服务主线。',
        minimum='本组不作为主研究完成条件；不必专门新增bit或整夜RTL，只为量化debug开销。',
        extension='只有发现debug与生产数值差异、需要解释旧debug周期，或需要日后调试工具时再做。必要的精算正确性检查仍保留在实验1/4和既有数值验收中。',
        order='默认延后，主线与必要验收完成后有需要再做。'),
      'state-reuse':dict(level='必须完成',kind='decode可用性 / 最低工程验收',
        reason='研究目标是连续decode。只对固定输入反复调用，无法证明换hidden/history后仍使用本步数据，旧候选或旧token残留会使速度结果失去意义。',
        minimum='至少验证A→B→A的不同输入切换和一段真实history推进序列，每步与独立CPU参考比较；保留输入/结果身份。',
        extension='所有语言各跑完整16步、更多长序列与极端历史组合属于覆盖扩展，可后续追加。这里要求最低连续调用正确性，不要求无限扩充测试矩阵。',
        order='在宣称支持连续decode及发布最终速度结论前完成；先离线参考，再RTL/获准实板。'),
      'policy-comparison':dict(level='建议完成',kind='策略解释 / 边界回归',
        reason='有助于定位history、正负分数和同分规则错误；当前已有冻结数值合同与组件检查，不必把每种策略组合都扩成整套系统实验。',
        minimum='建议用轻量CPU/子核夹具补正分、负分、同分和位图边界。生产penalty1.1与global history的基本语义仍必须正确。',
        extension='penalty关闭、p=1.0及更多人工分数组合可按缺口追加；不强制为每个组合另做生产bit。',
        order='优先复用轻量回归，异常出现时提高优先级。'),
      'error-comparison':dict(level='建议完成',kind='鲁棒性覆盖 / 故障定位',
        reason='完整异常注入矩阵用于提高鲁棒性，不直接回答稀疏方案质量/速度优劣。已有Csim拒绝与门控证据，不应无差别地重复到每个层级。',
        minimum='建议按新增路径和风险选取代表性注入；已有地址/容量/CRC/超时拒绝等基础保护不能删除，失败不得继续或发布旧token。',
        extension='将全部24项预检/5项运行错误在大规模RTL和实板逐项重跑可延后；如果某项保护未被证明或发生真实异常，则对应项转为本轮必须验收。',
        order='围绕实现变更补覆盖，不以完整异常矩阵阻塞核心算法对照。'),
      'transfer-comparison':dict(level='必须完成',kind='实板数据可信性 / 最低工程验收',
        reason='若不能证明权重/输入真实进入PL DDR且DMA已安全交接，板端正确性与性能数据都不可信。',
        minimum='上板阶段必须核对镜像/权重身份、目标PL DDR块与整份CRC/sentinel、配套软件及GEM停机条件；验证失败必须阻断测试。',
        extension='大量TCP分片组合、反复断线恢复、加载吞吐专项调优属于扩展，可按需要追加；最低加载与交接验收不能省。',
        order='未来上板的前置门槛；当前暂不上板，不因标为必须就自动连接或探测板卡。')}
    for g in v['comparisons']:g['importance']=definitions[g['id']]
    v['importance_policy']=[['必须完成','直接支撑研究结论，或保证该结论可信的最低工程验收。先完成标注的最低范围，不等于所有扩展都必须跑。'],['建议完成','有助于解释性能、定位错误或增强覆盖；可复用已有证据，资源有限时安排在核心主线之后。'],['可做可不做','辅助性议题，可延后或取消，不阻塞主研究；对应基本正确性要求仍由必要验收覆盖。']]
    v['updated']=datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S Asia/Shanghai')
    v['summary'][-1]=['重要性分级','必须3组 / 建议3组 / 可选1组；与完成状态分开']
    id='20261022-v4-experiment-importance'
    if not any(x['id']==id for x in d['entries']):d['entries'].append(dict(id=id,date='2026-10-22',title='按核心研究与最低工程验收给七组实验标注重要性',status='已验证',importance='重要成果',
        summary='必须：实验1质量/速度方案决策、实验4最低连续decode正确性、实验7最低加载/交接可信性；建议：实验2/5/6；可选：实验3 debug开销量化。每组写明原因、最低范围、扩展与顺序。',
        attempt='按用户要求区分研究核心、辅助分析和验证覆盖，避免将所有场景都当成相同优先级。',problem='原页面只有进展状态，没有解释每组实验是否影响研究方案选择、是否阻塞最低工程验收。',
        solution='左侧与详情同时显示三档重要性，增加重要性筛选；把必须的最低范围和可以延后的扩展拆开说明，保留所有历史结果。',
        verification='仅文档/数据/链接与JS语法静态检查；不启动GPU/RTL或操作板卡。',next='优先实验1与4的必要离线准备；实验7等未来用户允许上板后验收；实验3默认延后。',
        tags=['v4','重要性','研究主线','验收范围'],related=['20261022-v4-quality-speed-merged-gpu-reference'],evidence=[dict(label='重要性与实验范围',href='doc/design/V4Validation.html#quality')]))
    assert d['entries'][:len(previous)]==previous
    d['presentation']['checks']='保留既有历史，新增实验重要性说明；静态数据/链接/JS语法检查。未做file://视觉验收，未运行新增实验。'
    s=s[:m.start(2)]+'\n'+json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False).replace('<',r'\u003c')+'\n'+s[m.end(2):];p.write_text(s,encoding='utf-8')
    sys.path.insert(0,str(ROOT/'tools'));import render_v4_validation;render_v4_validation.render()
    print('IMPORTANCE=UPDATED must3/recommended3/optional1; history preserved; no experiment execution')
if __name__=='__main__':main()
