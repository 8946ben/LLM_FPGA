# M14 V2 single-module Vivado design

These scripts derive from the already validated AXU9EGB Module 16 design, with
the M14 V2 IP, 100 MHz PL clock, 128-bit M_AXI bundles, and PS
`S_AXI_HP2_FPD` data path required by the 0924 system plan.

Run only after HLS export has produced:

```text
module_14_lm_head_v2/build/lm_head_v2_export/solution1/impl/ip/component.xml
```

Then execute:

```powershell
$env:VIVADO_BIN = '<Vivado_2021.1>\bin\vivado.bat'
.\board\run_vivado.ps1 verify-ip
.\board\run_vivado.ps1 create
.\board\run_vivado.ps1 build
```

The create script asserts HP2 width 128. The build script writes post-synthesis
and post-route reports under `reports/board_build/`, plus an XSA containing the
bitstream. Review WNS, utilization, DRC, address segments, and the generated
HLS register map before creating the PS application.

These scripts create hardware artifacts only. They do not program the board.
