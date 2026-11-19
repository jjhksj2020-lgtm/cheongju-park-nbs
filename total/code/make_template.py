"""biz/code/map_template.html(사업성 지도 틀)을 바탕으로 통합 지도 틀 total/code/total_template.html 을 만든다.
사업성 지도 틀이 바뀌면 다시 실행: python total/code/make_template.py"""
import os
C = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(C))
t = open(f'{ROOT}/biz/code/map_template.html', encoding='utf-8').read()
def R(a, b, n=1):
    global t
    assert t.count(a) == n, (t.count(a), a[:80]); t = t.replace(a, b)

# ---------- 제목·머리 ----------
R('<title>청주 미집행공원 토지지도</title>', '<title>청주 미집행공원 통합지도</title>')
R('<h1>청주 장기미집행 공원 40개소 · 땅 주인 지도</h1>', '<h1>청주 장기미집행 공원 40개소 · 사업성·열저감 통합 지도</h1>')
R('<div class="sub">공원 경계 안 필지를 국유·시유·사유로 나눠 본다 · V-World 조회 <span id="asof"></span></div>',
  '<div class="sub">같은 지도에서 주제를 바꿔 본다 — <b>사업성</b>: 시가 낼 돈·단계 · <b>열저감</b>: 조성하면 여름 지표온도가 얼마나 내려가나 · 기준일 <span id="asof"></span></div>')
R('''    <div class="tabs" role="group" aria-label="보기">''', '''    <div class="tabs topic" role="group" aria-label="주제">
      <button id="tp-biz" aria-pressed="true">사업성</button>
      <button id="tp-heat" aria-pressed="false">열저감</button>
    </div>
    <div class="tabs" role="group" aria-label="보기">''')
R('.tabs button[aria-pressed="true"]{', '.tabs.topic button[aria-pressed="true"]{background:var(--ink);color:var(--panel)}\n.tabs button[aria-pressed="true"]{')
R('details.ev{', '.ctabs{display:flex;gap:2px;background:var(--soft);padding:3px;border-radius:8px;margin:0 0 10px}\n.ctabs button{flex:1;border:0;background:transparent;color:var(--muted);font:inherit;font-size:12px;font-weight:600;padding:5px 8px;border-radius:6px;cursor:pointer}\n.ctabs button[aria-pressed="true"]{background:var(--panel);color:var(--ink);box-shadow:0 1px 2px rgba(0,0,0,.12)}\ndetails.ev{')

# ---------- 상태·옵션 ----------
R("const S = {ter:3,", "const S = {topic:'biz', ter:3,")
R("  park:{color:[", """  cityHeat:{color:[['kind','성격 (조성형·보전형)'],['cool','냉각량 °C·ha'],['dcell','공원 일대 저감 °C'],['ndvi','지금 녹지(NDVI)'],['grade','열저감 등급']], height:[['cool','냉각량 (제곱근 눈금)'],['dcell','공원 일대 저감 °C'],['none','없음']]},
  park:{color:[""")
R("  const k=S.view==='park'?'park':'city'; const o=OPTS[k];", "  const k=S.view==='park'?'park':'city'; const o=k==='park'?OPTS.park:(S.topic==='heat'?OPTS.cityHeat:OPTS.city);")

# ---------- 열저감 값·색 ----------
R("function cityColor(p){\n", """const E = p => p.E||{};
const heatOK = p => E(p).status==='산정';
const maxCool = Math.max(...D.parks.map(p=>E(p).cool_base||0));
const maxDcell = Math.max(...D.parks.map(p=>E(p).dlst_cell_base||0));
const KCOL = {'조성형':'--own-ind','보전형':'--own-loc','미산정':'--own-unk'};
const GCOL = {'상':'--own-nat','중':'--seq1','하':'--gu-line'};
const f2 = (v,d=2) => v==null?'—':(+v).toFixed(d);
function heatColor(p){
  const e=E(p); if(!heatOK(p)) return C['--own-unk'];
  if(S.colorCity==='kind') return C[KCOL[e.kind]||'--own-unk'];
  if(S.colorCity==='cool') return seq(Math.sqrt((e.cool_base||0)/maxCool));
  if(S.colorCity==='dcell') return seq((e.dlst_cell_base||0)/maxDcell);
  if(S.colorCity==='ndvi') return lerp(C['--own-ind'], C['--own-loc'], Math.max(0,Math.min(1,(e.ndvi_now-0.1)/0.8)));
  return C[GCOL[e.grade]||'--own-unk'];
}
function cityColor(p){
  if(S.topic==='heat') return heatColor(p);
""")
R("function cityHeight(p){\n", """function cityHeight(p){
  if(S.topic==='heat'){ const e=E(p); if(!heatOK(p)) return 0;
    if(S.heightCity==='cool') return Math.sqrt((e.cool_base||0)/maxCool)*6000;
    if(S.heightCity==='dcell') return (e.dlst_cell_base||0)/maxDcell*6000; return 0; }
""")
# updateTriggers 에 주제 반영
t = t.replace("updateTriggers:{getFillColor:[S.colorCity,C['--own-nat']]}", "updateTriggers:{getFillColor:[S.topic,S.colorCity,C['--own-nat']]}")
t = t.replace("updateTriggers:{getElevation:S.heightCity,getFillColor:[S.colorCity,C['--own-nat']]}", "updateTriggers:{getElevation:[S.topic,S.heightCity],getFillColor:[S.topic,S.colorCity,C['--own-nat']]}")
t = t.replace("updateTriggers:{getFillColor:[S.colorCity,S.sel,C['--own-nat']]", "updateTriggers:{getFillColor:[S.topic,S.colorCity,S.sel,C['--own-nat']]")

