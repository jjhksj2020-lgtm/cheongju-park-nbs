"""biz/code/map_template.html(사업성 지도 틀)에 열저감·이용성 화면을 더해 통합 지도 틀 total/code/total_template.html 을 만든다.
사업성 지도 틀이 바뀌면 다시 실행: python total/code/make_template.py"""
import os
C = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(C))
t = open(f'{ROOT}/biz/code/map_template.html', encoding='utf-8').read()
def R(a, b, n=1):
    global t
    assert t.count(a) == n, (t.count(a), a[:80]); t = t.replace(a, b)

# ---------- 제목·머리 ----------
R('<title>청주 미집행공원 토지지도</title>', '<title>청주 장기미집행 공원 40개소 조성 지도</title>')
R('<h1>청주 장기미집행 공원 40개소 · 땅 주인 지도</h1>', '<h1>청주 장기미집행 공원 40개소 조성 지도</h1>')
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
R("  if(layer.id.startsWith('park-')){ const p=object.p||object; return {html:`<div class=\"tt\"><b>${p.name}</b> · ${p.loc}<br>면적 ${m2(p.area)} · 국공유 ${pct(p.pub)}<br>보상 ${eok(p.comp)}억 + 조성 ${eok(p.cons)}억 = 시 부담 최대 ${eok(p.maxH)}억 · ${p.stage}</div>`, style:ttStyle()}; }",
  "  if(layer.id.startsWith('park-')){ const p=object.p||object; const e=E(p); return {html:`<div class=\"tt\"><b>${p.name}</b> · ${p.loc}<br>면적 ${m2(p.area)} · 국공유 ${pct(p.pub)}<br>${S.topic==='heat'?(heatOK(p)?`${e.kind} · 냉각량 ${f2(e.cool_base)} °C·ha · 공원 일대 −${f2(e.dlst_cell_base)}°C · 등급 ${e.grade_range}`:'열저감 미산정'):`보상 ${eok(p.comp)}억 + 조성 ${eok(p.cons)}억 = 시 부담 최대 ${eok(p.maxH)}억 · ${p.stage}`}</div>`, style:ttStyle()}; }")

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
  S.colorPark = tp==='heat'?'use':'cost';
  if(S.view==='chart'){ chart(); return; }
  fillSelects(); list(); render();
}
$('tp-biz').onclick=()=>setTopic('biz'); $('tp-heat').onclick=()=>setTopic('heat');
function setView(v){""")

# ---------- 출처 ----------
R("생태공원3 필지는 사유·대형 필지만 표시.</footer>", "생태공원3 필지는 사유·대형 필지만 표시. 열저감: Landsat 8·9 C2 L2(USGS)·Sentinel-2 L2A(ESA)·ESA WorldCover v200·GHSL 2020(인구 참고), Google Earth Engine 처리, energy_engine.py 산출 — 계수는 모두 청주 위성 실측, 지표온도(기온 아님).</footer>")

# ================= 이용성 (③ 인구·토지·생활권 E·D·C, need/edc) =================
R('· <b>열저감</b>: 조성하면 여름 지표온도가 얼마나 내려가나 · 기준일',
  '· <b>열저감</b>: 조성하면 여름 지표온도가 얼마나 내려가나 · <b>이용성</b>: 주변에 누가 살고 지금 공원이 얼마나 모자라나 · 기준일')
R('      <button id="tp-heat" aria-pressed="false">열저감</button>', '      <button id="tp-heat" aria-pressed="false">열저감</button>\n      <button id="tp-use" aria-pressed="false">이용성</button>')
R("  park:{color:[", """  cityUse:{color:[['d1','D1 서비스권 밖 비율'],['e1','E1 버퍼 인구'],['e2','E2 아동·고령 비율'],['d2','D2 생활권 1인당 공원면적'],['c1','C1 녹지·수변축 거리'],['atype','지역 유형 (표시용)']], height:[['new','신규 수혜 인구 (제곱근 눈금)'],['e1','E1 버퍼 인구 (제곱근 눈금)'],['none','없음']]},
  park:{color:[""")
R("(S.topic==='heat'?OPTS.cityHeat:OPTS.city)", "(S.topic==='heat'?OPTS.cityHeat:S.topic==='use'?OPTS.cityUse:OPTS.city)")
R("function cityColor(p){\n", """const U = p => p.U||{};
const useOK = p => U(p).status==='산정';
const UOK = D.parks.filter(useOK);
const umax = k => Math.max(...UOK.map(p=>U(p)[k]||0)), umin = k => Math.min(...UOK.map(p=>U(p)[k]||0));
const maxE1=umax('E1_pop'), maxNew=umax('new_served_pop'), maxC1=umax('C1_m'), minE2=umin('E2_vulnerable'), maxE2=umax('E2_vulnerable'), minD2=umin('D2_built_m2_per_cap'), maxD2=umax('D2_built_m2_per_cap');
const ATCOL = {'밀집':'--own-org','주거':'--own-ind','주거+산업':'--seq2','산업':'--own-nat','기타':'--own-loc'};
const UTCOL = {'실자료':'--own-loc','대체자료':'--own-ind','가정':'--muted','미산정':'--own-unk'};
const nf = v => v==null?'—':Math.round(v).toLocaleString('ko-KR');
const pct1 = v => v==null?'—':(v*100).toFixed(1)+'%';
function utag(p,k){ const t=(U(p).tag||{})[k]; return t?` <span class="pill" style="color:var(${UTCOL[t[0]]||'--muted'})" title="자료: ${t[1]}">${t[0]}</span>`:''; }
function useColor(p){
  const u=U(p); if(!useOK(p)) return C['--own-unk'];
  if(S.colorCity==='d1') return seq(u.D1_unserved||0);
  if(S.colorCity==='e1') return seq(Math.sqrt((u.E1_pop||0)/maxE1));
  if(S.colorCity==='e2') return seq((u.E2_vulnerable-minE2)/((maxE2-minE2)||1));
  if(S.colorCity==='d2') return seq((maxD2-u.D2_built_m2_per_cap)/((maxD2-minD2)||1));
  if(S.colorCity==='c1') return seq(Math.min(1,(u.C1_m||0)/maxC1));
  return C[ATCOL[u.area_type]||'--own-unk'];
}
function useTip(p){ const u=U(p); return useOK(p)?`버퍼 ${u.buffer_m}m 인구 ${nf(u.E1_pop)}명 · 서비스권 밖 ${pct(u.D1_unserved)} · 신규 수혜 ${nf(u.new_served_pop)}명 · ${u.area_type}`:'이용성 미산정'; }
function useLegend(){
  const ramp=(t,a,b)=>`<div class="t">${t}</div><div class="ramp" style="background:linear-gradient(90deg,var(--seq0),var(--seq1),var(--seq2),var(--seq3))"></div><div class="ramp-l"><span>${a}</span><span>${b}</span></div>`;
  let h;
  if(S.colorCity==='d1') h=ramp('D1 서비스권 밖 비율 (버퍼 인구 중 기존 공원 유치권 밖)','0%','100%');
  else if(S.colorCity==='e1') h=ramp('E1 버퍼 인구 (제곱근 눈금)','0',nf(maxE1)+'명');
  else if(S.colorCity==='e2') h=ramp('E2 아동(9세 이하)·고령(65세 이상) 비율',pct1(minE2),pct1(maxE2));
  else if(S.colorCity==='d2') h=ramp('D2 생활권 1인당 조성 공원면적 (진할수록 적음)',maxD2+'㎡',minD2+'㎡');
  else if(S.colorCity==='c1') h=ramp('C1 녹지·수변축까지 거리 (진할수록 멂)','0m',nf(maxC1)+'m')+`<div class="meta">녹지축 = 토지피복지도 산림 ${D.U.params.axis_forest_min_ha}ha 이상, 수변축 = OSM 주요 하천. 녹지축 도면이 없어 대체자료</div>`;
  else h=`<div class="t">지역 유형 (표시용, 점수에는 넣지 않음)</div><div class="row">${Object.entries(ATCOL).map(([k,v])=>`<span class="k">${sw(v)}${k}</span>`).join('')}</div>`;
  h+=`<div class="meta" style="margin-top:4px">${sw('--own-unk')} 미산정: ${D.parks.filter(p=>!useOK(p)).map(p=>p.name).join('·')}(경계 없음)</div>`;
  h+= S.d3&&S.heightCity!=='none' ? `<div class="meta" style="margin-top:5px">기둥 높이 = ${S.heightCity==='new'?`신규 수혜 인구 (제곱근, 최고 ${nf(maxNew)}명)`:`버퍼 인구 (제곱근, 최고 ${nf(maxE1)}명)`}</div>` : `<div class="meta" style="margin-top:5px">원 크기 = 공원 면적</div>`;
  return h;
}
function useSummary(){
  const ok=UOK; const s=k=>ok.reduce((a,p)=>a+(U(p)[k]||0),0); const cnt=k=>ok.filter(p=>U(p).area_type===k).length;
  const top=[...ok].sort((a,b)=>U(b).new_served_pop-U(a).new_served_pop).slice(0,3).map(p=>`${p.name}(${nf(U(p).new_served_pop)}명)`).join(', ');
  return `<h2>40개소 요약 · 이용성</h2><div class="meta">질문: 공원 주변에 누가 살고, 지금 공원 혜택을 못 받는 사람이 얼마나 되나</div>
    <dl class="kv"><dt>산정</dt><dd>${ok.length}개소 / 40</dd>
    <dt>버퍼 인구 합계</dt><dd>${nf(s('E1_pop'))}명</dd><dt>신규 수혜 인구 합계</dt><dd>${nf(s('new_served_pop'))}명</dd>
    <dt>녹지·수변축 ${D.U.params.c1_near_m}m 이내</dt><dd>${ok.filter(p=>U(p).C1_near).length}곳</dd>
    <dt>지역 유형</dt><dd>${Object.keys(ATCOL).filter(cnt).map(k=>`${k} ${cnt(k)}`).join(' · ')}</dd></dl>
    <div class="note">신규 수혜 상위: ${top}. 버퍼가 겹치는 공원이 있어 합계에는 같은 사람이 두 번 들어갈 수 있다. 인구는 SGIS 2024 100m 격자, 기존 공원은 청주시 공원 목록(미조성 제외).</div>`;
}
function useCard(p){
  const u=U(p);
  const head=`<h2>${p.name} ${useOK(p)?`<span class="pill s2">${u.area_type}</span>`:'<span class="pill warn">미산정</span>'}</h2><div class="meta">${p.loc} · ${p.type} · ${m2(p.area)}${useOK(p)?` · ${u.dong} · ${u.living_zone}`:''}</div>`;
  if(!useOK(p)) return head+`<div class="note">${u.note||'공원 경계가 없어 산정하지 못함.'}</div>`;
  const row=(k,label,val)=>`<dt>${label}${utag(p,k)}</dt><dd>${val}</dd>`;
  const sh=[['주거',u.res_share,'--own-ind'],['공업',u.ind_share,'--own-nat'],['상업',u.com_share,'--own-org']];
  const rest=Math.max(0,1-sh.reduce((a,x)=>a+x[1],0));
  const bar=`<div class="bar">${sh.filter(x=>x[1]).map(([k,v,c])=>`<span title="${k} ${(v*100).toFixed(0)}%" style="width:${v*100}%;background:var(${c})"></span>`).join('')}<span title="그 밖 ${(rest*100).toFixed(0)}%" style="width:${rest*100}%;background:var(--soft)"></span></div>
    <div class="legend" style="position:static;border:0;padding:4px 0 0"><div class="row">${sh.map(([k,v,c])=>`<span class="k">${sw(c)}${k} ${(v*100).toFixed(0)}%</span>`).join('')}<span class="k">${sw('--soft')}그 밖(도로·녹지·농지 등) ${(rest*100).toFixed(0)}%</span></div></div>`;
  const A=D.U.params.area_type;
  return head+`<dl class="kv">
    ${row('E1',`E1 버퍼 ${u.buffer_m}m 인구`,nf(u.E1_pop)+'명')}
    ${row('E2','E2 아동·고령 비율',pct1(u.E2_vulnerable))}
    ${row('D1','D1 서비스권 밖 비율',pct1(u.D1_unserved))}
    ${row('new_served_pop','신규 수혜 인구',nf(u.new_served_pop)+'명')}
    ${row('D2',`D2 ${u.living_zone} 1인당`,`조성 ${u.D2_built_m2_per_cap}㎡ (결정 ${u.D2_decided_m2_per_cap}㎡)`)}
    ${row('C1','C1 녹지·수변축 거리',nf(u.C1_m)+'m')}
    <dt>수변축 / 녹지축</dt><dd>${nf(u.C1_water_m)}m / ${nf(u.C1_green_m)}m</dd>
    ${row('river_adjacent',`하천 ${D.U.params.river_adjacent_m}m 이내`,u.river_adjacent?'예':'아니오')}
    <dt>버퍼 인구밀도</dt><dd>${nf(u.pop_density_km2)}명/㎢</dd></dl>
    <div class="t" style="font-weight:600;font-size:12px;margin-top:10px">버퍼 안 토지이용 (토지피복지도 2025)</div>${bar}
    <details class="ev"><summary>숫자의 근거</summary><table>
    <tr><th>버퍼</th><td>공원 경계 + 유치거리 ${u.buffer_m}m (소공원·어린이공원 ${D.U.buffer_m['소공원']}m, 그 밖 ${D.U.buffer_m['근린공원']}m)</td></tr>
    <tr><th>E1 인구</th><td>SGIS 2024 100m 격자 총인구(국가데이터처 자료제공). 행정동 주민등록과 r 0.99</td></tr>
    <tr><th>E2</th><td>행안부 행정동 연령별 주민등록(2026-10) 9세 이하+65세 이상 비율을 격자 인구로 가중 (${u.E2_basis})</td></tr>
    <tr><th>D1·신규 수혜</th><td>청주시 도시공원정보(2025-11) − 미조성공원 현황(2026-09) = 기존 공원, 공원구분별 유치거리 원. 버퍼 인구 중 그 밖에 사는 사람</td></tr>
    <tr><th>D2</th><td>${D.U.zones.source}${u.living_zone==='도심생활권'?' · 도심생활권 배정은 가정':''}</td></tr>
    <tr><th>C1</th><td>토지피복지도 2025 산림 ${D.U.params.axis_forest_min_ha}ha 이상 + OSM 주요 하천(${D.U.params.axis_rivers.slice(0,4).join('·')} 등). 녹지축 도면 대체</td></tr>
    <tr><th>지역 유형</th><td>인구밀도 ${A.dense_per_km2.toLocaleString('ko-KR')}명/㎢ 이상 밀집, ${A.residential_per_km2.toLocaleString('ko-KR')}명/㎢ 또는 주거 ${A.residential_share*100}% 이상 주거, 공업 ${A.industrial_share*100}% 이상 산업 (가정)</td></tr>
    </table></details>`;
}
function useList(){
  const ps=[...D.parks].sort((a,b)=>(U(b).new_served_pop??-1)-(U(a).new_served_pop??-1));
  $('list').innerHTML=ps.map(p=>`<button role="listitem" data-id="${p.id}" aria-current="${S.sel===p.id}"><span class="n">${p.id}</span>
    <span style="min-width:0"><span style="display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${p.name} <span class="meta">${p.loc.split(' ').slice(-1)[0]}</span></span>
    <span class="mini" title="서비스권 밖 ${pct(U(p).D1_unserved)}"><i style="width:${(U(p).D1_unserved||0)*100}%;background:var(--seq2)"></i></span></span>
    <span class="v">${useOK(p)?nf(U(p).new_served_pop)+'명':'미산정'}</span></button>`).join('');
  $('list').querySelectorAll('button').forEach(b=>b.onclick=()=>select(+b.dataset.id, S.view==='park'));
}
function useChart(){
  const ps=[...D.parks].sort((a,b)=>(U(b).new_served_pop??-1)-(U(a).new_served_pop??-1));
  $('userows').innerHTML=ps.map(p=>{const u=U(p); return `<div class="crow"><span class="nm" title="${p.name}">${p.name}</span>
    ${useOK(p)?`<span class="cbar" style="position:relative;background:var(--soft)" title="버퍼 인구 ${nf(u.E1_pop)}명 · 신규 수혜 ${nf(u.new_served_pop)}명"><span style="position:absolute;left:0;width:${u.E1_pop/maxE1*100}%;height:100%;background:var(--seq1);opacity:.45"></span><span style="position:absolute;left:0;width:${u.new_served_pop/maxE1*100}%;height:100%;background:var(--seq2)"></span></span>`:'<span class="meta">미산정</span>'}
    <span class="num">${useOK(p)?nf(u.new_served_pop):'—'}</span><span class="num pc">${useOK(p)?pct(u.D1_unserved):''}</span></div>`;}).join('');
}
function cityColor(p){
""")
R("  if(S.topic==='heat') return heatColor(p);", "  if(S.topic==='heat') return heatColor(p);\n  if(S.topic==='use') return useColor(p);")
R("function cityHeight(p){\n", """function cityHeight(p){
  if(S.topic==='use'){ const u=U(p); if(!useOK(p)) return 0;
    if(S.heightCity==='new') return Math.sqrt((u.new_served_pop||0)/maxNew)*6000;
    if(S.heightCity==='e1') return Math.sqrt((u.E1_pop||0)/maxE1)*6000; return 0; }
""")
R("<br>${S.topic==='heat'?(heatOK(p)?", "<br>${S.topic==='use'?useTip(p):S.topic==='heat'?(heatOK(p)?")
R("  if(S.view==='city' && S.topic==='heat'){\n", "  if(S.view==='city' && S.topic==='use'){ h=useLegend(); }\n  else if(S.view==='city' && S.topic==='heat'){\n")
R("""<button data-tp="heat" aria-pressed="${S.topic==='heat'}">열저감 (지표온도)</button>""",
  """<button data-tp="heat" aria-pressed="${S.topic==='heat'}">열저감 (지표온도)</button><button data-tp="use" aria-pressed="${S.topic==='use'}">이용성 (주민·생활권)</button>""")
R("  if(S.topic==='heat'){ $('card').innerHTML=topicTabs()+(p?heatCard(p):heatSummary()); bindTabs(); return; }",
  "  if(S.topic==='use'){ $('card').innerHTML=topicTabs()+(p?useCard(p):useSummary()); bindTabs(); return; }\n  if(S.topic==='heat'){ $('card').innerHTML=topicTabs()+(p?heatCard(p):heatSummary()); bindTabs(); return; }")
R("function list(){\n", "function list(){\n  if(S.topic==='use') return useList();\n")
R("""    <div id="heatrows"></div>
    </div>
""", """    <div id="heatrows"></div>
    </div>
    <div id="usechart" hidden>
    <h2>공원별 신규 수혜 인구 — 버퍼 인구 중 지금 공원 유치권 밖에 사는 사람</h2>
    <div class="meta" style="margin-bottom:10px">옅은 막대 = 버퍼 인구(E1), 진한 막대 = 그중 기존 공원 유치권 밖(신규 수혜 인구). 오른쪽은 D1 서비스권 밖 비율.</div>
    <div class="chead"><span>공원</span><span>인구 (명)</span><span style="text-align:right">신규 수혜</span><span class="pc" style="text-align:right">D1</span></div>
    <div id="userows"></div>
    </div>
""")
R("  $('bizchart').hidden=S.topic==='heat'; $('heatchart').hidden=S.topic!=='heat';",
  "  $('bizchart').hidden=S.topic!=='biz'; $('heatchart').hidden=S.topic!=='heat'; $('usechart').hidden=S.topic!=='use';\n  if(S.topic==='use'){ useChart(); return; }")
R("  ['biz','heat'].forEach(k=>$('tp-'+k).setAttribute('aria-pressed',k===tp));\n  S.colorCity = tp==='heat'?'kind':'pub'; S.heightCity = tp==='heat'?'cool':'cost';\n  S.colorPark = tp==='heat'?'use':'cost';",
  "  ['biz','heat','use'].forEach(k=>$('tp-'+k).setAttribute('aria-pressed',k===tp));\n  S.colorCity = {biz:'pub',heat:'kind',use:'d1'}[tp]; S.heightCity = {biz:'cost',heat:'cool',use:'new'}[tp];\n  S.colorPark = tp==='biz'?'cost':'use';")
R("$('tp-biz').onclick=()=>setTopic('biz'); $('tp-heat').onclick=()=>setTopic('heat');", "$('tp-biz').onclick=()=>setTopic('biz'); $('tp-heat').onclick=()=>setTopic('heat'); $('tp-use').onclick=()=>setTopic('use');")
R("지표온도(기온 아님).</footer>", "지표온도(기온 아님). 이용성: SGIS 2024 100m 격자 인구(국가데이터처)·행안부 연령별 주민등록(2026-10)·청주시 도시공원정보(2025-11)·미조성공원 현황(2026-09)·V-World 주소 검색·환경부 토지피복지도 2025·OSM 하천·2030 청주시 공원녹지기본계획, build_edc.py 산출.</footer>")

open(f'{C}/total_template.html', 'w', encoding='utf-8').write(t)
print('total/code/total_template.html', len(t))
