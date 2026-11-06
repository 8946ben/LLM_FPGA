// Pure presentation of saved GPU_BENCHMARK.json; never runs a benchmark.
function gpuTimingCharts(benchmark){
 if(!benchmark)return '<p>尚无GPU计时结果。</p>';
 const names={DENSE_BF16:'BF16 同轮基线',DIRECT_W4:'W4 直接 · 质量未过',REFINE_W4_K512:'W4 预筛＋K512精算',DIRECT_W8:'W8 直接 · 质量未过',REFINE_W8_K512:'W8 预筛＋K512精算',CALIBRATION_QUALIFIED_DIRECT:'W12 直接 · 最终锁点'};
 const ordered=['DENSE_BF16','CALIBRATION_QUALIFIED_DIRECT','REFINE_W4_K512','REFINE_W8_K512','DIRECT_W4','DIRECT_W8'].map(id=>benchmark.methods.find(r=>r.id===id)).filter(Boolean);
 const W=940,L=224,R=80,T=50,B=44,row=66,H=T+B+row*ordered.length;
 const max=Math.ceil(Math.max(...ordered.map(r=>r.p95_ms))*1.12*2)/2;
 const x=v=>L+v/max*(W-L-R),f=v=>v.toFixed(3);
 let bars=`<svg data-chart="gpu-overall-timing" viewBox="0 0 ${W} ${H}" role="img" aria-label="六方案GPU耗时对比，中位数与P95，单位毫秒，越低越好" style="width:100%;height:auto;font:13px Microsoft YaHei,sans-serif"><title>同轮GPU耗时：中位数与P95（ms）</title><desc>每方案120次，四固定输入各30次；蓝色为中位数，浅灰色为P95。</desc>`;
 for(let i=0;i<=5;i++){const v=max*i/5;bars+=`<line x1="${x(v)}" x2="${x(v)}" y1="${T-10}" y2="${H-B}" stroke="#d3dfd5"/><text x="${x(v)}" y="${H-17}" text-anchor="middle" fill="#5a7065">${v.toFixed(1)}</text>`;}
 bars+=`<text x="${W-R}" y="22" text-anchor="end" fill="#5a7065">毫秒 ms · 越低越好</text>`;
 ordered.forEach((r,i)=>{const y=T+i*row;bars+=`<text x="${L-14}" y="${y+23}" text-anchor="end" fill="#20372e">${esc(names[r.id]||r.id)}</text>`;
  for(const [key,color,dy,label] of [['median_ms','#335e88',0,'中位数'],['p95_ms','#bccbd5',23,'P95']]){
   bars+=`<rect data-method="${r.id}" data-metric="${key}" data-value="${r[key]}" x="${L}" y="${y+dy}" width="${x(r[key])-L}" height="18" rx="3" fill="${color}"><title>${esc(names[r.id])} ${label}: ${f(r[key])} ms</title></rect><text x="${x(r[key])+7}" y="${y+dy+14}" fill="#20372e">${f(r[key])}</text>`;
  }
 });
 bars+='</svg>';
 const cases=['chinese','english','code','math'],caseNames=['中文','英文','代码','数学'];
 const selected=ordered.filter(r=>['DENSE_BF16','CALIBRATION_QUALIFIED_DIRECT','REFINE_W4_K512'].includes(r.id));
 const colors=['#335e88','#17664e','#ad7c33'],CW=940,CH=340,CL=70,CR=34,CT=35,CB=68;
 const cap=Math.ceil(Math.max(...selected.flatMap(r=>cases.map(c=>r.by_case[c].median_ms)))*1.18*2)/2;
 const xx=i=>CL+i*(CW-CL-CR)/3,yy=v=>CH-CB-v/cap*(CH-CT-CB);
 let lines=`<svg data-chart="gpu-case-timing" viewBox="0 0 ${CW} ${CH}" role="img" aria-label="BF16与两个最终锁点在四类固定输入上的GPU中位耗时" style="width:100%;height:auto;font:13px Microsoft YaHei,sans-serif"><title>四固定输入的中位耗时（ms）</title><desc>每个点30次测量。连线只帮助比较类别，不表示输入难度或连续变量。</desc>`;
 for(let i=0;i<=4;i++){const v=cap*i/4;lines+=`<line x1="${CL}" x2="${CW-CR}" y1="${yy(v)}" y2="${yy(v)}" stroke="#d3dfd5"/><text x="${CL-10}" y="${yy(v)+4}" text-anchor="end" fill="#5a7065">${v.toFixed(2)}</text>`;}
 lines+=`<text x="${CL}" y="18" fill="#5a7065">毫秒 ms · 越低越好</text>`;
 cases.forEach((c,i)=>lines+=`<text x="${xx(i)}" y="${CH-CB+26}" text-anchor="middle" fill="#20372e">${caseNames[i]}</text>`);
 selected.forEach((r,j)=>{const values=cases.map(c=>r.by_case[c].median_ms);lines+=`<polyline points="${values.map((v,i)=>xx(i)+','+yy(v)).join(' ')}" fill="none" stroke="${colors[j]}" stroke-width="2.5"/>`;
  values.forEach((v,i)=>lines+=`<circle data-method="${r.id}" data-case="${cases[i]}" data-value="${v}" cx="${xx(i)}" cy="${yy(v)}" r="5" fill="${colors[j]}"><title>${esc(names[r.id])} / ${caseNames[i]}: ${f(v)} ms</title></circle>`);
 });
 lines+='</svg>';
 return '<h3>整体耗时：中位数与 P95</h3><p class="section-note">■ 蓝：中位数　■ 浅灰：P95。每方案120次（4固定输入×30），另每组合3次预热。鼠标悬停可读数值。</p>'+bars+
 '<h3>同一固定输入下，两个最终锁点与 BF16 的时间对比</h3><p class="section-note">'+selected.map((r,j)=>`<span style="color:${colors[j]}">● ${esc(names[r.id])}</span>`).join('　')+'</p>'+lines+
 '<p class="section-note">每个点为该固定输入30次测量的中位数；类别连线仅辅助比较，不代表连续变化。分项点值可悬停查看，完整汇总表见实验8。</p>';
}
