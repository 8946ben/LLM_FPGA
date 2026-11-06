"""Add progress prints only to a generated C-TB copy, preserving original."""
from pathlib import Path
root = Path(__file__).resolve().parents[2]
p = root / 'build/frequency_200_20261016/reduce_layers/cosim/solution1/sim/wrapc/kernel_equivalence.cpp_pre.cpp.tb.cpp'
backup = p.with_suffix(p.suffix + '.before_debug')
if backup.exists(): raise SystemExit('Preserve existing debug backup')
s = p.read_text()
backup.write_text(s)
s = '#include <cstdio>\n' + s
s = s.replace('int main() {', 'int main() {\n    std::fprintf(stderr, "DEBUG_CTB_MAIN_ENTER\\n");', 1)
s = s.replace('    lm_head_v2(', '    std::fprintf(stderr, "DEBUG_CTB_TOP_CALL\\n");\n    lm_head_v2(', 1)
p.write_text(s)
print(p)
