// Saved calibration and final quality; no evaluation or parameter selection.
function calibrationQualityChart(rows){
 const names={DENSE_BF16:'BF16 同轮基线',DIRECT_W4:'W4 直接 · 质量未过',REFINE_W4_K512:'W4 预筛＋K512精算',DIRECT_W8:'W8 直接 · 质量未过',REFINE_W8_K512:'W8 预筛＋K512精算',CALIBRATION_QUALIFIED_DIRECT:'W12 直接 · 最终锁点'};
 const order=['DENSE_BF16','CALIBRATION_QUALIFIED_DIRECT','REFINE_W4_K512','REFINE_W8_K512','DIRECT_W4','DIRECT_W8'];
 const sorted=order.map(id=>rows.find(r=>r.id===id)).filter(Boolean);
 const W=1040,L=235,R=260,T=50,B=48,row=52,H=T+B+row*sorted.length;
 const maximum=Math.max(.2,Math.ceil(Math.max(...sorted.map(r=>r.quality.misses/r.quality.steps*100))*1.1));
 const x=v=>L+v/maximum*(W-L-R);
 let out=`<svg data-chart="six-method-calibration-quality" viewBox="0 0 ${W} ${H}" role="img" aria-label="与六个计时方案对应的校准decode错选漏选率对比" style="width:100%;height:auto;font:13px Microsoft YaHei,sans-serif"><title>六方案质量：同一4775次校准decode</title><desc>横轴从0开始，错误率越低越好。BF16为定义对照；直接量化为token错选，精算预筛为候选漏选。</desc>`;
 for(let i=0;i<=5;i++){const v=maximum*i/5;out+=`<line x1="${x(v)}" x2="${x(v)}" y1="${T-10}" y2="${H-B}" stroke="#d3dfd5"/><text x="${x(v)}" y="${H-20}" text-anchor="middle" fill="#5a7065">${v.toFixed(2)}%</text>`;}
 out+=`<text x="${L}" y="22" fill="#5a7065">decode错选/漏选率 · 越低越好</text><line x1="${x(.1)}" x2="${x(.1)}" y1="${T-10}" y2="${H-B}" stroke="#a25641" stroke-dasharray="5 4"><title>最终点门槛：错误率≤0.1%；校准准入还要求全部5095预测零错选/漏选</title></line>`;
 sorted.forEach((r,i)=>{const q=r.quality,error=q.misses/q.steps*100,y=T+i*row,color=r.id==='DIRECT_W4'||r.id==='DIRECT_W8'?'#9a5d66':'#17664e';
  out+=`<text x="${L-14}" y="${y+17}" text-anchor="end" fill="#20372e">${esc(names[r.id])}</text><rect data-method="${r.id}" data-misses="${q.misses}" data-steps="${q.steps}" data-value="${error}" x="${L}" y="${y}" width="${x(error)-L}" height="24" rx="3" fill="${color}"/><circle cx="${x(error)}" cy="${y+12}" r="4" fill="${color}"/><text x="${x(error)+12}" y="${y+17}" fill="${color}">${q.misses}/${q.steps} · ${(q.recall*100).toFixed(4)}%</text>`;
 });
 out+='</svg><div class="table-scroll"><table><thead><tr><th>计时方案</th><th>整体decode</th><th>中文</th><th>英文</th><th>代码</th><th>数学</th></tr></thead><tbody>';
 const cell=q=>`${q.misses}/${q.steps}<br>一致/召回 ${(q.recall*100).toFixed(4)}%`;
 out+=sorted.map(r=>`<tr><td>${esc(names[r.id])}</td><td>${cell(r.quality)}</td>${['chinese','english','code','math'].map(c=>`<td>${cell(r.quality.by_category[c])}</td>`).join('')}</tr>`).join('');
 return '<p class="section-note">6项与时间图逐项对应；共同使用320题/4775次decode校准记录。直接量化报告token一致率，预筛精算报告policy后dense赢家的候选召回率；BF16为定义对照。图上计数为错选/漏选，百分比标签为一致率/召回率。零值用圆点表示。</p>'+out+'</tbody></table></div><p class="section-note">校准用于选型，不能代替新独立问题认证；虚线为0.1%错误率参考线，保守校准准入另要求全部5095预测零错选/漏选。时间只测4个固定输入，质量覆盖完整校准集，样本与统计范围不同。</p>';
}
function finalQualityChart(final){
 if(!final)return '<p>新独立质量尚未完成。</p>';
 const categories=[['overall','整体'],['chinese','中文'],['english','英文'],['code','代码'],['math','数学']];
 const names={DIRECT_RTN_W12_G896_A:'W12 直接',REFINE_RTN_W4_G128_S_K512:'W4＋K512精算'};
 const colors=['#17664e','#ad7c33'],W=1040,L=132,R=290,T=55,B=50,row=76,H=T+B+row*categories.length;
 const max=.11,x=v=>L+v/max*(W-L-R);
 let svg=`<svg data-chart="final-quality" viewBox="0 0 ${W} ${H}" role="img" aria-label="新1000题两个锁点的整体及四类decode错选漏选率，越低越好" style="width:100%;height:auto;font:13px Microsoft YaHei,sans-serif"><title>独立最终质量：decode错选/漏选率（%）</title><desc>横轴从零开始，虚线为0.1%错误率门槛，即一致率99.9%。标签报告真实计数与一致率。</desc>`;
 for(const v of [0,.02,.04,.06,.08,.1])svg+=`<line x1="${x(v)}" x2="${x(v)}" y1="${T-10}" y2="${H-B}" stroke="#d3dfd5"/><text x="${x(v)}" y="${H-22}" text-anchor="middle" fill="#5a7065">${v.toFixed(2)}%</text>`;
 svg+=`<line x1="${x(.1)}" x2="${x(.1)}" y1="${T-18}" y2="${H-B}" stroke="#a25641" stroke-width="2" stroke-dasharray="6 5"/><text x="${x(.1)}" y="24" text-anchor="middle" fill="#a25641">门槛 ≤0.10%</text><text x="${L}" y="24" fill="#5a7065">错选/漏选率 · 越低越好</text>`;
 categories.forEach(([key,label],i)=>{const y=T+i*row;svg+=`<text x="${L-18}" y="${y+26}" text-anchor="end" fill="#20372e">${label}</text>`;
  final.results.forEach((r,j)=>{const q=key==='overall'?r.quality.decode:r.quality.decode.by_category[key];const error=q.misses/q.steps*100,yy=y+j*27;
   svg+=`<rect data-method="${r.id}" data-category="${key}" data-misses="${q.misses}" data-steps="${q.steps}" data-value="${error}" x="${L}" y="${yy}" width="${x(error)-L}" height="18" rx="3" fill="${colors[j]}"/><circle cx="${x(error)}" cy="${yy+9}" r="4" fill="${colors[j]}"><title>${esc(names[r.id])} / ${label}：${q.misses}/${q.steps}，一致率 ${(q.recall*100).toFixed(4)}%</title></circle><text x="${x(error)+12}" y="${yy+14}" fill="${colors[j]}">${q.misses}/${q.steps} · 一致率 ${(q.recall*100).toFixed(4)}%</text>`;
  });
 });
 svg+='</svg>';
 return '<p class="section-note">'+final.results.map((r,j)=>`<span style="color:${colors[j]}">● ${esc(names[r.id])}</span>`).join('　')+'</p>'+svg+
 '<p class="section-note">全新1000题，共14948次decode，零排除；两个锁点整体和每类均达到≥99.9%。代码与数学两方案均零错误，零值以圆点表示。质量使用新问题组，时间使用4个固定校准输入，两组样本分别统计。</p>';
}
