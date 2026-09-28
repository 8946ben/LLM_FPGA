# ip_repo

`lm_head_argmax/` 是 Vitis HLS 2021.1 的 `export_design -format ip_catalog`
输出，VLNV 为：

```text
xilinx.com:hls:lm_head_argmax:1.0
```

目录包含 `component.xml`、Verilog/VHDL、约束、xgui 和 standalone/Linux
驱动。它来自官方导出 ZIP 的干净解包结果，没有携带 HLS/Vivado 临时工程、
`.Xil`、journal 或 log。

在 Vivado 中将本目录加入 IP repository：

```tcl
set_property ip_repo_paths [list <module>/ip_repo] [current_project]
update_ip_catalog
```

随后可运行 `../vivado/create_lm_head_axu9eg_bd.tcl`。

