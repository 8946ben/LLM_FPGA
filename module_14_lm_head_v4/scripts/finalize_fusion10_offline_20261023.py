"""Publish only actually completed Exp10 offline evidence; never a release."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json
M=Path(__file__).resolve().parents[1];ROOT=M.parent;X=M/'experiments/fusion_exp10_20261023';R=M/'reports/fusion_exp10_20261023_r1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def main():
    names=['CALIBRATION_REVIEW.json','GPU_REVIEW.json','FINAL_QUALITY_REVIEW.json','PUBLIC_SOURCE_RESERVATION_REVIEW.json','HLS_SYNTHESIS_AUDIT.json','HOST_QUALIFICATION.json','RTL_QUALIFICATION.json','EXPORT_QUALIFICATION.json','AXI_LOCK_WARNING_REVIEW.json','SYSTEM_BUILD_INPUT_AUDIT.json','RESUME_INPUT_AUDIT.json','SELECTOR_VIVADO_SYNTHESIS_RESOURCES.json','PRIVATE_IP_AUDIT.json','OFFLINE_PACKAGE_AUDIT.json'];reports={n:read(R/n) for n in names}
    for n,d in reports.items():assert d['state'].startswith(('PASS','PRIVATE_')),n
    for n,h in reports['SYSTEM_BUILD_INPUT_AUDIT.json']['input_sha256'].items():assert sha(X/n)==h,n
    for n,h in reports['RESUME_INPUT_AUDIT.json']['source_sha256'].items():assert sha(M/n)==h,n
    host=reports['HOST_QUALIFICATION.json']
    for n,h in host['source_sha256'].items():assert sha(X/n)==h,n
    entry=read(M/'data/fusion10_quality_20261023/EVALUATION_ENTRY_LOCK.json')
    for n,h in entry['source_sha256'].items():assert sha(M/n)==h,n
    derived=read(X/'MANIFEST.json')
    for n,h in derived['fixture_sha256'].items():assert sha(X/'fixture'/n)==h,n
    original_ip=read(M/'reports/SELECTOR_PRIVATE_IP_MANIFEST.json')
    for n,h in original_ip['files'].items():assert sha(M/original_ip['path']/n)==h,n
    for n,h in original_ip['source_sha256'].items():assert sha(M/n)==h,n
    original_bundle=M/'reports/board_v4_20261021/private_package_r1'
    for line in (original_bundle/'SHA256SUMS.txt').read_text().splitlines():
        h,n=line.split('  ',1);assert sha(original_bundle/n)==h,n
    q=read(R/'FINAL_QUALITY.json');assert q['state']=='QUALITY_FAIL_NO_RELEASE_NO_RETUNE'
    hwpath=X/'reports/board_v4_20261021/hardware_audit_r2.json';hw=read(hwpath);assert hw['state']=='PASS_OFFLINE_SYSTEM'
    lock=read(R/'SELECTION_LOCK.json');gpu=read(R/'GPU_BENCHMARK.json');selected=next(c for c in gpu['configurations'] if c['id']==lock['chosen']);baseline=next(c for c in gpu['configurations'] if c['id']=='frozen_hybrid');dense=next(c for c in gpu['configurations'] if c['id']=='dense');rtl=reports['RTL_QUALIFICATION.json'];now=datetime.now(timezone(timedelta(hours=8))).isoformat()
    result=dict(state='OFFLINE_TESTS_COMPLETED_QUALITY_FAIL_NO_RELEASE',updated=now,selected=lock['chosen'],parameters=lock['parameters'],calibration=dict(grid_points=432,groups=320,decode=4775,selected_misses=0),fresh_quality=dict(groups=1000,decode_steps=q['decode_steps'],selected=q['selected']['report'],frozen_baseline=q['frozen_baseline']['report'],gate=False),gpu_reference=dict(timed_calls=1080,numeric_pairs=36,stability_calls=1000,stability_scope='Four fixed calibration inputs cyclically changed; not1000 distinct prompts/free generation',selected=selected,frozen_baseline=baseline,dense=dense,scope='Same-run fixed FP32 Eager reference, not optimized GPU/fullLLM/FPGA projection'),hls=reports['HLS_SYNTHESIS_AUDIT.json'],rtl=rtl,selector_vivado_synthesis=reports['SELECTOR_VIVADO_SYNTHESIS_RESOURCES.json'],hardware=hw,offline_package_audit_sha256=sha(R/'OFFLINE_PACKAGE_AUDIT.json'),report_sha256={n:sha(R/n) for n in names},board='NOT_RUN',whole_llm_decode='NOT_RUN',ttft='NOT_RUN',next='Keep frozen baseline; this locked point failed quality. Any new method/parameters require a new predeclared calibration/selection and untouched final cohort; no retune/re-certify this opened cohort. Board operation remains outside current authorization.')
    (R/'RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    text=['# 实验10：融合超参数的完整离线测试结果','','状态：**离线测试完成；锁点质量失败，不发布**。本轮没有连接、探测或操作FPGA。','',f'参数：`{lock["chosen"]}`。预先锁定432点，复用旧train1500，只用calibration320/4775decode选型。门槛、成本目标及新问题在产生标签前冻结。','', '| 新独立1000题 /14986 decode | 漏选 | dense赢家覆盖率 |','| --- | ---: | ---: |']
    for key,label in [('selected','实验10锁点'),('frozen_baseline','预声明冻结融合对照')]:
        d=q[key]['report']['decode'];text.append(f'| {label} | {d["misses"]} | {d["recall"]*100:.4f}% |')
    text+=['','锁点中文11/6000、英文7/3736、代码0/960、数学1/4290。整体及中英未达到99.9%拟议点门槛。校准零漏选没有推广到新问题；不根据本测试组回调参数。','',f'同轮GPU参考局部输出率：锁点{selected["equivalent_m14_per_s"]:.3f}、冻结融合{baseline["equivalent_m14_per_s"]:.3f}、dense{dense["equivalent_m14_per_s"]:.3f}次/s。仅4个固定校准输入、每组合3预热+30计时，共1080计时；36完整候选/raw/token/score/CRC证明，以及4输入轮换1000功能调用通过。不是整网decode或FPGA预测。','',f'HLS估计3.650ns，153BRAM18K/231DSP。真实Csim5次四类/生产/A→B→A调用+2验证命令，24预检拒绝/5运行错误；37项Python/Tcl宿主测试、25项fake-MMIO、88组loader对齐/长度组合通过。','', '| 完整RTL事务 | 周期 | 200MHz AXI模型耗时 / ms |','| --- | ---: | ---: |']
    for c,label in zip(rtl['transactions'],['真实中文debug、K17764','重叠拒绝']):text.append(f'| {label} | {c["cycles"]} | {c["model_ms_at200MHz"]:.6f} |')
    text+=['','selector单IP Vivado综合资源：49914 LUT、75623寄存器、53 BRAM Tile、231 DSP；这是单IP综合值，区别于HLS估计及完整系统布局布线资源。','', 'RTL完成41943040内存值/18标量逐位检查及原生成C后校验。周期只属于单固定输入、debug与仿真AXI模型；不是整体问题分布、生产模式、实际MIG或板测token/s。','',f'完整200MHz系统：WNS {hw["wns_ns"]:+.3f}ns、WHS {hw["whs_ns"]:+.3f}ns、WPWS {hw["wpws_ns"]:+.3f}ns；内部未约束端点/CDC Critical/MIG警告均0。其余DRC计数：{hw["drc_severity_counts"]}；不宣称零警告。','', '两条64位AXI计算通路均只到PL DDR；新bit/XSA、同XSA PS初始化、实际BSP编译两ELF、真实GEM基址/PHY、四类320MiB本地镜像与研究包SHA已核验。不是正式可移交发布ZIP。', '', '保留首轮Windows260路径失败、PowerShell R/r解析故障、宿主共享源路径/身份修正、短克隆导出暂存遗漏、导出选项语法、2026生成元数据整数溢出、BD实例旧VLNV引用修复及原始日志。数值入口/锁点与已打开质量组不变；原冻结v4/private_package及v2/v3/v3.1封存不改。','', '板卡目标加载/CRC、30次板测、1000次板上稳定性、整网decode及TTFT均NOT_RUN。']
    (R/'RESULT.md').write_text('\n'.join(text)+'\n',encoding='utf-8')
    status=dict(stage='OFFLINE_TESTS_COMPLETE_QUALITY_FAILED_NOT_RELEASE',updated=now,holdout_read=True,quality=q['state'],board='NOT_RUN',active_work='None; no automatic new studies, board jobs, WB or heartbeat',result='RESULT.json')
    for name in ['PROGRESS.json','EDA_PROGRESS.json']:(R/name).write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    block='\n## 实验10全部离线测试已结束（当前最高优先级）\n\n'+f'- 完成时间：{now}。事实源：module_14_lm_head_v4/reports/fusion_exp10_20261023_r1/RESULT.json、RESULT.md。\n'+f'- 432点校准、1080次GPU计时/36完整数值对照/4夹具轮换1000调用、锁点新1000题、Csim/HLS/完整RTL/200MHz系统/匹配BSP两ELF及本地镜像/研究包已核验。锁点{lock["chosen"]}新decode漏19/14986、99.8732%，质量门槛失败；冻结融合对照漏2、99.9867%。工程通过不能替代质量通过，不发布锁点，不用此已打开组调参再认证。\n'+f'- RTL中文周期{rtl["transactions"][0]["cycles"]}仅debug+AXI模型；真实FPGA/整网decode/TTFT均NOT_RUN。200MHz WNS{hw["wns_ns"]:+.3f}ns。私有GPIO0x4D345A0A/descriptor_v2/tag0x8507826e与研究包绑定，不混用冻结旧包。\n'+'- 不操作板卡，不恢复wb/luyou/心跳，不改封存和冻结基线。此一次性流程已结束；不自动开始新实验。后续等待用户新的研究/独占板卡安排。下方所有活动PID/进行中/旧未开始文字均为历史。\n\n'
    for p in [ROOT/'AGENTS.md',ROOT/'doc/LM_HEAD_V4_HANDOFF_20261021.md']:
        old=p.read_text(encoding='utf-8-sig');head,rest=old.split('\n',1);p.write_text(head+'\n'+block+rest,encoding='utf-8')
    print(result['state'])
if __name__=='__main__':main()
