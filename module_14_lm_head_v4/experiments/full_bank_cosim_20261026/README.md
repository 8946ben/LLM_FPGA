# 分bank模型下的一次完整联合验证

仅当本轮前5块独立VCD审计、观察器审计、原C后检查正负控制均通过，并确认前5块进程退出后，才允许手动执行run_full.py。入口不会自动等待或自动启动下一阶段。

复用原HLS生成的XSIM测试台、原随机停顿、原RTL/IP/有限FIFO、原完整TV与原cosim.pc.exe。仅替换已验证的仿真存储类、增加1522字节读回及无输出的被动观察器。AMD2022.2的config_cosim -setup支持生成后从命令外壳执行；此入口不再调用会覆盖修复模型的cosim_design生成步骤。

该入口报告“生成XSIM及C后检查实际通过”，不伪造cosim_design格式化报告PASS。后续仍需全数组独立重算及实际FIFO报告审计；只有这些完成才有完整工程资格。原full_r3的Fail和报告保持。

返回TV不包含工作区末尾额外guard；C后检查中的该guard是本地C数组哨兵，不能作为RTL越界证据。完整入口另绑定无输出AXI地址检查器，检查实际读/写范围、64位加法溢出、4KiB拆分、对齐/长度及只读权重写入；出现任何违反即失败。其7场景及真实RTL绑定审计是启动门槛。

fixtures只复制原输入，不放入任何预生成actual文件。C后检查通过后产生的actual还要与原始RTL返回TV对照。正控制参考输出只存在独立postcheck_control报告，不能混入本次实际证据。

强压力周期只分析阶段和AXI事件，不转写真实DDR/FPGA或整网decode速度。工具时限48小时，内存余量低于8GiB或STOP_REQUESTED时停止所属组。不会自动进入ABA、性能模型、综合、实现或板卡阶段。

官方选项说明：https://docs.amd.com/r/2022.2-English/ug1399-vitis-hls/config_cosim
