"""Stage or seal a self-contained lm_head v3 handoff; preserve v2 delivery."""
from pathlib import Path
import argparse, copy, csv, difflib, json, re, shutil, subprocess, sys, zipfile
from package_delivery import sha, dump, copy_tree, registers, write_sums

M=Path(__file__).resolve().parents[1]; ROOT=M.parent
VERSION='M14_V3_20261019_r1'; MOD='module_14_lm_head_v3'
OUT=ROOT/'deliverables/20261019_M14_V3_r1'
BASE=ROOT/'deliverables/20261010_M14_V2_r1/M14_V2_20261010_r1'
E=M/'experiments/board200_20261019'; R=M/'reports/board200_20261019'

def stage():
    assert not OUT.exists(),'Preserve existing v3 staging directory'
    p=OUT/VERSION; m=p/MOD; m.mkdir(parents=True)
    for folder in ('src','include','drivers'): copy_tree(E/folder,m/folder)
    for folder in ('tb','reference','golden'): copy_tree(M/folder,m/folder)
    scripts=m/'scripts'; scripts.mkdir()
    names=('run_hls.ps1','run_csim.tcl','run_csynth.tcl','run_cosim.tcl','run_export_ip.tcl',
           'summarize_acceptance.py','regenerate_golden.py','analyze_board_logits.py')
    for name in names: shutil.copy2(M/'scripts'/name,scripts/name)
    summary_script=scripts/'summarize_acceptance.py'
    summary_script.write_text(summary_script.read_text(encoding='utf-8').replace('load_profile(campaign["package_dir"])','load_profile(campaign.get("package_dir"))'),encoding='utf-8')
    shutil.copy2(M/'scripts/validate_delivery_v3.py',scripts/'run_tests.py')
    for file in scripts.glob('*.tcl'):
        text=file.read_text(encoding='utf-8').replace('create_clock -period 10','create_clock -period 5.000')
        text=text.replace('config_interface -m_axi_addr64','set_clock_uncertainty 1.350\nconfig_interface -m_axi_addr64')
        file.write_text(text.replace('-version 2.0','-version 2.1'),encoding='utf-8')
    file=scripts/'run_hls.ps1'; text=file.read_text(encoding='utf-8')
    text=text.replace("'D:\\install\\Xilinx", "'G:\\Xilinx").replace('user_org_llm_fpga_lm_head_v2_2_0.zip','user_org_llm_fpga_lm_head_v2_2_1.zip')
    file.write_text(text,encoding='utf-8')
    standalone=m/'standalone'; standalone.mkdir()
    copy_tree(M/'standalone/src',standalone/'src')
    (standalone/'scripts').mkdir()
    for name in ('probe_retained_state.tcl','read_tcp_diagnostics.tcl','recover_debug_access.tcl',
                 'run_step.tcl','start_tcp_loader.tcl','verify_weight_sentinels.tcl'):
        shutil.copy2(M/'standalone/scripts'/name,standalone/'scripts'/name)
    copy_tree(E/'loader',standalone/'tcp_loader')
    for name in ('board_profile.py','parse_mailbox.py','prepare_mailbox.py','program_board_tcp.ps1','run_step.ps1',
                 'run_negative.ps1','run_failure_regression.ps1','run_acceptance.ps1','upload_weight_tcp.py','test_tcp_loader_board.py'):
        shutil.copy2(M/'standalone'/name,standalone/name)
    edits=[]
    for file in standalone.glob('*.ps1'):
        before=file.read_text(encoding='utf-8-sig'); text=before
        text=text.replace('reports\\board_package_20261009','reports\\board_package_lm_head_v3').replace('reports\\tcp_loader_package_20261010','reports\\board_package_lm_head_v3')
        text=text.replace('192.168.8.190','192.168.0.190')
        text=text.replace("'C:\\Users\\ben\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe'",'$env:PYTHON')
        if '[string]$PythonExe=$env:PYTHON' in text or '[string]$PythonExe = $env:PYTHON' in text:
            if 'Get-Command python' not in text:
                anchor="$ErrorActionPreference='Stop'" if "$ErrorActionPreference='Stop'" in text else "$ErrorActionPreference = 'Stop'"
                assert anchor in text,file
                text=text.replace(anchor,anchor+"\nif (-not $PythonExe) {$PythonExe=(Get-Command python -ErrorAction Stop).Source}",1)
        file.write_text(text,encoding='utf-8')
        if text!=before: edits.append({'file':str(file.relative_to(m)),'reason':'default v3 profile/IP and portable Python discovery'})
    for name in ('upload_weight_tcp.py','test_tcp_loader_board.py'):
        file=standalone/name; file.write_text(file.read_text(encoding='utf-8').replace('192.168.8.190','192.168.0.190'),encoding='utf-8')
    software=(E/'build_software.ps1').read_text(encoding='utf-8')
    software=software.replace('$module=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)','$module=Split-Path -Parent $PSScriptRoot')
    software=software.replace("Join-Path $PSScriptRoot 'drivers", "Join-Path $module 'drivers")
    software=software.replace('"-I$PSScriptRoot\\drivers"','"-I$module\\drivers"')
    software=software.replace('"-I$PSScriptRoot\\loader"','"-I$PSScriptRoot\\tcp_loader"')
    software=software.replace('"loader\\$_"','"tcp_loader\\$_"')
    software=software.replace("$tool='G:\\Xilinx\\Vitis\\2021.1'","$tool='G:\\Xilinx\\Vitis\\2021.1'\nNew-Item -ItemType Directory -Force $run | Out-Null")
    (standalone/'build_software.ps1').write_text(software,encoding='utf-8')
    platform=(E/'platform.tcl').read_text(encoding='utf-8').replace('set module [file normalize [file join $here .. ..]]','set module [file normalize [file join $here ..]]')
    platform=platform.replace('set xsa [file join $module reports board200_20261019 hardware m14_v2_single.xsa]',
        'set xsa [file join $module reports rebuilt_hardware m14_v2_single.xsa]\nif {![file exists $xsa]} {set xsa [file join $module reports board_package_lm_head_v3 m14_v2_single.xsa]}')
    (standalone/'platform.tcl').write_text(platform,encoding='utf-8')
    # Board rebuild uses relative package paths and the exact 200 MHz PS/DDR configuration.
    board=m/'board'; board.mkdir()
    bd=(E/'create_bd.tcl').read_text(encoding='utf-8')
    bd=re.sub(r'set project_dir \{[^\n]+\}', 'set module [file normalize [file join [file dirname [info script]] ..]]\nset project_dir [file join $module board build m14_board200_20261019]',bd,count=1)
    bd=re.sub(r'set ip_repo \{[^\n]+\}', 'set ip_repo [file join $module ip_repo lm_head_v2]\nset rebuilt [file join $module build lm_head_v2_export solution1 impl ip]\nif {[file exists [file join $rebuilt component.xml]]} {set ip_repo $rebuilt}',bd,count=1)
    (board/'create_bd.tcl').write_text(bd,encoding='utf-8')
    build=(E/'build.tcl').read_text(encoding='utf-8').replace('set module [file normalize [file join $here .. ..]]','set module [file normalize [file join $here ..]]').replace('reports board200_20261019 hardware','reports rebuilt_hardware')
    (board/'build.tcl').write_text(build,encoding='utf-8')
    (board/'run_vivado.ps1').write_text('''param([ValidateSet('create_bd','build')][string]$Action='create_bd', [string]$Vivado='G:\\Xilinx\\Vivado\\2021.1\\bin\\vivado.bat')
$ErrorActionPreference='Stop'
$module=Split-Path -Parent $PSScriptRoot
$run=Join-Path $module 'build\\vivado_launch'
New-Item -ItemType Directory -Force $run | Out-Null
Push-Location $run
try { & $Vivado -mode batch -source (Join-Path $PSScriptRoot "$Action.tcl") -log "$Action.log" -journal "$Action.jou"; if($LASTEXITCODE -ne 0) {throw 'Vivado stage failed'} } finally {Pop-Location}
''',encoding='utf-8')
    # Exact exported 2.1 IP; exclude only packaging temporaries, not referenced runtime files.
    exported=M/'build/board200_20261019/hls/solution1/impl/ip'; ip=m/'ip_repo/lm_head_v2'; ip.mkdir(parents=True)
    for folder in ('constraints','doc','drivers','example','hdl','misc','subcore','xgui'):
        if (exported/folder).exists(): copy_tree(exported/folder,ip/folder)
    for name in ('component.xml','auxiliary.xml','lm_head_v2_info.xml','sysgen_info.xml'):
        if (exported/name).exists(): shutil.copy2(exported/name,ip/name)
    generated=next((ip/'drivers').glob('*/src')); shutil.copytree(generated,m/'drivers/generated')
    reports=m/'reports'; reports.mkdir()
    copy_tree(R/'package',reports/'board_package_lm_head_v3')
    copy_tree(R/'baseline_100_package',reports/'baseline_100_package')
    copy_tree(M/'build/board200_20261019/hls/solution1/syn/report',reports/'hls')
    shutil.copy2(generated/'xlm_head_v2_hw.h',reports/'hls/xlm_head_v2_hw.h')
    shutil.copy2(exported/'component.xml',reports/'hls/component.xml')
    impl=reports/'implementation'; impl.mkdir()
    for f in (R/'hardware').iterdir():
        if f.suffix in ('.rpt','.dcp'): shutil.copy2(f,impl/f.name)
    accepted=reports/'board200_20261019'; accepted.mkdir()
    for f in R.iterdir():
        if f.is_file() and f.suffix in ('.json','.md','.log','.diff'): shutil.copy2(f,accepted/f.name)
    copy_tree(R/'build_logs',accepted/'build_logs')
    oldproof=M/'reports/frequency_200_20261016/reduce_layers'
    rtl=reports/'rtl'; rtl.mkdir()
    for name in ('RESULT.md','VALIDATION.json','hls_summary.json','native_validation.json','simulation_source_identity.json','tested_native_sources.json'):
        if (oldproof/name).exists(): shutil.copy2(oldproof/name,rtl/name)
    for name in ('rtl896.log','rtl896_vector_recovery.log'):
        src=M/'build/frequency_200_20261016/reduce_layers'/name
        if src.exists(): shutil.copy2(src,rtl/name)
    copy_tree(M/'experiments/frequency_200_20261016/reduce_layers/tests',m/'verification/reduce_layers_tests')
    shutil.copy2(M/'NUMERIC_CONTRACT.md',m/'NUMERIC_CONTRACT.md')
    # Original raw evidence stays byte-identical; only derivatives relocate paths.
    comparison=json.loads((R/'comparison.json').read_text(encoding='utf-8'))
    runs=reports/'board_runs'; runs.mkdir()
    campaigns=[]; relocations=[]
    for key,pkg in (('baseline_campaign','baseline_100_package'),('candidate_campaign','board_package_lm_head_v3')):
        path=Path(comparison[key]); campaign=json.loads(path.read_text(encoding='utf-8-sig'))
        dirs={path.parent}|{Path(r['source_run']) for r in campaign['records']}
        for directory in dirs: copy_tree(directory,runs/directory.name)
        portable=copy.deepcopy(campaign); portable['package_dir']='reports/'+pkg
        for row in portable['records']:
            old=row['source_run']; row['source_run']='reports/board_runs/'+Path(old).name
            row['profile_source']='reports/'+pkg+'/RUN_PROFILE.json'
            relocations.append({'original':old,'portable':row['source_run']})
        dest=runs/path.parent.name/'campaign_portable.json'; dump(dest,portable)
        campaigns.append(dest.relative_to(m).as_posix())
    for key in ('baseline_upload','candidate_upload'):
        directory=Path(comparison[key]); copy_tree(directory,runs/directory.name)
    copy_tree(ROOT/'artifacts/module14_v2_assets',p/'artifacts/module14_v2_assets')
    (p/'ref').mkdir(); shutil.copy2(ROOT/'ref/xemacpsif_physpeed.c',p/'ref/xemacpsif_physpeed.c')
    copy_tree(BASE/'specifications',p/'specifications')
    shutil.copy2(BASE/'requirements.txt',p/'requirements.txt')
    # Keep the mature interface documentation; update only current identity/results.
    copy_tree(BASE/'module_14_lm_head_v2/interface',m/'interface')
    manifest=json.loads((BASE/'module_14_lm_head_v2/module_manifest.json').read_text(encoding='utf-8'))
    hw=comparison['hardware']; perf=comparison['candidate']['performance']
    manifest.update(version=VERSION,release_name='lm_head v3',name='lm_head_v3',hardware_top='lm_head_v2',
        delivery_date='2026-10-19',target_clock_hz=200_000_000,build_config='0x20c08011',ip_vlnv='user.org:llm_fpga:lm_head_v2:2.1',
        ip_component_sha256=sha(ip/'component.xml'),portable_campaigns=campaigns,
        acceptance_metadata='reports/board200_20261019/comparison.json',
        hls={'dot_word_loop_ii':1,'reduce_layer_ii':[1,1,1],'estimated_clock_ns':3.650,'clock_uncertainty_ns':1.350,'top_latency_cycles':None},
        implementation={'scope':'full independent M14 BD','LUT':23148,'FF':40194,'BRAM_tile':22,'DSP':59,'WNS_ns':.943,'WHS_ns':.010,'WPWS_ns':1.0,'DRC_errors':0,'DRC_critical_warnings':0,'DRC_warnings':192,'actual_pl_clock_hz':199998001},
        performance=comparison['candidate'],tested_source_sha256={f'{folder}/{f.name}':sha(f) for folder in ('src','include','drivers') for f in (m/folder).iterdir() if f.is_file()})
    manifest['known_limitations']=[
        'Verified scope: independent M14 H896/V151936 Decode penalty ON; no whole-model token throughput claim.',
        'ABI remains 2 and hardware symbol lm_head_v2; v3 is the user-requested release name.',
        'Native M06 BF16/full-system integration and extended mode/address/extreme-value matrices are outside this release validation.',
        'PS clock registers/configuration and A53 elapsed time checked; no external frequency counter or HP2 APM measurement.',
        'Archived raw evidence retains historical absolute workspace paths; portable campaigns relocate paths only.']
    dump(m/'module_manifest.json',manifest)
    contract_path=m/'interface/interface_contract.json'; contract=json.loads(contract_path.read_text(encoding='utf-8'))
    contract['identity'].update(name='lm_head_v3',release_name='lm_head v3',hardware_top='lm_head_v2',revision=2,abi_version=2)
    contract['build_config']['value']='0x20c08011'
    contract['build_config']['decode']['clock'].update(encoded=3,decoded_hz=200_000_000)
    contract['build_config']['decode']['module_revision'].update(encoded=2,decoded=2)
    regs=registers(ip/'component.xml'); contract['control_registers']=regs
    contract['timeout'].update(worst_measured_single_ip_ms=perf['ip_ms_max'],worst_measured_single_a53_ms=perf['a53_wall_ms_max'],tested_1000_call_wall_seconds=comparison['candidate']['stability_wall_seconds'])
    contract['tests']['decode_T1_penalty_on']='2026-10-19 BOARD PASS: 8 production +8 full logits, 30 independent timing, 1000 repeats'
    dump(contract_path,contract)
    with (m/'interface/axi_lite_registers.csv').open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(regs[0])); writer.writeheader(); writer.writerows(regs)
    profile_path=m/'interface/hardware_profile_summary.json'; hp=json.loads(profile_path.read_text(encoding='utf-8'))
    hp.update(target_PL_clock_hz=200_000_000,reported_PL_clock_hz=199998001,release_name='lm_head v3',build_config='0x20c08011',reported_clock_basis='Vivado PS configuration model, not frequency-counter measurement')
    dump(profile_path,hp)
    dump(p/'provenance/identity_and_source_mapping.json',{'release_name':'lm_head v3','abi_version':2,'ip_vlnv':manifest['ip_vlnv'],
        'tested_build_config':'0x20c08011','hardware_rebuilt_for_rename':False,'hardware_access_during_packaging':False,
        'tested_artifacts':{name:sha(R/'package'/name) for name in ('m14_v2_system_wrapper.bit','m14_v2_single.xsa','m14_v2_test.elf','m14_tcp_loader.elf','psu_init.tcl')},
        'tested_source_sha256':manifest['tested_source_sha256'],'package_only_edits':edits})
    dump(p/'provenance/evidence_path_relocations.json',relocations)
    # User-edited v2 wording remains preserved in the old delivery. New documents describe v3.
    for name in ('README.md','BOARD_TEST_PLAN.md','DELIVERY_NOTES.md'):
        shutil.copy2(Path(__file__).parent/'v3_delivery'/name,m/name)
    shutil.copy2(Path(__file__).parent/'v3_delivery/README_交付入口.md',p/'README_交付入口.md')
    shutil.copy2(Path(__file__).parent/'v3_delivery/交付说明.md',p/'交付说明.md')
    (standalone/'README.md').write_text('# lm_head v3 板测\n\n使用本模块 README 的 TCP 加载与验收命令。默认均选择200 MHz冻结包和192.168.0.190。\n参数 -PackageDir 可明确选择基线包；切换版本需完整初始化。大权重始终优先网口，禁止默认JTAG传整份权重。\n',encoding='utf-8')
    (standalone/'TCP_WEIGHT_LOADING.md').write_text((standalone/'README.md').read_text(encoding='utf-8')+'\n修复版 tcp_output 重试保留。主机SHA256、逐块DDR CRC、全DDR CRC和JTAG sentinel通过后才启动IP；失败整份重传。\nPC有线192.168.0.12/24，板卡192.168.0.190/24，端口1414。测试ELF无lwIP，验收期间ping不响应属预期。\n',encoding='utf-8')
    print('LM_HEAD_V3_STAGING='+str(p),flush=True)

