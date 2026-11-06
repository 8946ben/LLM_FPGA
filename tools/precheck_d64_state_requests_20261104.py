"""Finite synthetic controls of request replay + structural guard checks, no EDA."""
from pathlib import Path
import copy,csv,datetime,hashlib,json,re,tempfile
from review_d64_state_requests_20261104 import replay_requests
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4'
E=M/'experiments/d64_state_tb_20261104_r1';R=M/'reports/d64_state_tb_20261104_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    rows=[];metrics=[];summary=[];tick=0
    for frame in range(12):
        entries=[]
        if frame not in [5,6]:entries.append(('MR',0,0))
        if frame in [0,1,2,3,4,10,11]:entries += [('MW',24368,0),('WR',0,0)]
        if frame in [0,1,2,3,4,11]:entries.append(('WR',273416192,0))
        if frame==0:entries += [('MR',1289440,0),('MW',1289440,0),('WR',545685488,0),('WR',536870912,0),('MR',4080,0)]
        if frame==7:entries.append(('MR',24352,0))
        if frame==10:entries.append(('WR',273416176,0))
        c=[0]*7
        for kind,address,length in entries:
            tick+=1;rows.append([kind,str(frame),str(tick),'%016x'%address,str(length)])
            if kind=='MR':c[0]+=1;c[1]+=length+1
            elif kind=='MW':c[2]+=1;c[3]+=length+1
            else:
                c[4]+=1;c[5]+=length+1
                if address>=273416192:c[6]+=1
        metrics.append(dict(case=frame,meta_reads=c[1],meta_writes=c[3],weight_reads=c[5],canonical_requests=c[6]))
        summary.append([frame,*c])
    def save(path,rows):
        with path.open('w',newline='') as f:csv.writer(f).writerows(rows)
    rejected=[]
    with tempfile.TemporaryDirectory(prefix='request_auditor_control_',dir=R) as tmp:
        tmp=Path(tmp);positive=tmp/'SYNTHETIC_NOT_RTL.csv';total=tmp/'SYNTHETIC_NOT_RTL_summary.csv'
        save(positive,rows);save(total,summary);result=replay_requests(positive,metrics,total)
        first_mr=next(i for i,x in enumerate(rows) if x[0]=='MR')
        first_mw=next(i for i,x in enumerate(rows) if x[0]=='MW')
        first_wr=next(i for i,x in enumerate(rows) if x[0]=='WR')
        err_mr=next(i for i,x in enumerate(rows) if x[0]=='MR' and x[1]=='7')
        err_wr=next(i for i,x in enumerate(rows) if x[0]=='WR' and x[1]=='10')
        edits=[('meta_end_guard',first_mr,3,'%016x'%1289456),('input_overwrite',first_mw,3,'%016x'%0),
               ('workspace_end_guard',first_mw,3,'%016x'%1289456),('invalid_length',first_mr,4,'128'),
               ('unaligned',first_mr,3,'%016x'%1),('weight_end',first_wr,3,'%016x'%545685504),
               ('error_reads_workspace',err_mr,3,'%016x'%24368),('preview_error_canonical',err_wr,3,'%016x'%273416192),
               ('unknown_address',first_mr,3,'xxxxxxxxxxxxxxxx')]
        for label,index,column,value in edits:
            bad=[*rows];bad[index]=[*rows[index]];bad[index][column]=value
            path=tmp/'bad.csv';save(path,bad)
            try:replay_requests(path,metrics,total)
            except (AssertionError,ValueError):rejected.append(label)
            else:raise AssertionError('Accepted '+label)
        for label,address,length in [('4k_crossing',4080,1),('overflow',0xfffffffffffffff0,1)]:
            bad=[*rows];bad[first_mr]=[*rows[first_mr]];bad[first_mr][3]='%016x'%address;bad[first_mr][4]=str(length)
            path=tmp/'bad.csv';save(path,bad)
            try:replay_requests(path,metrics,total)
            except AssertionError:rejected.append(label)
            else:raise AssertionError('Accepted '+label)
        bad=copy.deepcopy(metrics);bad[0]['weight_reads']+=1
        try:replay_requests(positive,bad,total)
        except AssertionError:rejected.append('request_vs_actual_read_count')
        else:raise AssertionError('Accepted wrong count')
        bad=copy.deepcopy(summary);bad[0][1]+=1;save(tmp/'bad_summary.csv',bad)
        try:replay_requests(positive,metrics,tmp/'bad_summary.csv')
        except AssertionError:rejected.append('summary_vs_actual_requests')
        else:raise AssertionError('Accepted wrong summary')
    guard=E/'state_request_guard.sv';text=guard.read_text()
    portdecl=re.search(r'module d64_state_request_guard\((.*?)\);',text,re.S).group(1)
    ports=[]
    for item in portdecl.split(','):
        item=re.sub(r'\b(input|integer)\b|\[[^]]+\]','',item).strip();assert re.fullmatch(r'\w+',item);ports.append(item)
    binding=re.search(r'bind d64_state_tb d64_state_request_guard state_request_guard\((.*?)\);',text,re.S).group(1)
    pairs=re.findall(r'\.(\w+)\((\w+)\)',binding)
    assert {a for a,b in pairs}==set(ports) and len(pairs)==len(ports)
    bench=(E/'d64_state_tb.sv').read_text()
    declared={n for n in re.findall(r'\blogic\s*(?:\[[^]]+\])?\s*(\w+)\s*;',bench)}
    declared.update(['active_case','frame','current_debug'])
    assert all(b in declared for a,b in pairs)
    for line in text.splitlines():assert len(re.findall(r'(?<!\\)"',re.sub(r'//.*','',line)))%2==0
    stripped=re.sub(r'"(?:\\.|[^"\\])*"','""',re.sub(r'//[^\n]*','',text));words=re.findall(r'\b\w+\b',stripped)
    assert words.count('begin')==words.count('end') and words.count('task')==words.count('endtask')
    out=dict(state='PASS_SYNTHETIC_REQUEST_AUDITOR_AND_GUARD_STRUCTURE_ONLY',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        positive=result,negative_controls_rejected=rejected,guard_port_connections=len(pairs),
        sources={p.relative_to(ROOT).as_posix():sha(p) for p in [guard,E/'d64_state_tb.sv',ROOT/'tools/review_d64_state_requests_20261104.py']},
        evidence_scope='Synthetic accepted-request rows and static SV/bind inspection only; no compiled/executed monitor or full DUT.',
        pending=['Actual guard compile/unit controls','Actual qualified native model and completed suite','Full request/response completion and numeric binding'],
        eda='NOT_RUN',board='NOT_RUN',automatic_next_stage=False)
    target=R/'REQUEST_GUARD_PREPARATION_REVIEW.json';assert not target.exists()
    target.write_text(json.dumps(out,indent=2)+'\n')
    supplement=dict(state='PREPARED_NOT_COMPILED',base_preparation_sha256=sha(R/'PREPARATION.json'),
        request_guard_review_sha256=sha(target),additional_source=guard.relative_to(ROOT).as_posix(),additional_source_sha256=sha(guard),
        compilation_requirement='Include state_request_guard.sv after d64_state_tb.sv in the eventual independently frozen project. Existing bench and current strong-delay job unchanged.',
        source_changes_to_existing_bench=False,eda='NOT_RUN',automatic_next_stage=False)
    (R/'REQUEST_GUARD_SUPPLEMENT.json').write_text(json.dumps(supplement,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='positive'},indent=2))
if __name__=='__main__':main()
