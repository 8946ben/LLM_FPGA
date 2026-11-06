
"""Build private experimental D64 package; does not connect to a board."""
from pathlib import Path
import json,hashlib,shutil,zipfile,re,datetime,zlib
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4'
D=ROOT/'deliverables/20261106_M14_D64_200M_r1';P=D/'M14_D64_200M_20261106_r1'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def copy(source,target):
 target=P/target;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
def main():
 route=M/'reports/d64_system_200m_20261106_r4';hw=M/'reports/d64_bit_xsa_20261106_r1';ps=M/'reports/d64_matching_ps_20261106_r6'
 rv=json.loads((route/'INDEPENDENT_ROUTE_REVIEW.json').read_text());hv=json.loads((hw/'INDEPENDENT_HARDWARE_REVIEW.json').read_text());pv=json.loads((ps/'INDEPENDENT_PS_REVIEW.json').read_text())
 assert rv['state']=='PASS_OFFLINE_ROUTE_WITH_EXPLICIT_FINDING_DISPOSITIONS_NOT_BOARD' and hv['state']=='PASS_BIT_XSA_IDENTITY_ONLY_NOT_BOARD' and pv['state']=='PASS_MATCHING_BSP_ELF_OFFLINE_NOT_BOARD'
 assert not D.exists();P.mkdir(parents=True)
 for name in ['m14_d64_200m.bit','m14_d64_200m.xsa']:copy(hw/'collected/hardware'/name,'hardware/'+name)
 with zipfile.ZipFile(P/'hardware/m14_d64_200m.xsa') as z:
  for name in ['psu_init.tcl','psu_init.c','psu_init.h','psu_init_gpl.c','psu_init_gpl.h']:
   (P/'hardware'/name).write_bytes(z.read(name))
 for name in ['m14_d64_loader.elf','m14_d64_test.elf']:copy(ps/'collected/software'/name,'software/'+name)
 image=M/'reports/d64_board_20261105_r1/pl_image_r1/d64_pl_576m.bin'
 manifest=M/'reports/d64_board_20261105_r1/pl_image_r1/MANIFEST.json';im=json.loads(manifest.read_text())
 assert sha(image)==im['image_sha256']=='6dc780c58540b21e1cf659126823205894b17f4cd1c3ab06e2489424c53815e9'
 copy(image,'data/d64_pl_576m.bin');copy(manifest,'data/MANIFEST.json')
 e=M/'experiments/d64_matching_ps_20261106_r6';copy(e/'ps/layout.json','data/layout.json')
 for source in e.rglob('*'):
  if source.is_file():copy(source,'source/'+str(source.relative_to(e)))
 copy(ROOT/'tools/review_d64_board_results_20261106.py','tools/review_d64_board_results.py');copy(e/'ps/upload_d64.py','tools/upload_d64.py')
 for source,name in [(route/'INDEPENDENT_ROUTE_REVIEW.json','ROUTE_REVIEW.json'),(route/'route/WORKFLOW.json','ORIGINAL_ROUTE_WORKFLOW.json'),(hw/'INDEPENDENT_HARDWARE_REVIEW.json','HARDWARE_REVIEW.json'),(ps/'INDEPENDENT_PS_REVIEW.json','PS_REVIEW.json'),(ps/'ELF_LAYOUT_AUDIT.json','ELF_LAYOUT_AUDIT.json'),(ps/'BSP_COPY_RECEIPT.json','BSP_COPY_RECEIPT.json'),(M/'reports/d64_board_20261105_r1/EXPORT_INDEPENDENT_REVIEW.json','IP_EXPORT_REVIEW.json'),(M/'reports/d64_system_200m_20261105_r1/BD_INDEPENDENT_REVIEW.json','BD_REVIEW.json'),(M/'reports/d64_board_20261105_r1/OFFLINE_PREPARATION_REVIEW.json','OFFLINE_IMAGE_HOST_REVIEW.json')]:
  if not source.exists():
   if source==ps/'BSP_COPY_RECEIPT.json':source=ps/'collected/BSP_COPY_RECEIPT.json'
   elif source==route/'route/WORKFLOW.json':source=route/'terminal_collection_r1/module_14_lm_head_v4/reports/d64_system_200m_20261106_r4/route/WORKFLOW.json'
  copy(source,'evidence/'+name)
 raw=route/'terminal_collection_r1/module_14_lm_head_v4/reports/d64_system_200m_20261106_r4/hardware'
 for source in raw.glob('*'):
  if source.is_file() and source.suffix in ['.rpt','.txt','.json']:copy(source,'evidence/raw_route/'+source.name)
 for source in (ps/'collected/bsp').rglob('*'):
  if source.is_file():copy(source,'evidence/bsp_audit/'+str(source.relative_to(ps/'collected/bsp')))
 for source in (ps/'collected/execution').rglob('*'):
  if source.is_file():copy(source,'evidence/ps_execution/'+str(source.relative_to(ps/'collected/execution')))
 scenarios=json.loads((M/'reports/d64_state_fixtures_20261104_r2/MANIFEST.json').read_text())['scenarios'];assert len(scenarios)==12
 refs=P/'references';refs.mkdir();(refs/'arrays').mkdir()
 expected=[]
 for s in re.findall(r'^\{([0-9u,]+)\},?$',(e/'ps/d64_cases.h').read_text(),re.M):
  row=[int(x.rstrip('u')) for x in s.split(',')];assert len(row)==10;expected.append(dict(zip(['debug','capacity','status','token','score','k','crc','mutation_offset','original','replacement'],row)))
 assert len(expected)==16
 with image.open('rb') as f:
  for i in range(16):
   f.seek(0x20900000+i*0x6000);b=f.read(24368);(refs/f'input_{i:02}.bin').write_bytes(b)
   if i<12:assert hashlib.sha256(b).hexdigest()==scenarios[i]['input_sha256']
 for fixture in sorted({s['fixture'] for s in scenarios}):
  for field in ['dims','preview','keys','ids','raw']:
   source=M/'experiments/partial_hw_20261024/fixtures'/(fixture+'.'+field+'.bin');shutil.copy2(source,refs/'arrays'/source.name)
 config=dict(image_sha256=im['image_sha256'],timer_counts_per_second=pv['timer_counts_per_second'],scenarios=scenarios,expected=expected,reference_sha256={str(p.relative_to(refs)).replace('\\','/'):sha(p) for p in refs.rglob('*') if p.is_file()})
 (refs/'CONFIG.json').write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
 (P/'README.md').write_text("# M14 \u52a8\u6001\u901a\u9053\u9884\u89c8\u4e0e\u5019\u9009\u7cbe\u7b97\uff1a200 MHz \u5b9e\u9a8c\u4e0a\u677f\u5305\n\n\u65b9\u6848\uff1a\u6309 |hidden|\u00d7\u901a\u9053 RMS \u9009\u62e9 64 \u4e2a\u901a\u9053\uff0c\u9884\u89c8\u5b8c\u6574\u8bcd\u8868\uff0c\u53d6 Top4096 \u5e76\u5408\u5165 14 \u4e2a\u7279\u6b8a ID\uff0c\u518d\u7528 canonical BF16 \u5b8c\u6574 896 \u7ef4\u6743\u91cd\u7cbe\u7b97\u5019\u9009\u3002\n\u8fd9\u662f T04 d64 \u8def\u7ebf\uff0c\u4e0d\u662f\u65e9\u671f\u7684\u805a\u7c7b\uff0b\u4f4e\u79e9\u65b9\u6848\u3002\n\n\u672c\u5305\u72b6\u6001\uff1a\u79bb\u7ebf\u5b9e\u73b0\u53ca\u5339\u914d\u8f6f\u4ef6\u6838\u9a8c\u901a\u8fc7\uff1b\u5c1a\u672a\u8fdb\u884c\u672c\u8f6e\u677f\u5361\u9a8c\u6536\u3002\u539f\u5b8c\u657412\u573a\u666f RTL \u56de\u5f52\u6309\u7528\u6237\u9009\u62e9\u505c\u6b62\uff0c\u4fdd\u6301\u201c\u672a\u5b8c\u6210\u201d\u3002\u672c\u5305\u4e0d\u5f97\u4f5c\u4e3a\u7a33\u5b9a\u96c6\u6210\u7248\u6216\u6027\u80fd\u9a8c\u6536\u901a\u8fc7\u7248\u53d1\u5e03\u3002\n\n## \u5df2\u9a8c\u8bc1\u8303\u56f4\n- xczu9eg-ffvb1156-2-i\uff0c\u6807\u79f0200 MHz\uff0cPS\u5b9e\u9645\u914d\u7f6e199.998001 MHz\u3002\n- \u5df2\u5e03\u7ebf\uff1asetup +0.019 ns\uff0chold +0.009 ns\uff1b0\u8def\u7531\u9519\u8bef\u3002\u88d5\u91cf\u8f83\u5c0f\u3002\n- 73\u4e2aDDR\u7aef\u53e3\u7ea6\u675f\u3001CDC\u4e0eDRC\u8b66\u544a\u9010\u9879\u6838\u5bf9\uff0c\u539f\u8b66\u544a\u4fdd\u7559\u5728evidence\u3002\n- bit\u4e0eXSA\u5185\u5d4cbit\u9010\u5b57\u8282\u76f8\u540c\uff1bPS init\u6765\u81ea\u8fd9\u4efdXSA\u3002\n- \u5339\u914dBSP\u53ca\u4e24\u4e2aAArch64 ELF\u5b9e\u9645\u4e25\u683c\u7f16\u8bd1/\u94fe\u63a5\u901a\u8fc7\uff0cLOAD\u5747\u4f4d\u4e8ePS\u8f6f\u4ef6\u4fdd\u7559\u533a0x00000000\u20130x0fffffff\uff0c\u672a\u89e3\u6790\u7b26\u53f7\u4e3a\u7a7a\u3002\n- 576 MiB\u955c\u50cf\u3001canonical/tiled\u6743\u91cd\u548c16\u4e2a\u8f93\u5165\u5df2\u79bb\u7ebf\u6821\u9a8c\uff1b\u5c1a\u65e0\u672c\u8f6e\u76ee\u6807PL DDR\u56de\u8bfb\u7ed3\u679c\u3002\n\n## \u6587\u4ef6\u4e0e\u8eab\u4efd\nhardware/\uff1abit\u3001XSA\u3001PS init\u3002software/\uff1am14_d64_loader.elf\u3001m14_d64_test.elf\u3002\ndata/\uff1ad64_pl_576m.bin\u3001MANIFEST.json\u3001layout.json\u3002\nsource/\uff1a\u672c\u6b21\u5b9e\u9645\u7f16\u8bd1\u6e90\u53ca\u6784\u5efa\u8ba1\u5212\u3002references/\uff1a\u51bb\u7ed3\u7684Csim\u53c2\u8003\u6570\u7ec4\u300112\u573a\u666f\u914d\u7f6e\u4e0e16\u4e2a\u8f93\u5165\u3002\nevidence/\uff1a\u5b9e\u73b0\u3001\u8f6f\u4ef6\u3001\u79bb\u7ebf\u8d44\u4ea7\u6838\u9a8c\u53ca\u539f\u6d41\u7a0b\u5931\u8d25\u8bb0\u5f55\u3002\u8bb8\u53ef\u6587\u4ef6\u4e0d\u5728\u5305\u4e2d\u3002\nMANIFEST.json\u4e0eSHA256SUMS\u7528\u4e8e\u6587\u4ef6\u5b8c\u6574\u6027\uff1bZIP\u65c1\u53e6\u6709SHA256\u6587\u4ef6\u3002\u4fee\u6539\u5305\u5185\u6587\u4ef6\u540e\u5fc5\u987b\u91cd\u65b0\u751f\u6210\u5bf9\u5e94\u6e05\u5355\u548cZIP\u3002\n\n## \u79bb\u7ebf\u68c0\u67e5\n\u5728\u5305\u6839\u76ee\u5f55\u6267\u884c\uff1apython tools/verify_package.py\n\u8be5\u547d\u4ee4\u53ea\u6821\u9a8c\u672c\u5730\u6587\u4ef6\uff0c\u4e0d\u8fde\u63a5\u677f\u5361\u3002\npython tools/upload_d64.py data/d64_pl_576m.bin data/MANIFEST.json\n\u9ed8\u8ba4\u4e5f\u53ea\u9a8c\u8bc1\u672c\u5730\u955c\u50cf\uff1b\u53ea\u6709\u660e\u786e\u6dfb\u52a0--upload\u6216--read-only\u624d\u4f1a\u521b\u5efasocket\u3002\n\n## \u540e\u7eed\u4e0a\u677f\u5b89\u6392\uff08\u672c\u6b21\u672a\u6267\u884c\uff09\n\u5148\u786e\u8ba4\u72ec\u5360\u677f\u5361\uff0c\u6838\u5bf9AXU9EGB\u63a5\u7ebf\u4e0e\u4f9b\u7535\u3002\u4f7f\u7528\u672c\u5305bit\u3001PS init\u548cELF\u914d\u5957\u521d\u59cb\u5316\uff0c\u7981\u6b62\u6df7\u5165\u65e9\u671fv4\u7684ELF\u3002\nPL DDR\uff1a0x400000000\uff0c\u7269\u74062 GiB\uff1b\u8ba1\u7b97\u6570\u636e\u5728PL DDR\uff0c\u7a0b\u5e8f/\u6808/\u7f51\u53e3\u7f13\u51b2\u5141\u8bb8\u5728PS DDR\u3002\n\u63a7\u5236\uff1a0xA0000000\uff1b\u6821\u51c6GPIO\uff1a0xA0020000\uff1b\u7248\u672c\u7b7e\u540d\uff1a0x4D344401\u3002\nloader\u9759\u6001IP\uff1a192.168.0.190\uff0cTCP1416\uff0cD64A/version1/magic0x41343644\uff0c\u955c\u50cf603979776\u5b57\u8282\u3002\n\u521d\u6b21\u52a0\u8f7d\u5fc5\u987b\u4fdd\u7559576\u5757\u76ee\u6807CRC\u3001\u6574\u56fe\u76ee\u6807CRC\u548csentinel\u56de\u8bfb\u8bc1\u636e\uff1bREAD_ONLY\u56de\u6536\u4e0d\u66ff\u4ee3\u521d\u6b21\u52a0\u8f7d\u8bc1\u660e\u3002\n\u4f7f\u7528test ELF\u4f9d\u6b21\u6267\u884c12\u4e2a\u6301\u4e45\u72b6\u6001\u573a\u666f\u53ca\u56db\u7c7b\u56fa\u5b9a\u8f93\u5165\u54043\u6b21\u9884\u70ed\u300130\u6b21\u8ba1\u65f6\u30011000\u6b21\u7a33\u5b9a\u8c03\u7528\uff0c\u4e0d\u5728\u8c03\u7528\u4e4b\u95f4\u590d\u4f4d\u3002\n\u518d\u8fd0\u884cloader\u7684READ_ONLY\u65b9\u5f0f\u56de\u653624\u4efd\u5feb\u7167\u548c\u72b6\u6001/\u8ba1\u65f6\u8bb0\u5f55\uff1b\u8be5\u65b9\u5f0f\u4e0d\u80fd\u8bc1\u660e\u65b0\u6743\u91cd\u5df2\u6b63\u786e\u52a0\u8f7d\u3002\n\u9a8c\u6536\u547d\u4ee4\uff1apython tools/review_d64_board_results.py --dump <\u56de\u6536\u76ee\u5f55> --references references --out <\u65b0\u7ed3\u679c.json>\n\u8be5\u9a8c\u6536\u5668\u76ee\u524d\u5b8c\u6210\u8bed\u6cd5\u68c0\u67e5\uff0c\u5c1a\u672a\u5728\u7269\u7406\u677f\u5361\u6570\u636e\u4e0a\u6267\u884c\uff1b\u9700\u4fdd\u7559\u539f\u59cb\u56de\u6536\u6587\u4ef6\u5e76\u590d\u6838\u5176\u7ed3\u8bba\u3002\n\n## \u8ba1\u65f6\u89e3\u91ca\u4e0e\u9650\u5236\n\u5b9e\u9645BSP\u7684A53\u8ba1\u65f6\u9891\u738733333000 counts/s\u3002\u6bcf\u4e2a\u56fa\u5b9a\u8f93\u5165\u7684M14\u7b49\u6548\u8f93\u51fa\u7387=1000/\u5b8c\u6574A53\u8c03\u7528Median_ms\uff1bP95\u4f7f\u752830\u6b21\u6d4b\u91cf\u7684nearest-rank\u3002\n\u8c03\u7528\u5305\u542b\u53c2\u6570/\u8bfb\u56de\u3001\u7b49\u5f85\u3001\u7ed3\u679c\u6709\u6548\u4f4d\u53catoken/score CRC\u68c0\u67e5\uff1b\u4e0d\u542b\u521d\u59cb\u5316\u3001\u7f51\u53e3\u52a0\u8f7d\u3001\u6574\u6743\u91cdCRC\u3001\u5feb\u7167\u590d\u5236\u6216Transformer\u3002\n\u672c\u5305\u6ca1\u6709\u6574\u673aLLM token/s\u3001TTFT\u3001\u7269\u7406AXI\u9010\u62cd\u8f68\u8ff9\u6216IP\u786c\u4ef6\u5468\u671f\u5b9e\u6d4b\u6570\u636e\u3002\u56db\u7c7b\u56fa\u5b9a\u8f93\u5165\u901f\u5ea6\u4e5f\u4e0d\u7b49\u4e8e\u65b0\u8d28\u91cf\u96c6\u7684\u6574\u4f53decode\u5206\u5e03\u3002\n\u6570\u503c\u56de\u5f52\u3001\u9519\u8bef\u6062\u590d\u3001\u76ee\u6807DDR\u6821\u9a8c\u548c\u5b9e\u9645\u901f\u5ea6\uff0c\u5747\u987b\u4ee5\u968f\u540e\u672c\u8f6e\u677f\u5361\u539f\u59cb\u8bc1\u636e\u4e3a\u51c6\u3002\n",encoding='utf-8')
 verify=r'''from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parents[1];m=json.loads((root/'MANIFEST.json').read_text())
for name,item in m['files'].items():
 p=root/name;h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 assert p.stat().st_size==item['bytes'] and h.hexdigest()==item['sha256'],name
print('PASS_LOCAL_PACKAGE_SHA_ONLY_NO_BOARD')
'''
 (P/'tools/verify_package.py').write_text(verify,encoding='utf-8')
 files={str(p.relative_to(P)).replace('\\','/'):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in P.rglob('*') if p.is_file()}
 package=dict(state='EXPERIMENTAL_OFFLINE_PACKAGE_READY_FOR_FUTURE_EXCLUSIVE_BOARD_ACCEPTANCE',method='Abs(hidden)*RMS Top64 channels -> full-vocabulary preview -> Top4096 union14specialIDs -> canonical BF16 exact candidate logits',board='NOT_RUN',full12rtl='INCOMPLETE_USER_STOPPED',physical_decode_performance='NOT_MEASURED',route_setup_slack_ns=.019,route_hold_slack_ns=.009,files=files)
 (P/'MANIFEST.json').write_text(json.dumps(package,indent=2)+'\n',encoding='utf-8')
 (P/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(P)).replace('\\','/')+'\n' for p in sorted(P.rglob('*')) if p.is_file() and p.name!='SHA256SUMS'),encoding='utf-8')
 archive=D/(P.name+'.zip')
 with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
  for p in sorted(P.rglob('*')):
   if p.is_file():z.write(p,str(p.relative_to(D)).replace('\\','/'))
 with zipfile.ZipFile(archive) as z:assert z.testzip() is None
 (D/(archive.name+'.sha256')).write_text(sha(archive)+'  '+archive.name+'\n')
 (D/'PACKAGE_REVIEW.json').write_text(json.dumps(dict(state=package['state'],files=len(files),zip_bytes=archive.stat().st_size,zip_sha256=sha(archive),bit_sha256=hv['bit_sha256'],xsa_sha256=hv['xsa_sha256'],elf=pv['elf'],no_board_operations=True),indent=2)+'\n')
 print(json.dumps(dict(package=str(P.resolve()),zip=str(archive.resolve()),files=len(files),zip_bytes=archive.stat().st_size,zip_sha256=sha(archive)),indent=2))
if __name__=='__main__':main()

