# Driver integration

`lm_head_v2_driver.h` defines the logical M14 V2 job/result contract and
`lm_head_v2_driver.c` performs checks that do not depend on the board memory
map. `lm_head_v2_mmio.c` maps that contract to the Vitis HLS generated driver,
waits with a finite polling budget, reads every result/counter, and checks the
production invariants. M03 remains responsible for DDR-region bounds,
capacity, alias, generation, and cache ownership.

After IP export, use Vitis HLS generated `xlm_head_v2.h` and
`xlm_head_v2_hw.h` as the only source of register offsets. The system wrapper
is included by `lm_head_v2_mmio.h`; numeric offsets are not copied into this
directory. Vitis HLS 2021.1 names the logical hidden pointer
`hidden_offset` and the hidden-size scalar `hidden_size_r`.

Before start, the wrapper must:

1. validate descriptors and 64-byte alignment;
2. clean only CPU-dirty hidden/history ranges;
3. avoid re-cleaning the immutable 259.7 MiB weight on every job;
4. program all address high/low words before scalar controls;
5. write `ap_start` last;
6. read status/counters after completion;
7. invalidate logits only when `write_logits=1` and the CPU will read them.
