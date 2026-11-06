# 仿真阶段与AXI被动计数器

无输出驱动、无DUT修改、无综合；只记录仿真边沿。阶段0通道选择/1通道ID写回/2预览/3Top-T/4精算，stage=-1为整次M14。

周期定义为ap_start首次上升到实际busy之后ap_done的采样边沿差，包含启动及AXI等待；idle-high done不算完成。不是HLS纯运算延迟。各阶段可有边界重叠，不能默认相加等于整次调用。

weight_reads/meta_reads/meta_writes计VALID&&READY数据拍；ar/aw/w stall计VALID&&!READY；weight_r_backpressure计RVALID&&!RREADY。它们是事件分类，不是物理DDR带宽推断。

本入口验证三次调用、空闲done高、不同阶段与错误返回的计数重置；随后仅展开真实冻结RTL验证bind可用，绝不运行完整模型或更改正在运行的前5块验证。自动重启连续ap_start高不在本观察器当前资格内。

强压力测试计数不换算正常decode。未来性能运行需另冻存储模型、输入、时钟、生产模式、K与计时范围；固定5ns仿真时钟不是200MHz布局布线资格。