# ---------- 툴팁 ----------
R("  if(layer.id.startsWith('park-')){ const p=object.p||object; return {html:`<div class=\"tt\"><b>${p.name}</b> · ${p.loc}<br>면적 ${m2(p.area)} · 국공유 ${pct(p.pub)}<br>시 부담 최대 ${eok(p.maxH)}억 · ${p.stage}</div>`, style:ttStyle()}; }",
  "  if(layer.id.startsWith('park-')){ const p=object.p||object; const e=E(p); return {html:`<div class=\"tt\"><b>${p.name}</b> · ${p.loc}<br>면적 ${m2(p.area)} · 국공유 ${pct(p.pub)}<br>${S.topic==='heat'?(heatOK(p)?`${e.kind} · 냉각량 ${f2(e.cool_base)} °C·ha · 공원 일대 −${f2(e.dlst_cell_base)}°C · 등급 ${e.grade_range}`:'열저감 미산정'):`시 부담 최대 ${eok(p.maxH)}억 · ${p.stage}`}</div>`, style:ttStyle()}; }")

# ---------- 범례 ----------
R("  if(S.view==='city'){\n    if(S.colorCity==='pub')", """  if(S.view==='city' && S.topic==='heat'){
    if(S.colorCity==='kind') h=`<div class="t">열저감 성격</div><div class="row">${Object.entries(KCOL).map(([k,v])=>`<span class="k">${sw(v)}${k}</span>`).join('')}</div><div class="meta">조성형 = 지금 녹지가 잔디 수준(NDVI ${f2(D.E.target.grass)}) 미만</div>`;
    else if(S.colorCity==='cool') h=`<div class="t">냉각량 (기준 시나리오, 제곱근 눈금)</div><div class="ramp" style="background:linear-gradient(90deg,var(--seq0),var(--seq1),var(--seq2),var(--seq3))"></div><div class="ramp-l"><span>0</span><span>${f2(maxCool,1)} °C·ha</span></div>`;
    else if(S.colorCity==='dcell') h=`<div class="t">공원 일대 지표온도 저감 (기준)</div><div class="ramp" style="background:linear-gradient(90deg,var(--seq0),var(--seq1),var(--seq2),var(--seq3))"></div><div class="ramp-l"><span>0</span><span>−${f2(maxDcell)}°C</span></div>`;
    else if(S.colorCity==='ndvi') h=`<div class="t">지금 녹지 (Sentinel-2 여름 NDVI)</div><div class="ramp" style="background:linear-gradient(90deg,var(--own-ind),var(--own-loc))"></div><div class="ramp-l"><span>0.1 적음</span><span>0.9 많음</span></div>`;
    else h=`<div class="t">열저감 등급 (냉각량 순위)</div><div class="row">${Object.entries(GCOL).map(([k,v])=>`<span class="k">${sw(v)}${k}</span>`).join('')}</div>`;
    h+=`<div class="meta" style="margin-top:4px">${sw('--own-unk')} 미산정: 어린이공원152(경계 없음)·생태공원3(하천 위주)</div>`;
    h+= S.d3&&S.heightCity!=='none' ? `<div class="meta" style="margin-top:5px">기둥 높이 = ${S.heightCity==='cool'?`냉각량 (제곱근, 최고 ${f2(maxCool,1)} °C·ha)`:`공원 일대 저감 (최고 −${f2(maxDcell)}°C)`}</div>` : `<div class="meta" style="margin-top:5px">원 크기 = 공원 면적</div>`;
  } else if(S.view==='city'){
    if(S.colorCity==='pub')""")