def seal():
    p=OUT/VERSION; m=p/MOD
    assert p.is_dir() and not (OUT/(VERSION+'.zip')).exists()
    catalog=OUT/'ip_catalog.log'
    catalog_text=catalog.read_text(encoding='utf-8-sig')
    assert '\nLM_HEAD_V3_IP_CATALOG=PASS' in catalog_text and '\nLM_HEAD_V3_IP_VLNV=user.org:llm_fpga:lm_head_v2:2.1' in catalog_text
    shutil.copy2(catalog,m/'reports/hls/delivery_ip_catalog.log')
    manifest=json.loads((m/'module_manifest.json').read_text(encoding='utf-8'))
    mappings=[]
    for folder in ('src','include','drivers'):
        for source in (E/folder).iterdir():
            if source.is_file(): mappings.append((source,m/folder/source.name))
    for source in (E/'loader').iterdir():
        if source.is_file(): mappings.append((source,m/'standalone/tcp_loader'/source.name))
    for source in (M/'standalone/src').iterdir():
        if source.is_file(): mappings.append((source,m/'standalone/src'/source.name))
    records=[]
    for source,target in mappings:
        assert sha(source)==sha(target),'Tested source differs: '+str(target)
        manifest['tested_source_sha256'][target.relative_to(m).as_posix()]=sha(target)
        records.append({'workspace_source':source.relative_to(ROOT).as_posix(),'delivery':target.relative_to(p).as_posix(),'sha256':sha(target)})
    dump(m/'module_manifest.json',manifest)
    provenance=json.loads((p/'provenance/identity_and_source_mapping.json').read_text(encoding='utf-8'))
    provenance['tested_source_sha256']=manifest['tested_source_sha256']; provenance['tested_source_mappings']=records
    provenance['package_only_edits'] += [
        {'file':'scripts/summarize_acceptance.py','reason':'Accept legacy 100 MHz unit-test fixtures lacking package_dir; 200 MHz still requires matching profile/build identity.'},
        {'file':'scripts/run_*.tcl','reason':'Use 5 ns /1.35 ns and IP 2.1; keep ABI/top symbols.'},
        {'file':'board/create_bd.tcl, board/build.tcl','reason':'Relocate verified 200 MHz configuration and IP repository to package-relative paths.'},
        {'file':'standalone/build_software.ps1, standalone/platform.tcl','reason':'Package-relative drivers/loader/reference PHY and matching rebuilt or frozen 200 MHz XSA.'}]
    dump(p/'provenance/identity_and_source_mapping.json',provenance)
    assert sha(ROOT/'deliverables/20261010_M14_V2_r1/M14_V2_20261010_r1.zip')=='215b7bf756c57e637fa2943baacef582307fc53db545a1a42f50aca7d76aa514'
    write_sums(m); write_sums(p)
    def verify(directory,log):
        result=subprocess.run([sys.executable,'-B',str(directory/MOD/'scripts/run_tests.py')],cwd=directory,capture_output=True,text=True)
        log.write_text(result.stdout+result.stderr,encoding='utf-8')
        if result.returncode: raise RuntimeError('Delivery check failed: '+str(log))
    verify(p,OUT/'STAGING_VALIDATION.log'); print('V3_STAGING_VERIFY=PASS',flush=True)
    archive=OUT/(VERSION+'.zip')
    tracked=[line.split('  ',1)[1] for line in (p/'SHA256SUMS').read_text(encoding='utf-8').splitlines()]+['SHA256SUMS']
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for name in tracked: z.write(p/name,VERSION+'/'+name)
    extracted=OUT/'verify_extracted'
    with zipfile.ZipFile(archive) as z:
        assert set(z.namelist())=={VERSION+'/'+name for name in tracked} and z.testzip() is None
        z.extractall(extracted)
    verify(extracted/VERSION,OUT/'EXTRACTED_VALIDATION.log'); print('V3_EXTRACTED_VERIFY=PASS',flush=True)
    result={'state':'PASS','release_name':'lm_head v3','version':VERSION,'archive':archive.name,'bytes':archive.stat().st_size,
        'sha256':sha(archive),'files':len(tracked),'staging_validation':'PASS','extracted_validation':'PASS',
        'hardware_access':False,'vivado_catalog_validation':'PASS','tested_sources_identical':True,'v2_archive_preserved':True,
        'note':'Preserved tested 200 MHz binaries; release rename and portable packaging only.'}
    dump(OUT/'DELIVERY_VALIDATION.json',result)
    (OUT/'ZIP_SHA256SUMS.txt').write_text(result['sha256']+'  '+archive.name+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=True,indent=2),flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser(); a.add_argument('action',choices=('stage','seal')); args=a.parse_args()
    stage() if args.action=='stage' else seal()
