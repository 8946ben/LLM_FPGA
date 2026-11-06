"""One targeted RAM-for-port-scheduling variant, no algorithm/quality tuning."""
from pathlib import Path
import json,hashlib,tarfile
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';E=M/'experiments/partial_hw_20261024';R=M/'reports/partial_hw_20261024_r1';E3=E/'r3';R3=R/'r3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not (R3/'PLAN.json').exists();R3.mkdir(exist_ok=True);(E3/'derived').mkdir(parents=True,exist_ok=True)
    for p in (E/'r2/derived').iterdir():(E3/'derived'/p.name).write_bytes(p.read_bytes())
    s=(E/'partial_proto.cpp').read_text(encoding='utf-8')
    s=s.replace('unsigned keys[P_D];bool bad=false;','unsigned long long ranked[P_D];bool bad=false;')
    s=s.replace('keys[j]=0;dims[j]=0xffffffffu;','ranked[j]=0;')
    s=s.replace('unsigned carry_key=sort_key(value),carry_id=channel;','unsigned long long carry=(static_cast<unsigned long long>(sort_key(value))<<32) | (0xffffffffu-channel);')
    begin=s.index('            unsigned old_key=keys[j],old_id=dims[j];');end=s.index('        }\n    }\n    return bad;',begin)
    s=s[:begin]+'''            unsigned long long previous=ranked[j];
            if(carry>previous) {ranked[j]=carry;carry=previous;}
'''+s[end:]
    target='    return bad;\n}\n\nbool partial_preview'
    assert s.count(target)==1
    s=s.replace(target,'''emit_channel_ids:
    for(int j=0;j<P_D;++j) {
#pragma HLS PIPELINE II=1
        dims[j]=0xffffffffu-static_cast<unsigned>(ranked[j]);
    }
    return bad;
}

bool partial_preview''')
    s=s.replace('    unsigned hist[256];','''    unsigned hist[256],key_cache[P_V],id_cache[P_T+14];
#pragma HLS ARRAY_PARTITION variable=key_cache cyclic factor=4 dim=1
#pragma HLS ARRAY_PARTITION variable=id_cache cyclic factor=4 dim=1
read_key_cache:
    for(unsigned word=0;word<P_V/4;++word) {
#pragma HLS PIPELINE II=1
        Beat packed=workspace[P_KEY+word];
        for(unsigned lane=0;lane<4;++lane) {
#pragma HLS UNROLL
            key_cache[word*4+lane]=packed.range(lane*32+31,lane*32).to_uint();
        }
    }''')
    a=s.index('radix_word_loop:');b=s.index('        bool found=false;',a)
    s=s[:a]+'''radix_cached_key_loop:
        for(unsigned id=0;id<P_V;++id) {
#pragma HLS PIPELINE II=2
            unsigned key=key_cache[id];
            if((key&mask)==prefix) {unsigned digit=(key>>shift)&255;hist[digit]=hist[digit]+1;}
        }
'''+s[b:]
    a=s.index('    unsigned count=0;Beat packed_ids=~Beat(0);');b=s.index('    Beat header=0;',a)
    s=s[:a]+'''    unsigned count=0;
candidate_cached_scan:
    for(unsigned id=0;id<P_V;++id) {
#pragma HLS PIPELINE II=2
        unsigned key=key_cache[id];
        bool tied=key==prefix && remaining!=0;
        bool selected=key>prefix || tied;
        if(tied)--remaining;
        if(selected || (id>=151643 && id<151657))id_cache[count++]=id;
    }
write_candidate_cache:
    for(unsigned word=0;word<(count+3)/4;++word) {
#pragma HLS PIPELINE II=1
#pragma HLS LOOP_TRIPCOUNT min=1024 max=1028
        Beat packed_ids=~Beat(0);
        for(unsigned lane=0;lane<4;++lane) {
#pragma HLS UNROLL
            if(word*4+lane<count)packed_ids.range(lane*32+31,lane*32)=id_cache[word*4+lane];
        }
        workspace[P_TABLE+1+word]=packed_ids;
    }
'''+s[b:]
    assert 'carry_key' not in s and 'candidate_lane_loop:' not in s and 'radix_word_loop:' not in s
    (E3/'partial_proto.cpp').write_text(s,encoding='utf-8')
    t=(E/'r2/proto.tcl').read_text(encoding='utf-8').replace('.cache p64_r2 $mode','.cache p64_r3 $mode').replace('file join $src r2 derived','file join $src r3 derived')
    t=t.replace('add_files [file join $src partial_proto.cpp]','add_files [file join $src r3 partial_proto.cpp]')
    (E3/'proto.tcl').write_text(t,encoding='utf-8')
    remote=(E/'r2/remote_run.py').read_text(encoding='utf-8').replace('reports/partial_hw_20261024_r1/r2','reports/partial_hw_20261024_r1/r3').replace("E/'r2/proto.tcl'","E/'r3/proto.tcl'")
    remote=remote.replace("parent['r2']='candidate/history preloaded before DATAFLOW; no arithmetic/parameter change'","parent['r3']='r2 preloads retained; local32bit key cache, ordered candidate RAM and composite64bit channel ranks; arithmetic/parameters unchanged'")
    (E3/'remote_run.py').write_text(remote,encoding='utf-8')
    plan=json.loads((R/'r2/PLAN.json').read_text(encoding='utf-8'));plan.update(state='FROZEN_R3_RAM_SCHEDULING_VARIANT',
        parent_plan_sha256=sha(R/'r2/PLAN.json'),r2_verdict='CsimPASS; synthcompleted but estimate10.383ns/candidateemitII14; histogramII2; previewII1',
        repair_r3='Read all32bit keys once into banked BRAM,4 sequential radix scansII2, sorted candidate local RAM then packed AXI writeback; channel key/id composite64bit comparator; no false dependence directive, no arithmetic/parameter changes',
        additional_key_and_candidate_payload_bytes=151936*4+4110*4,
        exploration_limit='This is the one targeted memory-rich scheduling variant. If it fails timing/II, preserve results and stop before RTL; no unlimited sweep.')
    paths=[Path(__file__),*sorted(E3.glob('*.cpp')),*sorted(E3.glob('*.py')),*sorted(E3.glob('*.tcl')),*sorted((E3/'derived').iterdir())]
    plan['source_sha256'].update({p.relative_to(ROOT).as_posix():sha(p) for p in paths})
    (R3/'PLAN.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with tarfile.open(R/'r3_schedule_variant.tar.gz','w:gz') as t:
        for p in [R3/'PLAN.json',*paths]:t.add(p,arcname=p.relative_to(ROOT).as_posix(),recursive=False)
    print(json.dumps(dict(state=plan['state'],sha256=sha(R/'r3_schedule_variant.tar.gz'))))
if __name__=='__main__':main()
