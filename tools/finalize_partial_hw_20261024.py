from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'module_14_lm_head_v4/reports/partial_hw_20261024_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
class Page(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.resources=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='a' and a.get('href'):self.links.append(a['href'])
        if tag in ['script','img','iframe'] and a.get('src'):self.resources.append(a['src'])
        if tag=='link' and a.get('href'):self.resources.append(a['href'])
def main():
    for revision,base in [('r1',R),('r2',R/'r2'),('r3',R/'r3')]:
        for name,h in read(base/'PLAN.json')['source_sha256'].items():assert sha(ROOT/name)==h,(revision,name)
    after=read(R/'PROCESS_AFTER.json');assert after['state']=='PASS_REMOTE_TASK_STOPPED_SOURCE_SHA_UNCHANGED' and not after['owned_child_process_group_members']
    page=ROOT/'doc/design/V4PartialHardware.html';p=Page();p.feed(page.read_text(encoding='utf-8'));assert not p.resources
    for link in p.links:
        u=urlsplit(link);assert not u.scheme;target=(page.parent/unquote(u.path)).resolve();assert target.exists(),target
    result=read(R/'RESULT.json');assert sha(page)==result['page_sha256']
    assert result['state']=='CSIM_PASS_HLS_ESTIMATE_PASS_RTL_PENDING'
    for name,h in result['evidence_sha256'].items():assert sha(R/name)==h,name
    qa=dict(state='PASS_SOURCE_LOCK_REPORT_SHA_LOCAL_LINKS',page_sha256=sha(page),local_links=len(p.links),external_dependencies=0,
        source_counts={revision:len(read(base/'PLAN.json')['source_sha256']) for revision,base in [('r1',R),('r2',R/'r2'),('r3',R/'r3')]},
        browser_visual='NOT_RUN',all_stages_terminal=after['checks'],qa_source_sha256=sha(Path(__file__)))
    (R/'PAGE_REVIEW.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    result['final_artifact_sha256']={x:sha(R/x) for x in ['PAGE_REVIEW.json','NAVIGATION_REVIEW.json','PROCESS_AFTER.json']}
    result['publication_source_sha256']={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in [Path(__file__),ROOT/'tools/publish_partial_hw_20261024.py',ROOT/'tools/review_partial_hls_20261024.py',ROOT/'tools/review_partial_hw_20261024.py',ROOT/'tools/render_v4_validation.py']}
    (R/'RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    roadmap=ROOT/'doc/design/V4_NEXT_TASKS_20261024.md';text=roadmap.read_text(encoding='utf-8')
    text=text.replace('当前：阶段A质量/全557补测与阶段B布局/Top-T离线评审已完成。阶段C最小Csim/HLS原型尚未运行；没有自动EDA或板卡下阶段。','当前：阶段A/B与阶段C最小Csim/HLS原型已完成。STHL HLS2022.2 r3数值与综合估计门槛通过，RTL/200MHz实现/板卡仍未运行；没有自动下阶段。')
    text=text.replace('## 4. 阶段C：下一个有限任务','## 4. 阶段C：已完成的有限原型任务')
    text=text.replace('只实现d64/Top4096一个主候选；d128仅保留接口容量余量，不同时综合第二套完整系统。','实际结果见[STHL原型报告](V4PartialHardware.html)：r1接口综合失败保留；r2数值通过但10.383ns/候选II14；r3用片上键/ID缓存分离读写后，11次完整Csim及6错误门控通过，关键路径估计3.650ns、预览II1/直方图II2/候选II2，BRAM18K444/DSP179/FF129572/LUT52680。两master64位地址/128位数据。工具2022.2单列，不等于真实200MHz时序或decode速度。\n\n仅实现d64/Top4096一个主候选；d128仍是质量备选。下列为本阶段执行要求记录：')
    text=text.replace('交付：冻结入口、隔离源码、Csim逐位证明、HLS报告、阶段成本和继续/停止结论。当前该阶段NOT_RUN。','交付已完成：冻结入口、隔离源码、11次Csim逐位证明、HLS原始报告、r1/r2失败与r3阶段对照。STHL全部所属进程已退出，锁不存在，110/116/123份源与输入SHA核验不变。')
    text=text.replace('## 5. 后续系统与板卡阶段','## 5. 下一阶段：分段RTL、完整系统与板卡')
    text=text.replace('最小原型通过后再做完整RTL逐位核对→新私有IP/200MHz实现与STA/CDC/DRC→匹配bit/XSA/PS init/BSP/ELF/loader与SHA离线包。每阶段以真实产物为准，不继承旧核资格。','先验证选择器/预览块及精算有界FIFO的分段RTL，覆盖全平局/重复桶、跨4KiB、AXI背压、A→B→A；不能把Csim无界队列峰值当成实际FIFO深度依据。分段仅是定位手段，之后仍需一次完整配置联合RTL及全数值核对，再新私有IP/200MHz实现与STA/CDC/DRC。新系统使用与2022.2 XSA匹配的工具链/BSP/ELF/loader及新身份，不混用旧2021.1 bit/XSA/软件。每阶段以真实产物为准，不继承旧核资格；当前未启动RTL或实现。')
    roadmap.write_text(text,encoding='utf-8')
    print(json.dumps(dict(state=qa['state'],links=len(p.links),source_locks=qa['source_counts'])))
if __name__=='__main__':main()