# ---------- 카드: 주제 탭 + 열저감 카드 ----------
R("function card(){\n  const p=byId[S.sel];\n  if(!p){", """function topicTabs(){ return `<div class="ctabs" role="group" aria-label="카드 주제"><button data-tp="biz" aria-pressed="${S.topic==='biz'}">사업성 (시가 낼 돈)</button><button data-tp="heat" aria-pressed="${S.topic==='heat'}">열저감 (지표온도)</button></div>`; }
function bindTabs(){ $('card').querySelectorAll('.ctabs button').forEach(b=>b.onclick=()=>setTopic(b.dataset.tp)); }
function heatSummary(){
  const ok=D.parks.filter(heatOK); const s=k=>ok.reduce((a,p)=>a+(E(p)[k]||0),0);
  const byK=k=>ok.filter(p=>E(p).kind===k); const cK=k=>byK(k).reduce((a,p)=>a+E(p).cool_base,0);
  const top=[...ok].sort((a,b)=>E(b).cool_base-E(a).cool_base).slice(0,3).map(p=>p.name).join(', ');
  return `<h2>40개소 요약 · 열저감</h2><div class="meta">질문: 공원을 조성하면 지금보다 여름 지표온도가 얼마나 내려가나</div>
    <dl class="kv"><dt>산정</dt><dd>${ok.length}개소 / 40</dd><dt>냉각량 합계 (기준)</dt><dd>${f2(s('cool_base'),1)} °C·ha</dd>
    <dt>범위 (8개 시나리오)</dt><dd>${f2(s('cool_low'),1)}~${f2(s('cool_high'),1)}</dd>
    <dt>조성형</dt><dd>${byK('조성형').length}곳 · ${f2(cK('조성형'),1)}</dd><dt>보전형</dt><dd>${byK('보전형').length}곳 · ${f2(cK('보전형'),1)}</dd>
    <dt>등급 확정</dt><dd>${ok.filter(p=>E(p).grade_stable==='확정').length}곳 (경계 ${ok.filter(p=>E(p).grade_stable==='경계').length})</dd></dl>
    <div class="note">상위: ${top}. 계수는 모두 청주 위성 실측 — 녹지(NDVI) 1 증가당 −${f2(D.E.coef.green)}~−${f2(D.E.coef.loss)}°C, 주변 300m 퍼짐 ${f2(D.E.factors.spill[0])}~${f2(D.E.factors.spill[1])}(잠두봉·매봉). 지표온도이며 기온이 아니고, 전력으로 바꾸지 않는다.</div>`;
}
function heatCard(p){
  const e=E(p);
  const head=`<h2>${p.name} ${heatOK(p)?`<span class="pill" style="color:var(${KCOL[e.kind]})">${e.kind}</span><span class="pill s2">등급 ${e.grade_range} · ${e.grade_stable}</span>`:'<span class="pill warn">미산정</span>'}</h2><div class="meta">${p.loc} · ${p.type} · ${m2(p.area)}</div>`;
  if(!heatOK(p)) return head+`<div class="note">${e.note||(p.type==='생태공원'?'생태공원(하천·제방 위주)은 수면이 NDVI를 낮춰 녹지 증가가 과대 계산되므로 미산정.':'공원 경계가 없어 위성값을 뽑을 수 없음.')}</div>`;
  const L=['숲','농지','시가지','기반시설','공원'], LC={'숲':'--own-loc','농지':'--seq1','시가지':'--own-org','기반시설':'--own-nat','공원':'--own-unk'};
  const bar=`<div class="bar">${L.filter(k=>e['share_'+k]).map(k=>`<span title="${k} ${(e['share_'+k]*100).toFixed(0)}%" style="width:${e['share_'+k]*100}%;background:var(${LC[k]})"></span>`).join('')}</div>
    <div class="legend" style="position:static;border:0;padding:4px 0 0"><div class="row">${L.filter(k=>e['share_'+k]).map(k=>`<span class="k">${sw(LC[k])}${k} ${(e['share_'+k]*100).toFixed(0)}%</span>`).join('')}</div></div>`;
  return head+`<dl class="kv">
    <dt>지금 녹지 (NDVI)</dt><dd>${f2(e.ndvi_now,3)}</dd>
    <dt>① 녹지 증가 (기준·범위)</dt><dd>${f2(e.dndvi_base,3)} (${f2(e.dndvi_low,2)}~${f2(e.dndvi_high,2)})</dd>
    <dt>② 공원 일대 저감</dt><dd>−${f2(e.dlst_cell_base)}°C (${f2(e.dlst_cell_low)}~${f2(e.dlst_cell_high)})</dd>
    <dt>③ 주변 300m 저감</dt><dd>${e.ring_applied==='적용'?`−${f2(e.dlst_ring_base)}°C (${f2(e.dlst_ring_low)}~${f2(e.dlst_ring_high)})`:'— (1ha 미만)'}</dd>
    <dt>④ 냉각량</dt><dd>${f2(e.cool_base)} °C·ha (${f2(e.cool_low)}~${f2(e.cool_high)})</dd>
    <dt>위성 칸(1ha) 반영 비율</dt><dd>${f2(e.cell_share)}</dd>
    <dt>주변 300m 인구 (참고)</dt><dd>${e.pop_300!=null?Math.round(e.pop_300).toLocaleString('ko-KR')+'명':'—'}</dd></dl>
    <div class="t" style="font-weight:600;font-size:12px;margin-top:10px">지금 땅 상태 (필지 이용상황)</div>${bar}
    <details class="ev"><summary>숫자의 근거</summary><table>
    <tr><th>지금 녹지</th><td>Sentinel-2 L2A 여름(2024–25) ${D.E.city.s2_scenes}장 중앙값, 공원 경계 안</td></tr>
    <tr><th>조성 목표</th><td>청주 시가지 잔디 ${f2(D.E.target.grass,3)} ~ 수목 ${f2(D.E.target.tree,3)} (ESA WorldCover 분류별 중앙값)</td></tr>
    <tr><th>온도 계수</th><td>${D.E.periods.before[0].slice(0,4)}–${D.E.periods.before[1].slice(0,4)} → ${D.E.periods.after[0].slice(0,4)}–${D.E.periods.after[1].slice(0,4)} Landsat 8·9 여름, 녹지가 변한 픽셀 기울기: 늘어난 곳 −${f2(D.E.coef.green)}, 줄어든 곳 −${f2(D.E.coef.loss)}°C / NDVI 1</td></tr>
    <tr><th>1ha 칸</th><td>Landsat 열밴드 100m 관측 → 1ha보다 작은 공원은 면적÷1ha 만큼만 반영</td></tr>
    <tr><th>주변 300m 퍼짐</th><td>특례사업지 ${D.E.spill_sites.join('·')} 개발 전후 실측 ${f2(D.E.factors.spill[0])}~${f2(D.E.factors.spill[1])}, 1ha 이상 공원만</td></tr>
    <tr><th>등급</th><td>시나리오 8개마다 냉각량 순위로 상(25%)·중(50%)·하 → 모두 같으면 확정</td></tr>
    </table></details>`;
}
function card(){
  const p=byId[S.sel];
  if(S.topic==='heat'){ $('card').innerHTML=topicTabs()+(p?heatCard(p):heatSummary()); bindTabs(); return; }
  if(!p){""")
