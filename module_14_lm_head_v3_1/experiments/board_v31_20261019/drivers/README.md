# Driver integration

`lm_head_v2_driver.h` defines the logical M14 V2 job/result contract and
`lm_head_v2_driver.c` validates this v3.1 image's active buffer spans within
the PL DDR system window `[0x400000000, 0x480000000)`, including end overflow
and integer wrap, and rejects PS DDR or legacy local-offset pointers.
`lm_head_v2_mmio.c` maps that contract to the Vitis HLS generated driver,
waits with a finite polling budget, reads every result/counter, and checks the
production invariants. M03 remains responsible for the per-allocation bounds,
capacity, alias, generation, layout and ownership of a future integrated system.
The local aperture check does not establish those system-wide properties.

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

For this standalone A53 software, PL DDR is Normal Non-cacheable. A53 and
HLS use the same complete 64-bit address; MIG receives the low 31 bits.
Calibration is checked with a finite timeout before memory access. TCP CRC
verification reads the actual PL DDR target through aligned volatile 64-bit
loads into a 16 KiB PS scratch buffer; this is not a PS DDR compute fallback.
PS code, stack, heap, TCP receive buffers and mailbox may remain in PS DDR.
