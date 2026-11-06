"""Derive a new BD script from the accepted topology, never edit/reset it."""
from pathlib import Path
import hashlib, json

HERE = Path(__file__).resolve().parent
MODULE = HERE.parents[1]
OUT = HERE / 'physical_200'
SOURCE = MODULE / 'board/create_m14_v2_single_bd.tcl'


def main():
    OUT.mkdir(exist_ok=True)
    target = OUT / 'create_bd.tcl'
    if target.exists(): raise SystemExit('Preserve existing generated physical script')
    source = SOURCE.read_text(encoding='utf-8')
    begin = source.index('set script_dir ')
    end = source.index('set project_name ', begin)
    project = MODULE / 'board/build/m14_v2_200_layers'
    ip = MODULE / 'build/frequency_200_20261016/reduce_layers/csynth/solution1/impl/ip'
    replacement = (f'set project_dir {{{project.as_posix()}}}\n'
                   f'set ip_repo {{{ip.as_posix()}}}\n'
                   'if {[file exists $project_dir]} {error "Preserve existing 200 MHz project"}\n\n')
    source = source[:begin] + replacement + source[end:]
    for before, after in [
        ('set project_name "m14_v2_single"', 'set project_name "m14_v2_200_layers"'),
        ('set design_name "m14_v2_system"', 'set design_name "m14_200_system"'),
        ('create_project -force $project_name', 'create_project $project_name'),
        ('CONFIG.PSU__CRL_APB__PL0_REF_CTRL__FREQMHZ {100}',
         'CONFIG.PSU__CRL_APB__PL0_REF_CTRL__FREQMHZ {200}'),
        ('CONFIG.PSU__CRL_APB__PL0_REF_CTRL__DIVISOR0 {4}',
         'CONFIG.PSU__CRL_APB__PL0_REF_CTRL__DIVISOR0 {2}'),
        ('rst_ps8_0_100M', 'rst_ps8_0_200M'),
        ('A single 100 MHz PL clock domain', 'A single 200 MHz PL clock domain'),
    ]:
        assert source.count(before) == 1, before
        source = source.replace(before, after)
    source = ('# DIAGNOSTIC 200 MHz BD. Old build_config retained: DO NOT PROGRAM BOARD.\n' + source)
    checks = r'''
set actual [get_property CONFIG.PSU__CRL_APB__PL0_REF_CTRL__ACT_FREQMHZ $ps]
if {$actual < 199.9 || $actual > 200.1} {error "PL0 actual frequency not approximately 200 MHz: $actual"}
puts "M14_200_DIAGNOSTIC_BD_CREATED_ACTUAL_MHZ=$actual"
'''
    source = source.replace('close_project\nexit', checks + '\nclose_project\nexit', 1)
    target.write_text(source, encoding='utf-8')
    (OUT / 'template_identity.json').write_text(json.dumps({
        'template':str(SOURCE.relative_to(MODULE)),
        'template_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'generated_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
        'project':str(project), 'ip':str(ip), 'board_usable':False,
        'changes':['new paths/names', 'PL0 requested 200MHz and divisor0=2', 'reset name',
                   'refuse overwrite', 'verify actual PL0 frequency'],
        'unchanged':['DDR settings','AXI topology','address mapping','PS peripherals']
    },indent=2)+'\n',encoding='utf-8')
    print(target)


if __name__ == '__main__': main()
