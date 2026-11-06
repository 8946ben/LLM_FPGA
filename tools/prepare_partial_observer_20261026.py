from pathlib import Path
import json,hashlib,re,tarfile
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4'
E=M/'experiments/perf_observer_20261026';R=M/'reports/perf_observer_20261026_r1'
RTL=M/'reports/partial_hw_20261024_r1/r3/remote_hls/syn/verilog/lm_head_v4_partial_proto.v'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 R.mkdir(exist_ok=True);assert not (R/'PLAN.json').exists()
 names=['grp_p_anonymous_namespace_select_channels_fu_308','grp_lm_head_v4_partial_proto_Pipeline_write_dims_fu_329','grp_p_anonymous_namespace_partial_preview_fu_338','grp_p_anonymous_namespace_radix_candidates_fu_362','grp_lm_head_v4_candidate_1_fu_369']
 signals={s:'{'+','.join(n+'_ap_'+s for n in reversed(names))+'}' for s in ['start','done','idle']}
 maps=dict(clk='ap_clk',rst_n='ap_rst_n',top_start='ap_start',top_done='ap_done',top_idle='ap_idle',st_start=signals['start'],st_done=signals['done'],st_idle=signals['idle'],status='status')
 for pfx,bus in [('w','weights'),('m','meta')]:
  for field in (['arvalid','arready','rvalid','rready'] if pfx=='w' else ['arvalid','arready','rvalid','rready','awvalid','awready','wvalid','wready']):maps[pfx+'_'+field]='m_axi_'+bus+'_'+field.upper()
 text=RTL.read_text()
 for value in maps.values():
  for name in re.findall(r'\b\w+\b',value):assert re.search(r'\b'+name+r'\b',text),name
 bind='bind lm_head_v4_partial_proto lmh_stage_observer lmh_observer(\n'+',\n'.join(' .{}({})'.format(k,v) for k,v in maps.items())+'\n);\n'
 (E/'stage_bind.sv').write_text(bind)
 expected=[dict(frame=1,stage=0,cycles=6,weight_reads=2,meta_reads=2,meta_writes=2,weight_ar_stall=3,status=0),
           dict(frame=1,stage=-1,cycles=8,weight_reads=2,meta_reads=2,meta_writes=2,weight_ar_stall=3,status=0),
           dict(frame=2,stage=3,cycles=3,weight_reads=2,meta_reads=0,meta_writes=0,weight_ar_stall=0,status=0),
           dict(frame=2,stage=-1,cycles=5,weight_reads=2,meta_reads=0,meta_writes=0,weight_ar_stall=0,status=0),
           dict(frame=3,stage=-1,cycles=2,weight_reads=0,meta_reads=0,meta_writes=0,weight_ar_stall=0,status=1)]
 (E/'expected_unit.json').write_text(json.dumps(expected,indent=2)+'\n')
 (E/'README.md').write_text('''# 仿真阶段与AXI被动计数器

无输出驱动、无DUT修改、无综合；只记录仿真边沿。阶段0通道选择/1通道ID写回/2预览/3Top-T/4精算，stage=-1为整次M14。

周期定义为ap_start首次上升到实际busy之后ap_done的采样边沿差，包含启动及AXI等待；idle-high done不算完成。不是HLS纯运算延迟。各阶段可有边界重叠，不能默认相加等于整次调用。

weight_reads/meta_reads/meta_writes计VALID&&READY数据拍；ar/aw/w stall计VALID&&!READY；weight_r_backpressure计RVALID&&!RREADY。它们是事件分类，不是物理DDR带宽推断。

本入口验证三次调用、空闲done高、不同阶段与错误返回的计数重置；随后仅展开真实冻结RTL验证bind可用，绝不运行完整模型或更改正在运行的前5块验证。自动重启连续ap_start高不在本观察器当前资格内。

强压力测试计数不换算正常decode。未来性能运行需另冻存储模型、输入、时钟、生产模式、K与计时范围；固定5ns仿真时钟不是200MHz布局布线资格。
''',encoding='utf-8')
 plan=dict(state='FROZEN_PASSIVE_STAGE_OBSERVER_ENTRY',stages=['channel_selection','write_dims','preview','top_t','exact'],
  scope='Observer unit simulation and actual frozen RTL bind elaboration only; no full RTL/implementation/board',
  top_rtl_sha256=sha(RTL),source_sha256={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in E.iterdir() if p.is_file()},
  actual_bind_has_no_outputs=True,automatic_next_stage=False,board='NOT_RUN')
 (R/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
 with tarfile.open(R/'entry.tar.gz','w:gz') as t:
  for p in list(E.iterdir())+[R/'PLAN.json']:t.add(p,arcname=str(p.relative_to(ROOT)))
 print(json.dumps(dict(archive=str(R/'entry.tar.gz'),sha256=sha(R/'entry.tar.gz'))))
if __name__=='__main__':main()