# 사업성 카드 앞에도 주제 탭
R("    $('card').innerHTML=`<h2>40개소 요약</h2>", "    $('card').innerHTML=topicTabs()+`<h2>40개소 요약 · 사업성</h2>")
R("      <div class=\"note\">생태공원3(2.58㎢)이 면적의 대부분을 차지하고 99.7%가 국유 하천·제방이다. 시 부담 합계에는 생태공원 조성비(미산정)가 빠져 있다.</div>`;\n    return;",
  "      <div class=\"note\">생태공원3(2.58㎢)이 면적의 대부분을 차지하고 99.7%가 국유 하천·제방이다. 시 부담 합계에는 생태공원 조성비(미산정)가 빠져 있다.</div>`;\n    bindTabs(); return;")
R("  $('card').innerHTML=`<h2>${p.name} <span class=\"pill ${p.stage==='1단계'?'s1':'s2'}\">${p.stage}</span>${warn}</h2>",
  "  $('card').innerHTML=topicTabs()+`<h2>${p.name} <span class=\"pill ${p.stage==='1단계'?'s1':'s2'}\">${p.stage}</span>${warn}</h2>")
R("  const g=$('goPark'); if(g) g.onclick=()=>setView('park');\n}", "  const g=$('goPark'); if(g) g.onclick=()=>setView('park');\n  bindTabs();\n}")

# ---------- 목록: 주제별 정렬·값 ----------
R("  const ps=[...D.parks].sort((a,b)=>(b.maxH||0)-(a.maxH||0));\n  $('list').innerHTML",
  "  const H=S.topic==='heat'; const ps=[...D.parks].sort((a,b)=>H?((E(b).cool_base??-1)-(E(a).cool_base??-1)):((b.maxH||0)-(a.maxH||0)));\n  $('list').innerHTML")
R("    <span class=\"v\">${eok(p.maxH)}억</span></button>`).join('');", "    <span class=\"v\">${H?(heatOK(p)?f2(E(p).cool_base)+' °C·ha':'미산정'):eok(p.maxH)+'억'}</span></button>`).join('');")
R("    <span class=\"mini\" title=\"국공유 ${pct(p.pub)}\"><i style=\"width:${(p.pub||0)*100}%\"></i></span></span>",
  "    <span class=\"mini\" title=\"${H?'지금 녹지 NDVI '+f2(E(p).ndvi_now):'국공유 '+pct(p.pub)}\"><i style=\"width:${H?Math.max(0,Math.min(1,E(p).ndvi_now||0))*100:(p.pub||0)*100}%;${H?'background:var(--own-loc)':''}\"></i></span></span>")

# ---------- 비교 막대 ----------
R('    <h2>공원별 시 부담 최대(상한 단가) — 보상비와 조성비</h2>', '    <div id="bizchart">\n    <h2>공원별 시 부담 최대(상한 단가) — 보상비와 조성비</h2>')
R('    <div id="chartrows"></div>\n  </div>', '''    <div id="chartrows"></div>
    </div>
    <div id="heatchart" hidden>
    <h2>공원별 냉각량 — 기준값과 8개 시나리오 범위</h2>
    <div class="meta" style="margin-bottom:10px">막대 = 하한~상한, 진한 칸 = 기준. 제곱근 눈금(작은 공원도 보이게). 오른쪽은 등급(냉각량 순위, 8개 시나리오가 모두 같으면 확정).</div>
    <div class="chead"><span>공원</span><span>냉각량 °C·ha</span><span style="text-align:right">기준</span><span class="pc" style="text-align:right">등급</span></div>
    <div id="heatrows"></div>
    </div>
  </div>''')
R("function chart(){\n", """function chart(){
  $('bizchart').hidden=S.topic==='heat'; $('heatchart').hidden=S.topic!=='heat';
  if(S.topic==='heat'){
    const ps=[...D.parks].sort((a,b)=>(E(b).cool_base??-1)-(E(a).cool_base??-1)); const mx=Math.sqrt(Math.max(...ps.map(p=>E(p).cool_high||0)));
    const x=v=>Math.sqrt(Math.max(0,v||0))/mx*100;
    $('heatrows').innerHTML=ps.map(p=>{const e=E(p); return `<div class="crow"><span class="nm" title="${p.name}">${p.name}</span>
      ${heatOK(p)?`<span class="cbar" style="position:relative;background:var(--soft)"><span style="position:absolute;left:${x(e.cool_low)}%;width:${Math.max(.6,x(e.cool_high)-x(e.cool_low))}%;height:100%;background:var(${KCOL[e.kind]});opacity:.45"></span><span style="position:absolute;left:${Math.max(0,x(e.cool_base)-.6)}%;width:1.2%;min-width:3px;height:100%;background:var(--ink)"></span></span>`:'<span class="meta">미산정</span>'}
      <span class="num">${heatOK(p)?f2(e.cool_base):'—'}</span><span class="num pc">${heatOK(p)?e.grade_range+(e.grade_stable==='확정'?'':'*'):''}</span></div>`;}).join('');
    return;
  }
""")

# ---------- 주제 전환 ----------
R("function setView(v){", """function setTopic(tp){
  if(S.topic===tp) return; S.topic=tp;
  ['biz','heat'].forEach(k=>$('tp-'+k).setAttribute('aria-pressed',k===tp));
  S.colorCity = tp==='heat'?'kind':'pub'; S.heightCity = tp==='heat'?'cool':'cost';
  S.colorPark = tp==='heat'?'use':'own';
  if(S.view==='chart'){ chart(); return; }
  fillSelects(); list(); render();
}
$('tp-biz').onclick=()=>setTopic('biz'); $('tp-heat').onclick=()=>setTopic('heat');
function setView(v){""")

# ---------- 출처 ----------
R("생태공원3 필지는 사유·대형 필지만 표시.</footer>", "생태공원3 필지는 사유·대형 필지만 표시. 열저감: Landsat 8·9 C2 L2(USGS)·Sentinel-2 L2A(ESA)·ESA WorldCover v200·GHSL 2020(인구 참고), Google Earth Engine 처리, energy_engine.py 산출 — 계수는 모두 청주 위성 실측, 지표온도(기온 아님).</footer>")

open(f'{C}/total_template.html', 'w', encoding='utf-8').write(t)
print('total/code/total_template.html', len(t))
