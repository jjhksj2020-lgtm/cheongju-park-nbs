// 발표용 페이지 — 지도 앱의 데이터 D(세 파트 결과)만 읽어 숫자를 만든다. 지도 앱 함수에는 기대지 않는다(지도 엔진을 못 불러와도 설명 페이지는 뜨게).
(function(){
const P = D.parks, EM = D.E, UM = D.U, R = D.rule;
const $ = id => document.getElementById(id);
const E = p => p.E||{}, U = p => p.U||{};
const heatOK = p => E(p).status==='산정', useOK = p => U(p).status==='산정';
const nf = v => v==null?'—':Math.round(v).toLocaleString('ko-KR');
const f = (v,d=1) => v==null?'—':(+v).toLocaleString('ko-KR',{minimumFractionDigits:d,maximumFractionDigits:d});
const eok = v => v==null?'—':Math.round(v/1e8).toLocaleString('ko-KR');
const pc = v => v==null?'—':Math.round(v*100)+'%';
const sum = (a,g) => a.reduce((s,x)=>s+(g(x)||0),0);
const man = v => (v/1e4).toLocaleString('ko-KR',{maximumFractionDigits:1});

// ---------- 공통 조각 ----------
const kpi = (l,v,u,c,hl) => `<div class="pz-kpi${hl?' hl':''}"><div class="l">${l}</div><div class="v">${v}${u?`<small>${u}</small>`:''}</div>${c?`<div class="c">${c}</div>`:''}</div>`;
const stepc = (k,t,d,fm,s,key) => `<div class="pz-stepc${key?' key':''}"><div class="k">${k}</div><div class="t">${t}</div><div class="d">${d}</div>${fm?`<div class="f">${fm}</div>`:''}${s&&s!=='—'?`<div class="s">자료 · ${s}</div>`:''}</div>`;
const more = (title, body) => `<details class="pz-more"><summary>${title}</summary>${body}</details>`;
const dl = rows => `<dl class="pz-dl">${rows.map(([a,b])=>`<dt>${a}</dt><dd>${b}</dd>`).join('')}</dl>`;
function rank(rows, max, fmt, segs){ // rows: [{p, v, segs?}] 한 색 막대(또는 두 칸)
  return `<div class="pz-rank">${rows.map((r,i)=>`<div class="pz-r" title="${r.p.name} · ${fmt(r)}"><span class="no">${i+1}</span><span class="nm">${r.p.name}<small>${r.p.loc.split(' ').slice(-1)[0]} · ${r.p.type}</small></span>
    <span class="tr">${(r.segs||[[r.v,'var(--tc)']]).filter(s=>s[0]>0).map(([v,c])=>`<span style="width:${Math.max(.4,v/max*100)}%;background:${c}"></span>`).join('')}</span>
    <span class="val">${fmt(r)}</span></div>`).join('')}</div>`;
}
const head = (tp,no,label,q) => `<div class="pz-eyebrow">${no} · ${label}</div><h2 class="pz-h2">${q}</h2>`;
const sec = (n,t,body,extra='') => `<section class="pz-block" ${extra}><h3 class="pz-h3"><span class="n">${n}</span>${t}</h3>${body}</section>`;
const dash = (tp,tip) => `<section class="pz-block pz-dash"><div class="pz-dash-head"><h3 class="pz-h3" style="margin:0"><span class="n">3</span>대시보드</h3><span class="tip">${tip}</span></div><div class="pz-slot" id="slot-${tp}"></div></section>`;

// ---------- 1. 주제·목적 ----------
const n = P.length, early = P.filter(p=>p.expiry<=PZ.stage1_expiry_max).length;
const small = P.filter(p=>/소공원|어린이공원/.test(p.type)).length;
const yrs = P.map(p=>p.expiry), y0=Math.min(...yrs), y1=Math.max(...yrs);
// 표지 지도: 청주시 4개 구 경계 + 공원 40곳 위치 (SVG, 지도 엔진 없이)
function cityMap(){
  const rings = D.gu.flatMap(g=>g.poly.map(pg=>({name:g.name, r:pg[0]})));
  const xs = rings.flatMap(o=>o.r.map(c=>c[0])), ys = rings.flatMap(o=>o.r.map(c=>c[1]));
  const x0=Math.min(...xs), x1=Math.max(...xs), y0g=Math.min(...ys), y1g=Math.max(...ys), k=Math.cos((y0g+y1g)/2*Math.PI/180);
  const W=420, sc=W/((x1-x0)*k), H=Math.round((y1g-y0g)*sc), pad=10;
  const X=lon=>pad+(lon-x0)*k*sc, Y=lat=>pad+(y1g-lat)*sc;
  const path = r => 'M'+r.map(c=>X(c[0]).toFixed(1)+','+Y(c[1]).toFixed(1)).join('L')+'Z';
  const cen = r => [r.reduce((a,c)=>a+c[0],0)/r.length, r.reduce((a,c)=>a+c[1],0)/r.length];
  const dots = [...P].filter(p=>p.c).sort((a,b)=>b.expiry-a.expiry).map(p=>`<circle cx="${X(p.c[0]).toFixed(1)}" cy="${Y(p.c[1]).toFixed(1)}" r="4.2" fill="${p.expiry<=PZ.stage1_expiry_max?'#1a2230':'#b0aca2'}" stroke="#fff" stroke-width="1.4"><title>${p.name} · ${p.loc} · 실효 ${p.expiry}</title></circle>`).join('');
  return `<svg viewBox="0 0 ${W+pad*2} ${H+pad*2}" role="img" aria-label="청주시 구 경계와 장기미집행 공원 ${n}곳 위치">
    ${rings.map((o,i)=>`<path d="${path(o.r)}" fill="${['#eef1ec','#e8ece6','#f1f2ee','#e9ede8'][i%4]}" stroke="#fff" stroke-width="2" stroke-linejoin="round"/>`).join('')}
    ${rings.map(o=>`<path d="${path(o.r)}" fill="none" stroke="#9aa39b" stroke-width=".8" stroke-linejoin="round"/>`).join('')}
    ${rings.map(o=>{const c=cen(o.r);return `<text x="${X(c[0]).toFixed(0)}" y="${Y(c[1]).toFixed(0)}" text-anchor="middle" font-size="13" font-weight="700" fill="#9aa39b" style="letter-spacing:.1em">${o.name}</text>`}).join('')}
    ${dots}</svg>
    <div class="lg"><span><i style="background:#1a2230"></i>${PZ.stage1_expiry_max}년까지 실효</span><span><i style="background:#b0aca2"></i>그 이후 실효</span></div>`;
}
const pIntro = `<div class="pz-hero"><div>
  <div class="pz-eyebrow" style="--tc:var(--pz-ink2)">청주시 공고 제2026-2004호 · 장기미집행 도시공원 ${n}개소</div>
  <h1 class="pz-h1">어떤 공원부터<br>먼저 만들어야 하는가</h1>
  <p class="pz-lead">청주시에는 공원으로 지정만 되고 아직 만들지 못한 땅이 <b>${n}곳</b> 있습니다. 이 땅들은 ${y0}년부터 ${y1}년 사이에 차례로 <b>공원 지정이 풀립니다(실효)</b>. 한꺼번에 조성하기는 어렵기 때문에, <b>무엇을 기준으로 순서를 정할지</b>를 데이터로 제시합니다.</p>
</div><div class="pz-cmap">${cityMap()}</div></div>
<div class="pz-kpis" style="--cols:4;margin-top:26px">
  ${kpi('대상 공원',n,'곳',`소공원·어린이공원 ${small}곳, 근린·주제공원 ${n-small}곳`)}
  ${kpi('실효 시점',`${y0}–${y1}`,'',`${PZ.stage1_expiry_max}년까지 ${early}곳이 먼저 풀림`)}
  ${D.R?kpi('평가 단계','3','단계','현황·유형 → 조성형 순위 → 에너지·탄소'):kpi('평가 기준','3','가지','이용성 · 에너지저감 · 사업성')}
  ${kpi('시 부담 추정',`${eok(sum(P,p=>p.minL))}–${eok(sum(P,p=>p.maxH))}`,'억 원','40곳 전체, 땅 보상 + 공원 조성')}
</div>`;

// ---------- 3. 평가 기준 (세 가지 눈과 순서) ----------
const pFrame = `<div class="pz-eyebrow" style="--tc:var(--pz-ink2)">평가 기준</div>
<h2 class="pz-h2">세 가지 눈으로 봅니다</h2>
<p class="pz-lead" style="margin-top:10px">공원 하나를 <b>세 가지 질문</b>으로 차례로 봅니다. 앞의 두 질문은 <b>어떤 공원이 먼저여야 하는지</b>를, 마지막 질문은 <b>언제·어떤 돈으로 할 수 있는지</b>를 답합니다.</p>
<div class="pz-lenses pz-order">
  <button class="pz-lens" style="--tc:var(--pz-use)" data-go="use"><span class="k">① 필요한가</span><span class="t">이용성</span><span class="q">누가 이 공원을 쓰게 되나?</span><span class="d">주변에 사는 사람 중 지금 걸어서 갈 공원이 없는 사람이 얼마나 되는지 봅니다.</span><span class="m">핵심 지표 · 신규 수혜 인구(명)</span><span class="go">자세히 →</span></button>
  <button class="pz-lens" style="--tc:var(--pz-heat)" data-go="heat"><span class="k">② 효과가 있는가</span><span class="t">에너지저감</span><span class="q">만들면 여름이 얼마나 시원해지나?</span><span class="d">녹지가 늘어 여름철 땅 온도가 얼마나 내려가는지 청주 위성 실측으로 봅니다.</span><span class="m">핵심 지표 · 냉각량(°C·ha)</span><span class="go">자세히 →</span></button>
  <button class="pz-lens" style="--tc:var(--pz-biz)" data-go="biz"><span class="k">③ 할 수 있는가</span><span class="t">사업성</span><span class="q">시가 얼마를 내고, 언제 할 수 있나?</span><span class="d">땅 주인과 땅값으로 시 부담을 계산하고, 실효 시기와 재원으로 단계를 나눕니다.</span><span class="m">핵심 지표 · 시 부담(억 원) · 집행 단계</span><span class="go">자세히 →</span></button>
</div>
<section class="pz-block"><h3 class="pz-h3">왜 이 순서인가</h3>
  <div class="pz-steps3 pz-why3">
    <div style="--tc:var(--pz-use)"><div class="t"><span>1</span>쓰일 곳인가가 출발점</div><div class="d">공원은 시민이 이용하는 시설입니다. 주변에 사람이 없거나 이미 공원이 충분한 곳이라면 새로 만들 이유가 약합니다. 그래서 <b>필요(이용성)</b>를 먼저 봅니다.</div></div>
    <div style="--tc:var(--pz-heat)"><div class="t"><span>2</span>같은 필요라면 효과가 큰 곳</div><div class="d">녹지를 새로 만드는 공원은 여름철 열을 낮춰 도시 전체에 이익이 됩니다. 필요가 비슷한 공원 사이에서 <b>환경 효과(에너지저감)</b>로 우선순위를 더 가립니다.</div></div>
    <div style="--tc:var(--pz-biz)"><div class="t"><span>3</span>마지막으로 실현 가능성</div><div class="d">필요하고 효과가 있는 공원이라도 재원과 시기가 맞아야 실행됩니다. <b>사업성</b>은 앞의 판단을 바꾸기보다, <b>언제·어떤 돈으로</b> 할지를 정합니다.</div></div>
  </div>
  ${more('상세보기 — 청주시 평가 기준과의 연결', dl([
    ['① 공원조성 가치','에너지저감(환경 효과) · 녹지·수변축과의 연결은 이용성의 참고 지표로'],
    ['② 이용성','이용성 — 주변 인구, 공원 공백, 신규 수혜 인구'],
    ['③ 개발압력','조성했을 때와 지금 그대로일 때를 비교하는 평가라 따로 점수로 다루지 않음'],
    ['④ 재정여건 · ⑤ 기존투자','사업성 — 시 부담, 외부 재원, 집행 단계']]))}
</section>`;

// ---------- 2. 공원이란 ----------
const TYPES = [
  ['소공원','소규모 휴식 공간','도시 안 자투리 땅을 활용한 작은 쉼터'],
  ['어린이공원','어린이 놀이·안전','어린이의 보건과 정서를 위한 동네 놀이 공간'],
  ['근린공원','동네 주민의 휴양','가까운 주민의 산책·운동·휴식을 위한 공원'],
  ['역사공원','주제공원','유적·유물 등 역사 자원을 활용한 공원'],
  ['문화공원','주제공원','지역의 문화적 특징을 살린 공원'],
  ['생태공원','주제공원','하천·습지 등 자연 생태를 보전·학습하는 공원']];
const tcount = Object.fromEntries(TYPES.map(([t])=>[t,P.filter(p=>p.type===t).length]));
const tmax = Math.max(...Object.values(tcount));
const ycount = {}; for(let y=y0;y<=y1;y++) ycount[y]=P.filter(p=>p.expiry===y).length;
const ymax = Math.max(...Object.values(ycount));
const pPark = `<div class="pz-divider"><span class="pz-eyebrow" style="--tc:var(--pz-ink2)">배경</span><h2 class="pz-h2">공원이란, 그리고 장기미집행 공원이란</h2></div>
<p class="pz-lead"><b>도시공원</b>은 도시의 자연경관을 지키고 시민의 건강·휴양·정서 생활을 높이기 위해 <b>도시관리계획으로 결정한 공원</b>입니다(도시공원 및 녹지 등에 관한 법률). 공원으로 결정했지만 아직 땅을 사거나 조성하지 못한 곳이 <b>장기미집행 공원</b>입니다.</p>
<div class="pz-two" style="margin-top:6px">
  <section class="pz-block"><h3 class="pz-h3">도시공원의 종류와 이번 대상</h3>
    <p class="pz-cap">대상 ${n}곳의 유형별 개수. 생활권공원(소공원·어린이공원·근린공원)이 대부분입니다.</p>
    <div class="pz-types">${TYPES.map(([t,k,d])=>`<div class="pz-type" title="${d}"><span class="nm">${t}<small>${k}</small></span><span class="tr"><span style="width:${tcount[t]/tmax*100}%"></span></span><span class="c">${tcount[t]}곳</span></div>`).join('')}</div>
    ${more('상세보기 — 유형별 설명', dl(TYPES.map(([t,k,d])=>[t,`${d}. 걸어서 이용하는 거리(유치거리) ${UM.buffer_m[t]}m로 계산`])))}
  </section>
  <section class="pz-block"><h3 class="pz-h3">언제 공원 지정이 풀리나 (실효 연도)</h3>
    <p class="pz-cap">공원으로 결정된 뒤 20년 안에 조성하지 못하면 결정의 효력이 사라집니다(국토계획법 제48조). <span style="color:var(--pz-ink);font-weight:600">■</span> ${PZ.stage1_expiry_max}년까지 실효되는 곳</p>
    <div class="pz-years">${Object.entries(ycount).map(([y,c])=>`<div class="pz-y${c?'':' empty'}${+y<=PZ.stage1_expiry_max?' urg':''}" title="${y}년 ${c}곳"><b>${c||''}</b><span style="height:${c/ymax*120}px"></span><em>${String(y).slice(2)}</em></div>`).join('')}</div>
    <p class="pz-cap" style="margin:8px 0 0">가로축: 실효 연도(20XX년) · 세로: 공원 수</p>
  </section>
</div>
<section class="pz-block"><h3 class="pz-h3">왜 순서를 정해야 하나</h3>
  <div class="pz-steps3">
    <div><div class="t">실효되면 되돌리기 어렵다</div><div class="d">공원 지정이 풀리면 그 땅은 다른 용도로 개발될 수 있어, 도심의 녹지와 휴식 공간이 사라집니다.</div></div>
    <div><div class="t">조성에는 큰돈이 든다</div><div class="d">사유지는 시가 보상하고 사들여야 합니다. ${n}곳 전체의 시 부담은 최대 약 ${eok(sum(P,p=>p.maxH))}억 원으로 추정됩니다.</div></div>
    <div><div class="t">그래서 근거 있는 순서가 필요하다</div><div class="d">시민에게 쓰임이 크고, 환경 효과가 있고, 재정적으로 가능한 곳부터 — 다음 장의 세 가지 기준으로 봅니다.</div></div>
  </div>
</section>`;

// ---------- 3. 이용성 ----------
const UO = P.filter(useOK), uNew = sum(UO,p=>U(p).new_served_pop), uPop = sum(UO,p=>U(p).E1_pop);
const uTop = [...UO].sort((a,b)=>U(b).new_served_pop-U(a).new_served_pop);
const u5 = uTop.slice(0,5), u5s = sum(u5,p=>U(p).new_served_pop);
const uMiss = P.filter(p=>!useOK(p)).map(p=>p.name).join('·');
const B = UM.buffer_m;
const pUse = `${head('use',D.R?'부록':'기준 1','이용성','누가 이 공원을 쓰게 되나?')}
<section class="pz-block pz-why"><h3 class="pz-h3"><span class="n">1</span>왜 보나</h3><p>공원은 <b>사람이 이용할 때</b> 가치가 생깁니다. 주변에 사는 사람이 많고, 그중 <b>지금 걸어서 갈 만한 공원이 없는 사람</b>이 많을수록 새로 만들었을 때 혜택이 큽니다.</p>
  <ul><li>청주시 기준 ② 이용성</li><li>걸어서 이용하는 거리 기준</li><li>100m 격자 실제 인구</li></ul></section>
${sec(2,'평가 구조',`<div class="pz-flow" style="--cols:3">
  ${stepc('① 주변 인구','공원 주변에 몇 명이 사나',`공원 경계에서 걸어서 오는 거리 안에 사는 사람 수. 소공원·어린이공원 ${B['소공원']}m, 근린·주제공원 ${B['근린공원']}m.`,'주변 인구 (E1)','국가데이터처 SGIS 2024 100m 격자')}
  ${stepc('② 공원 공백','그중 공원이 없는 사람은',`주변 인구 중 기존 공원의 이용 거리 밖에 사는 사람의 비율.`,'공백 비율 (D1)','청주시 도시공원정보 · 미조성공원 현황')}
  ${stepc('③ 신규 수혜 인구','새로 혜택을 받는 사람',`이 공원을 만들면 <b>처음으로</b> 걸어서 갈 공원이 생기는 사람 수. 순위의 기준입니다.`,'① × ② = 신규 수혜 인구','—',true)}
</div>
${more('상세보기 — 함께 보는 참고 지표와 가정', dl([
  ['아동·고령 비율 (E2)','주변 인구 중 9세 이하 + 65세 이상 비율. 행정안전부 행정동 연령별 주민등록(2026-10)'],
  ['생활권 1인당 공원면적 (D2)',`공원이 속한 생활권의 1인당 조성 공원면적. 도심생활권 ${UM.zones.per_cap_built['도심생활권']}㎡로 가장 적음 (2030 청주시 공원녹지기본계획)`],
  ['녹지·수변축 거리 (C1)',`큰 산림(${UM.params.axis_forest_min_ha}ha 이상) 또는 주요 하천까지 거리. 녹지축 도면 대신 토지피복지도·OSM 사용(대체자료)`],
  ['인구 자료 검증','100m 격자 인구를 행정동 주민등록 인구와 비교: 상관계수 0.99'],
  ['기존 공원','청주시 도시공원정보(2025-11)에서 미조성 공원을 뺀 공원. 위치는 면적이 같은 원으로 가정']]))}`)}
${dash('use','색 = 공원 공백 비율 · 3D 기둥 = 신규 수혜 인구 · 공원을 누르면 오른쪽에 근거')}
${sec(4,'결과',`<div class="pz-kpis" style="--cols:4">
  ${kpi('신규 수혜 인구 합계',nf(uNew),'명',`${UO.length}곳 산정 (${uMiss} 경계 없음)`)}
  ${kpi('주변 인구 합계',nf(uPop),'명','공원별 이용 거리 안')}
  ${kpi('1위',u5[0].name,'',`신규 수혜 ${nf(U(u5[0]).new_served_pop)}명`,true)}
  ${kpi('상위 5곳 비중',pc(u5s/uNew),'','신규 수혜 인구 중')}
</div>
<div class="pz-res"><div><p class="pz-sub">신규 수혜 인구 상위 5곳</p><div class="pz-legend" style="margin-top:2px"><span><i style="background:var(--pz-use)"></i>신규 수혜 인구</span><span><i style="background:#cfe3d8"></i>주변 인구 중 이미 공원이 있는 사람</span></div>
  ${rank(u5.map(p=>({p,v:U(p).new_served_pop,segs:[[U(p).new_served_pop,'var(--pz-use)'],[U(p).E1_pop-U(p).new_served_pop,'#cfe2d7']]})), Math.max(...u5.map(p=>U(p).E1_pop)), r=>`${nf(r.v)}명<small>공백 ${pc(U(r.p).D1_unserved)}</small>`)}</div>
  <div class="pz-take" style="--tc:var(--pz-use)"><div class="h">해석</div>
  <p><b>${u5[0].name}</b>은 주변 ${nf(U(u5[0]).E1_pop)}명 중 ${nf(U(u5[0]).new_served_pop)}명이 지금 걸어서 갈 공원이 없어, 조성 시 혜택을 받는 사람이 가장 많습니다.</p>
  <ul><li>상위 5곳이 전체 신규 수혜 인구의 ${pc(u5s/uNew)}를 차지합니다.</li><li>주변에 공원이 이미 있으면 인구가 많아도 순위가 낮습니다.</li></ul></div></div>
${more('상세보기 — '+UO.length+'곳 전체 표', `<table class="pz-t"><thead><tr><th>순위</th><th>공원</th><th>위치</th><th class="r">주변 인구</th><th class="r">공백 비율</th><th class="r">신규 수혜</th><th class="r">아동·고령</th><th class="r">생활권 1인당</th></tr></thead><tbody>
  ${uTop.map((p,i)=>{const u=U(p);return `<tr><td>${i+1}</td><td>${p.name}</td><td>${p.loc}</td><td class="r">${nf(u.E1_pop)}</td><td class="r">${pc(u.D1_unserved)}</td><td class="r">${nf(u.new_served_pop)}</td><td class="r">${pc(u.E2_vulnerable)}</td><td class="r">${u.D2_built_m2_per_cap}㎡</td></tr>`}).join('')}</tbody></table>`)}`)}`;

// ---------- 4. 에너지저감 ----------
const HO = P.filter(heatOK), hSum = sum(HO,p=>E(p).cool_base), hLo = sum(HO,p=>E(p).cool_low), hHi = sum(HO,p=>E(p).cool_high);
const hTop = [...HO].sort((a,b)=>E(b).cool_base-E(a).cool_base), h5 = hTop.slice(0,5);
const hBuild = HO.filter(p=>E(p).kind==='조성형'), hKeep = HO.filter(p=>E(p).kind==='보전형');
const hStable = HO.filter(p=>E(p).grade_stable==='확정').length;
const yr = s => s.slice(0,4);
const e1 = E(h5[0]);
const pHeat = `${head('heat',D.R?'부록':'기준 2','에너지저감','공원을 만들면 여름이 얼마나 시원해지나?')}
<section class="pz-block pz-why" style="--tc:var(--pz-heat)"><h3 class="pz-h3"><span class="n">1</span>왜 보나</h3><p>녹지는 여름철 땅의 온도를 낮춰 도심 열섬과 <b>냉방 에너지 부담</b>을 줄입니다. 지금 녹지가 적은 곳에 공원을 만들수록 효과가 큽니다. 이 평가는 근거가 확실한 범위까지만 계산해, <b>청주 위성으로 실제 측정한 온도 변화(°C)</b>로 효과를 나타냅니다.</p>
  <ul><li>청주시 기준 ① 공원조성 가치(환경)</li><li>청주 위성 실측 계수만 사용</li><li>판정에 넣지 않는 참고 지표</li></ul></section>
${sec(2,'평가 구조',`<div class="pz-flow" style="--cols:4">
  ${stepc('① 녹지 증가','얼마나 더 푸르러지나',`지금 녹지 점수(NDVI, 0~1)에서 공원 조성 후 점수(잔디 ${f(EM.target.grass,2)} ~ 숲 ${f(EM.target.tree,2)})까지의 차이. 이미 숲이면 0.`,'목표 − 지금 녹지','Sentinel-2 위성 여름 영상')}
  ${stepc('② 공원 일대 온도','몇 도 내려가나',`녹지 1만큼 늘면 −${f(EM.coef.green,1)}~−${f(EM.coef.loss,1)}°C. 청주에서 녹지가 실제로 변한 ${nf(EM.change.all_n)}개 지점(${yr(EM.periods.before[0])}–${yr(EM.periods.before[1])} → ${yr(EM.periods.after[0])}–${yr(EM.periods.after[1])})에서 구한 값.`,'녹지 증가 × 계수','Landsat 8·9 지표온도')}
  ${stepc('③ 주변 300m','주변까지 퍼지나',`1ha 이상 공원은 주변 ${EM.ring_m}m도 함께 시원해짐. 퍼지는 비율 ${f(EM.factors.spill[0],2)}~${f(EM.factors.spill[1],2)}은 특례사업지(${EM.spill_sites.join('·')}) 개발 전후 실측.`,'② × 퍼짐 비율','특례사업지 전후 위성 비교')}
  ${stepc('④ 냉각량','얼마나 넓게 시원해지나',`내려가는 온도에 그 면적(ha)을 곱한 값. 공원 간 비교·순위의 기준입니다.`,'°C × ha = 냉각량(°C·ha)','—',true)}
</div>
<div class="pz-note"><b>측정 단위에 대해</b> — 전력(kWh)으로 바꾸는 계산은 해외·도시 전체 계수를 여러 번 겹쳐야 해서 근거가 약해 제외했습니다. 대신 청주에서 직접 잰 온도 변화만으로 평가합니다.</div>
${more('상세보기 — 계산 가정과 보정', dl([
  ['작은 공원 보정',`위성 열 영상은 약 100m 칸(1ha)으로 봅니다. 1ha보다 작은 공원은 그 칸의 일부만 바뀌므로 면적 비율만큼만 반영`],
  ['보전형 / 조성형',`지금 녹지가 잔디 수준(${f(EM.target.grass,3)}) 이상이면 보전형(이미 푸름), 미만이면 조성형(새로 녹지를 만듦)`],
  ['시나리오',`목표 녹지(잔디·숲) × 계수(늘어난 곳·줄어든 곳) × 퍼짐 비율(2곳) = ${EM.n_scen}가지. 기준값은 각 범위의 중간`],
  ['등급','시나리오마다 냉각량 순위로 상(상위 25%)·중(50%)·하 → 모든 시나리오에서 같으면 확정'],
  ['지표온도','위성이 재는 땅 표면 온도이며, 사람이 느끼는 기온과는 다름'],
  ['제외',`${P.filter(p=>!heatOK(p)).map(p=>p.name).join('·')} — 경계 없음 또는 하천 위주라 녹지 계산이 맞지 않음`]]))}`,`style="--tc:var(--pz-heat)"`)}
${dash('heat','색 = 공원 성격(조성형·보전형) · 3D 기둥 = 냉각량 · 공원을 누르면 ①~④ 계산 근거').replace('class="pz-block pz-dash"','class="pz-block pz-dash" style="--tc:var(--pz-heat)"')}
${sec(4,'결과',`<div class="pz-kpis" style="--cols:4">
  ${kpi('냉각량 합계',f(hSum,1),'°C·ha',`범위 ${f(hLo,1)}~${f(hHi,1)} (${EM.n_scen}개 시나리오)`)}
  ${kpi('1위',h5[0].name,'',`전체의 ${pc(e1.cool_base/hSum)} · 공원 일대 −${f(e1.dlst_cell_base,2)}°C`,true)}
  ${kpi('조성형',hBuild.length,'곳',`냉각량의 ${pc(sum(hBuild,p=>E(p).cool_base)/hSum)} — 녹지를 새로 만드는 곳`)}
  ${kpi('보전형',hKeep.length,'곳','이미 푸른 곳 — 지키는 것이 핵심')}
</div>
<div class="pz-res"><div><p class="pz-sub">냉각량 상위 5곳</p><p class="pz-cap">막대 = 냉각량(°C·ha, 기준 시나리오)</p>
  ${rank(h5.map(p=>({p,v:E(p).cool_base})), E(h5[0]).cool_base, r=>`${f(r.v,2)}<small>${E(r.p).kind} · 등급 ${E(r.p).grade_range}</small>`)}</div>
  <div class="pz-take" style="--tc:var(--pz-heat)"><div class="h">해석</div>
  <p><b>${h5[0].name}</b>(${f(h5[0].area/1e4,1)}ha) 한 곳이 전체 냉각량의 ${pc(e1.cool_base/hSum)}를 차지합니다. 지금 녹지가 적은(${f(e1.ndvi_now,2)}) 도심 공원이라, 조성하면 공원 일대 −${f(e1.dlst_cell_base,2)}°C, 주변 ${EM.ring_m}m −${f(e1.dlst_ring_base,2)}°C 효과가 납니다.</p>
  <ul><li>작은 공원은 위성으로 보이는 효과가 작습니다.</li><li>이미 숲인 보전형은 효과가 거의 0 — 지키는 것 자체가 가치입니다.</li><li>등급 확정 ${hStable}곳, 나머지는 가정에 따라 등급이 바뀌는 경계.</li></ul></div></div>
${more('상세보기 — '+HO.length+'곳 전체 표', `<table class="pz-t"><thead><tr><th>순위</th><th>공원</th><th>성격</th><th class="r">지금 녹지</th><th class="r">공원 일대</th><th class="r">주변 300m</th><th class="r">냉각량 (범위)</th><th>등급</th></tr></thead><tbody>
  ${hTop.map((p,i)=>{const e=E(p);return `<tr><td>${i+1}</td><td>${p.name}</td><td>${e.kind}</td><td class="r">${f(e.ndvi_now,2)}</td><td class="r">−${f(e.dlst_cell_base,2)}°C</td><td class="r">${e.ring_applied==='적용'?'−'+f(e.dlst_ring_base,2)+'°C':'—'}</td><td class="r">${f(e.cool_base,2)} (${f(e.cool_low,2)}~${f(e.cool_high,2)})</td><td>${e.grade_range} · ${e.grade_stable}</td></tr>`}).join('')}</tbody></table>`)}`,`style="--tc:var(--pz-heat)"`)}`;

// ---------- 5. 사업성 ----------
const bMax = sum(P,p=>p.maxH), bMin = sum(P,p=>p.minL);
const st1 = P.filter(p=>p.stage==='1단계'), st1Max = sum(st1,p=>p.maxH);
const pubA = P.filter(p=>p.pub!=null&&p.type!=='생태공원'), pubShare = sum(pubA,p=>p.area*p.pub)/sum(pubA,p=>p.area);
const allPub = P.filter(p=>p.pub===1).length, spec = P.filter(p=>p.special);
const bTop = [...P].sort((a,b)=>(b.maxH||0)-(a.maxH||0)), b5 = bTop.slice(0,5);
const W = PZ.wolmyeong, wComp = W.area_m2*R.high, wCons = W.area_m2*R.klow;
const pBiz = `${head('biz',D.R?'④ 실행':'기준 3','사업성','시가 얼마를 내야 하고, 언제 할 수 있나?')}
<section class="pz-block pz-why" style="--tc:var(--pz-biz)"><h3 class="pz-h3"><span class="n">1</span>왜 보나</h3><p>${n}곳을 실효 전에 모두 조성하기에는 재원이 한정되어 있습니다. <b>땅 주인과 땅값</b>으로 시가 실제로 낼 돈을 계산하고, <b>실효 시기와 외부 재원</b>으로 먼저 할 곳(1단계)과 나중에 할 곳(2단계)을 나눕니다.</p>
  <ul><li>청주시 기준 ④ 재정여건 · ⑤ 기존투자</li><li>필지 단위 소유·공시지가</li><li>청주 실제 사업비로 검증</li></ul></section>
${sec(2,'평가 구조',`<div class="pz-flow" style="--cols:4">
  ${stepc('① 땅 주인 확인','누구 땅인가','공원 경계 안 필지마다 국·공유지인지 사유지인지 확인. 국·공유지는 사들이지 않습니다.','국공유 비율','V-World 토지소유정보 (2026-11)')}
  ${stepc('② 시 부담','얼마가 드나',`<b>보상비</b> = 사유지 면적 × ${man(R.low)}~${man(R.high)}만원/㎡<br><b>조성비</b> = 공원 전체 면적 × ${man(R.klow)}~${man(R.khigh)}만원/㎡`,'보상비 + 조성비','청주 실제 사업 단가 · 2026 공시지가')}
  ${stepc('③ 외부 재원','시 부담을 줄일 수 있나',`${(PZ.special_min_m2/1e4).toLocaleString('ko-KR')}만㎡ 이상은 민간공원 특례(민간이 조성), 요건을 갖추면 국비 공모로 조성비 일부 지원.`,'최대 → 최소 부담','공원녹지법 제21조의2')}
  ${stepc('④ 집행 단계','언제 하나',`실효가 ${PZ.stage1_expiry_max}년 이전이거나, 공고상 1단계이거나, 외부 재원이 있으면 1단계.`,'1단계 / 2단계','청주시 공고 제2026-2004호',true)}
</div>
<div class="pz-note"><b>검증</b> — 같은 방법으로 청주 월명공원(${nf(W.area_m2)}㎡) 실제 사업비를 다시 계산했습니다. 보상비 ${f(wComp/1e8,1)}억(실제 ${f(W.compensation_krw/1e8,0)}억), 조성비 ${f(wCons/1e8,1)}억(실제 ${f(W.construction_krw/1e8,0)}억)으로 차이 1% 안입니다.</div>
${more('상세보기 — 단가 근거와 가정', dl([
  ['보상 단가',`청주 실적 ${man(R.low)}만(강내근린공원)~${man(R.high)}만원/㎡(월명공원). 사유지 공시지가가 더 높으면 공시지가 기준(토지보상법 제70조)으로 올림`],
  ['조성 단가',`청주 실적 ${man(R.klow)}만(월명공원)~${man(R.khigh)}만원/㎡(강내근린공원)`],
  ['단계 안정성','단가·국비 조건을 바꾼 여러 경우에서도 단계가 같은지 확인'],
  ['국·공유지','국유·시유지는 사들이지 않고 사용 허가로 활용 → 조성비만 듦'],
  ['한계','어린이공원152는 공원 경계를 찾지 못해 전부 사유지로 가정. 생태공원3 조성비는 비교할 실적이 없어 미산정']]))}`,`style="--tc:var(--pz-biz)"`)}
${dash('biz','색 = 국공유지 비율 · 3D 기둥 = 시 부담 · 공원을 누르면 보상비·조성비 계산과 필지').replace('class="pz-block pz-dash"','class="pz-block pz-dash" style="--tc:var(--pz-biz)"')}
${sec(4,'결과',`<div class="pz-kpis" style="--cols:4">
  ${kpi('시 부담 (전체)',`${eok(bMin)}–${eok(bMax)}`,'억 원','외부 재원 최대 활용 ~ 시가 전부 부담')}
  ${kpi('1단계',st1.length,'곳',`시 부담 최대 ${eok(st1Max)}억 원`,true)}
  ${kpi('보상비 0인 공원',allPub,'곳',`땅이 모두 국공유 — 조성비만 듦 (생태공원 제외 국공유 비율 ${pc(pubShare)})`)}
  ${kpi('민간공원 특례 가능',spec.length,'곳',spec.map(p=>p.name).join(' · ')||'—')}
</div>
<div class="pz-res"><div><p class="pz-sub">시 부담이 큰 5곳 (최대 기준)</p><div class="pz-legend"><span><i style="background:var(--pz-comp)"></i>보상비 (사유지)</span><span><i style="background:var(--pz-cons)"></i>조성비 (전체 면적)</span></div>
  ${rank(b5.map(p=>({p,v:p.maxH,segs:[[p.comp||0,'var(--pz-comp)'],[p.cons||0,'var(--pz-cons)']]})), b5[0].maxH, r=>`${eok(r.v)}억<small>${r.p.stage} · 국공유 ${pc(r.p.pub)}</small>`)}</div>
  <div class="pz-take" style="--tc:var(--pz-biz)"><div class="h">해석</div>
  <p>${n}곳 전체 시 부담은 <b>${eok(bMin)}억~${eok(bMax)}억 원</b>입니다. 이 중 <b>${st1.length}곳</b>을 1단계로 먼저 추진해야 합니다.</p>
  <ul><li>비용 차이는 대부분 사유지 보상비에서 생깁니다.</li><li>국공유지가 많은 공원은 조성비만으로 빠르게 추진할 수 있습니다.</li></ul>
  <div class="pz-chips">${st1.map(p=>`<span>${p.name}</span>`).join('')}</div></div></div>
${more('상세보기 — '+n+'곳 전체 표', `<table class="pz-t"><thead><tr><th>순위</th><th>공원</th><th>위치</th><th class="r">실효</th><th class="r">국공유</th><th class="r">보상비</th><th class="r">조성비</th><th class="r">시 부담 최대</th><th>단계</th></tr></thead><tbody>
  ${bTop.map((p,i)=>`<tr><td>${i+1}</td><td>${p.name}</td><td>${p.loc}</td><td class="r">${p.expiry}</td><td class="r">${pc(p.pub)}</td><td class="r">${p.comp==null?'—':eok(p.comp)+'억'}</td><td class="r">${p.cons==null?'미산정':eok(p.cons)+'억'}</td><td class="r">${eok(p.maxH)}억</td><td>${p.stage}</td></tr>`).join('')}</tbody></table>`)}`,`style="--tc:var(--pz-biz)"`)}
<section class="pz-block"><h3 class="pz-h3">자료 출처</h3><div class="pz-src">${(document.querySelector('#app footer')||{}).innerHTML||''}</div></section>`;

// ---------- 우선순위 흐름 (교수님 방향: 유형 → 조성형 순위 → 에너지·탄소, 사업성은 실행) ----------
const RP = p => p.R||{}, RH = p => RP(p).hot||{};
const prioOK = p => RP(p).status==='산정';
const RO = P.filter(prioOK), RB = RO.filter(p=>RP(p).kind==='조성형'), RK = RO.filter(p=>RP(p).kind==='보전형');
const sg = (v,d=2) => v==null?'—':(v>0?'+':v<0?'−':'')+Math.abs(v).toFixed(d);
// 조성형 순위 = 열 취약(주변 핫스팟 비율) 등수 + 열 노출 감소 등수 (지도 앱 RRANK와 같은 규칙)
const RR = (()=>{ const r={}, by=f=>[...RB].sort((a,b)=>f(b)-f(a));
  by(p=>RH(p).hot2_share||0).forEach((p,i)=>(r[p.id]={h:i+1}));
  by(p=>-(RP(p).exposure||0)).forEach((p,i)=>(r[p.id].e=i+1));
  [...RB].sort((a,b)=>(r[a.id].h+r[a.id].e)-(r[b.id].h+r[b.id].e)||RP(a).exposure-RP(b).exposure).forEach((p,i)=>(r[p.id].rank=i+1));
  return r; })();
const rTop = [...RB].sort((a,b)=>RR[a.id].rank-RR[b.id].rank), r5 = rTop.slice(0,5);
// 방법 강건성(OECD·JRC 2008 Step 7): 순위합 대신 정규화 가중합(가중치 0.3·0.5·0.7, 열 노출 원값/로그)으로 바꿔도 순위가 유지되나
const ROB = (()=>{ if(!RB.length) return [];
  const H=p=>RH(p).hot2_share||0, X=p=>-RP(p).exposure, LX=p=>Math.log1p(X(p));
  const mm=f=>{const v=RB.map(f), lo=Math.min(...v), hi=Math.max(...v); return p=>(f(p)-lo)/((hi-lo)||1);};
  const base=Object.fromEntries(rTop.map((p,i)=>[p.id,i])), top5=new Set(r5.map(p=>p.id)), n=RB.length;
  const out=[];
  for(const [lab,xf] of [['정규화 가중합',mm(X)],['정규화 가중합(열 노출 로그)',mm(LX)]]) for(const w of [0.3,0.5,0.7]){
    const hf=mm(H), o=[...RB].sort((a,b)=>(w*hf(b)+(1-w)*xf(b))-(w*hf(a)+(1-w)*xf(a)));
    const d2=o.reduce((s,p,i)=>s+(i-base[p.id])**2,0), rho=1-6*d2/(n*(n*n-1));
    out.push({lab:`${lab} · 열 취약 ${w}`, top:o.slice(0,5).filter(p=>top5.has(p.id)).length, rho, shift:o.reduce((s,p,i)=>s+Math.abs(i-base[p.id]),0)/n});
  }
  return out; })();
// 파레토(비지배): 두 기준 모두에서 다른 조성형보다 뒤지지 않는 공원
const PARETO = RB.filter(p=>!RB.some(q=>q!==p && (RH(q).hot2_share||0)>=(RH(p).hot2_share||0) && -RP(q).exposure>=-RP(p).exposure && ((RH(q).hot2_share||0)>(RH(p).hot2_share||0) || -RP(q).exposure>-RP(p).exposure)));
const kTop = [...RK].sort((a,b)=>RP(b).exposure-RP(a).exposure);
const RC = D.R ? D.R.coef : {build:{},keep:{in:0,bands:[[0,0]]},ef:0};
const bSum = -sum(RB,p=>RP(p).exposure), kSum = sum(RK,p=>RP(p).exposure);
const RL = (D.R&&D.R.refs&&D.R.refs.items)||{};
const cite = ks => ks.filter(k=>RL[k]).map(k=>RL[k].short).join('; ');
const refList = () => Object.keys(RL).length ? more('참고문헌', `<ol class="pz-refs">${Object.values(RL).map(x=>`<li>${x.cite}</li>`).join('')}</ol>`) : '';
const HP = (D.R&&D.R.hot&&D.R.hot.params)||{sample_buffer_m:150};
const ZN = (D.R&&D.R.zones)||[];


// 조성 전·후 지표온도 변화(전국 실측, 본 연구 분석) — params.yaml priority.evidence
function evBlock(){
  const EV = D.R && D.R.evidence; if(!EV) return '';
  const mx = Math.max(...EV.cols.flatMap(c=>c.values.map(Math.abs)));
  const bar = v => `<span style="display:inline-block;vertical-align:middle;height:8px;border-radius:2px;width:${Math.max(2,Math.abs(v)/mx*90)}px;background:${v<0?'#2b6cb0':'#c4623a'};margin-left:6px"></span>`;
  return `<div style="margin-top:18px"><p class="pz-sub" style="margin-bottom:6px">조성 전·후 여름 지표온도 변화 (전국 실측, 본 연구 분석)</p>
  <table class="pz-t"><thead><tr><th>위치</th>${EV.cols.map(c=>`<th class="r">${c.label}<br><small>${c.n}곳</small></th>`).join('')}</tr></thead><tbody>
  ${EV.zones.map((z,i)=>`<tr><td>${z}</td>${EV.cols.map(c=>`<td class="r">${sg(c.values[i])}°C${bar(c.values[i])}</td>`).join('')}</tr>`).join('')}</tbody></table>
  <p class="pz-cap" style="margin-top:6px">파랑 = 시원해짐, 주황 = 더워짐. 공원을 만들면 공원 안은 약 1°C(1ha 이상 약 1.5°C) 낮아지고, 효과는 경계 밖 100m 안에서 대부분 사라집니다. 숲이 개발되면 변화가 약 5배 큽니다.</p>
  ${more('상세보기 — 방법 · 면적별 · 계절별', `<p class="pz-cap">${EV.method}</p>
    <table class="pz-t"><thead><tr><th>새 녹지 면적</th><th class="r">사례</th><th class="r">공원 안</th><th class="r">0~100m</th></tr></thead><tbody>${EV.by_area.map(r=>`<tr><td>${r[0]}</td><td class="r">${r[1]}곳</td><td class="r">${sg(r[2])}°C</td><td class="r">${sg(r[3])}°C</td></tr>`).join('')}</tbody></table>
    <p class="pz-cap">1ha를 넘으면 공원 안 효과가 약 2배로 커지고 그 이상은 비슷합니다.</p>
    <table class="pz-t"><thead><tr><th>계절</th><th class="r">공원 안</th><th class="r">0~100m</th></tr></thead><tbody>${EV.by_season.map(r=>`<tr><td>${r[0]}</td><td class="r">${sg(r[1])}°C</td><td class="r">${sg(r[2])}°C</td></tr>`).join('')}</tbody></table>
    <p class="pz-cap">냉각 효과는 잎이 무성한 여름에만 뚜렷합니다. 그래서 냉방 전력 절감은 여름 효과만 씁니다.</p>`)}</div>`;
}
// ---------- 2. 평가 기준 (새 틀) ----------
const pFrame2 = `<div class="pz-eyebrow" style="--tc:var(--pz-ink2)">평가 기준</div>
<h2 class="pz-h2">3단계 평가 체계</h2>
<p class="pz-lead" style="margin-top:10px">공원 조성은 <b>지역 기온 저감 → 냉방 전력 감소 → 탄소 배출 감소</b>로 이어집니다. 이 효과를 극대화하기 위해 <b>열 취약성 · 거주 인구 · 에너지 저감 효과</b>를 평가 기준으로 삼습니다. 사업성은 우선순위를 바꾸는 기준이 아니라 <b>집행 시기와 재원</b>을 정하는 기준으로 활용합니다.</p>
<div class="pz-lenses pz-order">
  <button class="pz-lens" style="--tc:var(--pz-prio)" data-go="type"><span class="k">① 대상지 유형 구분</span><span class="t">현황·유형</span><span class="q">조성 대상지인가, 보전 대상지인가?</span><span class="d">공원 부지의 현재 토지피복과 식생 상태에 따라 조성형(녹지 부족)과 보전형(녹지 형성)으로 구분합니다.</span><span class="m">조성형 ${RB.length}곳 · 보전형 ${RK.length}곳</span><span class="go">자세히 →</span></button>
  <button class="pz-lens" style="--tc:var(--pz-prio)" data-go="rank"><span class="k">② 조성 우선순위</span><span class="t">조성형 우선순위</span><span class="q">어느 대상지를 우선 조성할 것인가?</span><span class="d">주변 열 취약도가 높고 냉각 효과 범위 내 거주 인구가 많아 열 노출 저감 효과가 큰 대상지를 우선합니다.</span><span class="m">핵심 지표 · 핫스팟 비율 · 열 노출 저감량(인·°C)</span><span class="go">자세히 →</span></button>
  <button class="pz-lens" style="--tc:var(--pz-prio)" data-go="carbon"><span class="k">③ 에너지·탄소 효과</span><span class="t">에너지·탄소</span><span class="q">냉방 전력과 탄소 배출을 얼마나 줄이는가?</span><span class="d">열 노출 변화를 냉방 전력(kWh)과 탄소 배출량(tCO₂)으로 환산하여 청주시 감축 목표에 대한 기여도를 산정합니다.</span><span class="m">핵심 지표 · kWh · tCO₂ (계수 확보 중)</span><span class="go">자세히 →</span></button>
</div>
<section class="pz-block"><h3 class="pz-h3">평가 순서의 근거</h3>
  <div class="pz-steps3 pz-why3">
    <div style="--tc:var(--pz-prio)"><div class="t"><span>1</span>대상지 성격에 따른 구분</div><div class="d">이미 녹지가 형성된 부지는 조성에 따른 추가 냉각 효과가 작은 반면, 개발 시 열환경이 크게 악화됩니다. 따라서 <b>조성 대상지</b>와 <b>보전 대상지</b>를 먼저 구분합니다.</div></div>
    <div style="--tc:var(--pz-prio)"><div class="t"><span>2</span>조성 대상지는 효과 순으로</div><div class="d">동일한 규모의 공원이라도 <b>열 취약도가 높고 거주 인구가 많은 지역</b>에 조성할수록 냉각 효과의 수혜 인구가 커집니다.</div></div>
    <div style="--tc:var(--pz-prio)"><div class="t"><span>3</span>탄소로 연결</div><div class="d">조성형 상위 대상지의 냉각 효과를 <b>냉방 전력과 탄소 배출 감소량</b>으로 환산해, 청주시 감축 목표에 대한 기여를 제시합니다.</div></div>
  </div>
  ${more('상세보기 — 기존 평가 틀(이용성·에너지저감·사업성)과의 관계', dl([
    ['이용성 지표','냉각 범위 내 거주 인구·아동·고령 비율로 ②에 반영'],
    ['에너지저감 1차 모델','②·③에는 청주 픽셀 계수 대신 전국 공원 조성·녹지 개발 전후 실측 계수를 적용'],
    ['사업성','표준품셈 공사비로 다시 산정한 뒤 집행 계획 단계에서 활용(이 발표판에는 아직 넣지 않음)']]))}
</section>`;

// ---------- 3. ① 현황·유형 ----------
const pType = !D.R ? '' : `${head('type','①','현황·유형','조성 대상지인가, 보전 대상지인가?')}
<section class="pz-block pz-why" style="--tc:var(--pz-prio)"><h3 class="pz-h3"><span class="n">1</span>분석 목적</h3><p>40개 대상지에는 현재 <b>시가지·나지 등 녹지가 부족</b>하여 공원 조성 시 냉각 효과가 기대되는 곳과, 이미 <b>숲·농경지 등 녹지가 형성</b>되어 추가 냉각 효과는 작으나 <b>개발 시 열환경 악화가 우려</b>되는 곳이 함께 있습니다. 두 유형은 평가 관점이 다르므로 먼저 구분합니다.</p>
  <ul><li>위성 식생지수(NDVI)</li><li>환경부 토지피복지도</li><li>전국 전후 실측 비교</li></ul></section>
${sec(2,'유형 기준',`<div class="pz-flow" style="--cols:2">
  ${stepc('조성형','조성 시 냉각 효과가 기대되는 대상지',`녹지가 부족한 시가지·나지·일부 농경지. 전국 신규 공원 72곳 조성 전후: 공원 안 ${sg(RC.build.ge1?RC.build.ge1.in:null)}°C(1ha 이상), 경계 밖 0~100m ${sg(RC.build.ge1?RC.build.ge1.bands[0][1]:null)}°C.`,'조성 시 지표온도 저감',cite(['landsat','parklist']))}
  ${stepc('보전형','개발 시 열환경 악화가 우려되는 대상지',`숲·농경지 등 녹지가 형성된 부지. 전국 도시 숲 일부 개발 561곳 전후: 개발된 자리 ${sg(RC.keep.in)}°C, 바로 옆 ${sg(RC.keep.bands[0][1])}°C — 조성 효과의 약 5배에 해당.`,'개발 시 지표온도 상승',cite(['landsat','dw']))}
</div>
${evBlock()}`)}
${dash('type','색 = 조성형(주황) · 보전형(초록) · 공원을 누르면 오른쪽에 근거')}
${sec(4,'결과',`<div class="pz-kpis" style="--cols:2">
  ${kpi('조성형',RB.length,'곳',`조성 시 열 노출 ${nf(bSum)} 인·°C 저감`,true)}
  ${kpi('보전형',RK.length,'곳',`보전 시 열 노출 ${nf(kSum)} 인·°C 증가 방지`)}
</div>
<p class="pz-cap" style="margin:8px 0 0">40곳 중 ${P.length-RO.length}곳(${P.filter(p=>!prioOK(p)).map(p=>p.name).join('·')})은 공원 경계 자료가 없거나 초대형 하천 기반시설이라 유형을 나누지 않았습니다.</p>
<div class="pz-res"><div><p class="pz-sub">보전형 — 보전 시 열 노출 증가 방지 효과가 큰 대상지</p>
  ${rank(kTop.slice(0,5).map(p=>({p,v:RP(p).exposure})), Math.max(...kTop.slice(0,5).map(p=>RP(p).exposure)), r=>`+${nf(r.v)}<small>인·°C</small>`)}</div>
  <div class="pz-take" style="--tc:var(--pz-prio)"><div class="h">해석</div>
  <p>보전형은 대부분 0.1~0.3ha 규모의 소공원으로 주변 거주 인구는 적으나, 개발 시 지표온도 변화 폭이 조성 효과보다 크게 나타납니다.</p>
  <ul><li>보전형은 순위를 매기지 않고 <b>보전 대상지</b>로 분류합니다(개발 압력 자료 확보 후 순위 산정 예정).</li><li>조성형 ${RB.length}곳의 우선순위는 다음 장에서 제시합니다.</li></ul></div></div>
${more('상세보기 — 생활권 순위(배경)', `<table class="pz-t"><thead><tr><th>생활권</th><th class="r">수요 D</th><th class="r">환경 E</th><th class="r">종합 P</th></tr></thead><tbody>${ZN.map(z=>`<tr><td>${z.zone}</td><td class="r">${z.D}</td><td class="r">${z.E??'—'}</td><td class="r">${z.P??'—'}</td></tr>`).join('')}</tbody></table><p class="pz-cap">D = 평균(공원 부족(법정 1인당 6㎡ 대비), 서비스권 밖 인구 비율) × 100 · E = 평균(NDVI 취약, 지표온도 취약) × 100 · P = 0.5D + 0.5E</p>`)}`,`style="--tc:var(--pz-prio)"`)}`;

// ---------- 4. ② 조성형 우선순위 ----------
const pRank = !D.R ? '' : `${head('rank','②','조성형 우선순위','어느 대상지를 우선 조성할 것인가?')}
<section class="pz-block pz-why" style="--tc:var(--pz-prio)"><h3 class="pz-h3"><span class="n">1</span>분석 목적</h3><p>공원 조성에 따른 냉각 효과는 <b>주변 지역의 열 취약도와 거주 인구</b>에 따라 공원마다 다르게 나타납니다. 열 취약도가 높고 거주 인구가 많은 대상지를 우선 조성할 때 동일한 예산으로 더 많은 주민이 냉각 효과를 누릴 수 있습니다.</p>
  <ul><li>열 취약성</li><li>거주 인구</li><li>에너지 저감 효과</li></ul></section>
${sec(2,'평가 구조',`<div class="pz-flow" style="--cols:3">
  ${stepc('① 열 취약도','주변 지역의 열 취약 정도',`공원 경계+${HP.sample_buffer_m}m 중 여름 열 핫스팟(시가지 안 취약도 상위 20%) 면적 비율.`,'핫스팟 비율',cite(['landsat','dw','gee']))}
  ${stepc('② 열 노출 저감량','냉각 효과의 수혜 규모',`거리별 지표온도 저감량(전국 신규 공원 72곳 조성 전후 실측) × 해당 거리 내 거주 인구. 거주 인구와 에너지 저감 효과를 함께 반영하는 지표.`,'거주 인구 × 온도 저감 (인·°C)',cite(['liu2022','li2024','sgis']))}
  ${stepc('③ 조성 우선순위','순위 산정 방법',`①과 ②의 순위를 합산하여 합이 작은 대상지를 우선합니다(순위합, Borda 규칙). 순위 기반 방법은 이상치의 영향을 받지 않아 값의 분포가 1~356으로 크게 치우친 ②에 적합합니다.`,'등수 합',cite(['oecd2008']),true)}
</div>
${more('상세보기 — 방법의 근거와 강건성', dl([
  ['순위합(Borda)',`각 기준의 순위를 더하는 합성 방법. 단순하고 이상치에 영향을 받지 않지만 값의 크기 정보는 잃습니다 (${cite(['oecd2008'])}, p.102).`],
  ['다른 연구의 방식',`열 노출·취약 인구 우선지역은 점수를 합치기보다 기준을 겹쳐 모두 높은 곳을 고르는 경우가 많고(${cite(['norton2015'])}), 미집행 공원 우선순위 연구도 기준별 순위와 그 교집합을 씀(${cite(['kang2018'])}).`],
  ['파레토(두 기준 모두 앞선 곳)',`${PARETO.map(p=>p.name).join(', ')||'없음'} — 두 기준 모두에서 다른 조성형에 뒤지지 않습니다.`],
  ['강건성 점검',`방법·가중치를 바꿔 순위가 유지되는지 확인 (${cite(['oecd2008'])}, pp.117-118). 상위 5곳 유지 ${ROB.filter(r=>r.top===5).length}/${ROB.length}개 조건, 순위상관 ${Math.min(...ROB.map(r=>r.rho)).toFixed(2)}~${Math.max(...ROB.map(r=>r.rho)).toFixed(2)}`]]))
}
${more('상세보기 — 강건성 표', `<table class="pz-t"><thead><tr><th>비교 방법</th><th class="r">상위 5곳 일치</th><th class="r">순위상관(스피어만)</th><th class="r">평균 순위 이동</th></tr></thead><tbody>${ROB.map(r=>`<tr><td>${r.lab}</td><td class="r">${r.top}/5</td><td class="r">${r.rho.toFixed(2)}</td><td class="r">${r.shift.toFixed(1)}</td></tr>`).join('')}</tbody></table><p class="pz-cap">기준 = 순위합. 정규화 가중합 = 두 기준을 0~1로 바꿔 가중 평균.</p>`)}`)}
${dash('rank',`조성형 ${RB.length}곳만 표시 · 색이 진할수록 우선 조성 · 공원을 누르면 오른쪽에 근거`)}
${sec(4,'결과',`<div class="pz-take" style="--tc:var(--pz-prio)"><div class="h">해석</div>
  <p><b>${r5[0].name}</b>은 주변 면적의 ${pc(RH(r5[0]).hot2_share)}가 열 핫스팟이며 냉각 효과 범위 내 거주 인구가 ${nf(RP(r5[0]).pop_in_range)}명으로, 두 기준 모두 1위입니다.</p>
  <ul><li>상위 5개소(${r5.map(p=>p.name).join('·')})가 조성형 전체 열 노출 저감량의 ${pc(sum(r5,p=>-RP(p).exposure)/bSum)}를 차지하며, 모두 도심 시가지에 위치합니다.</li>
  <li>외곽 소공원은 공원 서비스 공백이 크나 주변 거주 인구가 적어 하위에 위치합니다.</li>
  <li>전체 순위는 위 대시보드의 목록과 아래 표에서 확인할 수 있습니다.</li></ul></div>
${more('상세보기 — 조성형 '+RB.length+'곳 전체 표', `<table class="pz-t"><thead><tr><th>순위</th><th>공원</th><th>위치</th><th class="r">핫스팟 비율</th><th class="r">경계 밖 저감</th><th class="r">범위</th><th class="r">범위 안 주민</th><th class="r">아동·고령</th><th class="r">열 노출 감소</th></tr></thead><tbody>
  ${rTop.map(p=>{const r=RP(p);return `<tr><td>${RR[p.id].rank}</td><td>${p.name}</td><td>${p.loc}</td><td class="r">${pc(RH(p).hot2_share)}</td><td class="r">${sg(r.t_edge)}°C</td><td class="r">${r.range_m}m</td><td class="r">${nf(r.pop_in_range)}</td><td class="r">${pc(r.vulnerable)}</td><td class="r">${nf(-r.exposure)}</td></tr>`}).join('')}</tbody></table>`)}
${refList()}`,`style="--tc:var(--pz-prio)"`)}`;

// ---------- 5. ③ 에너지·탄소 (②의 상위 5곳 → 전·후 실측 계수 적용 → 지표온도 저감 → 기온 → 가정 냉방 전력 → 탄소) ----------
// 전력 환산 계수는 params.yaml priority.energy (min/base/max). 없으면 kWh·tCO₂ 칸은 '산정 예정'
const EN = (D.R && D.R.energy) || null;
function enCalc(p){   // 공원 하나: 거리 구간별 가구 × 기온 저감 × 24°C 초과일수 / 100 × CDD 100당 가구 월 전력 → kWh/여름 (최소·기준·최대)
  const r = RP(p); if(!EN) return null;
  const out = [0,1,2].map(k => r.bands.reduce((s,b)=>{
    const hh = b.pop / EN.persons_per_household;
    const dAir = Math.abs(b.dt) * EN.lst_to_air[k];                 // 기온 저감(°C)
    return s + hh * dAir * EN.hot_days[k] / 100 * EN.kwh_per_100cdd_month[k];   // 냉방도일 감소 × CDD 100당 가구 월 전력
  },0));
  return {kwh: out, t: out.map(v=>v/1000*RC.ef)};
}
const fx = (v,d=0) => v==null?'—':(+v).toLocaleString('ko-KR',{maximumFractionDigits:d,minimumFractionDigits:d});
const rng = (a,d) => a ? `${fx(a[0],d??(a[0]<10?1:0))}~${fx(a[2],d??(a[2]<10?1:0))}` : '산정 예정';
const top5 = r5, E5 = top5.map(p=>({p, e:enCalc(p)}));
const sumE = k => EN ? E5.reduce((s,x)=>s+x.e[k][1],0) : null;

// ③ 페이지: ① 지표온도 저감 계산 자세히 — 전국 실측 계수(면적 구간) → 상위 5곳에 적용
function step1Detail(){
  const B = RC.build||{}, EV = D.R.evidence||{};
  const cls = [['04_06','0.4~0.6ha'],['06_1','0.6~1ha'],['ge1','1ha 이상'],['lt04','0.4ha 미만']];
  const pick = ha => ha<0.4?'lt04':ha<0.6?'04_06':ha<1?'06_1':'ge1';
  const lab = Object.fromEntries(cls);
  const band = (c,lo) => { const b=(B[c]||{}).bands||[]; const f=b.find(x=>x[0]>lo); return f?sg(f[1])+'°C':'—'; };
  return `<div><ol class="pz-refs" style="font-size:14px">
    <li><b>전국 신규 공원 찾기</b> — 전국 공원 목록과 위성 식생지수를 맞대어, 2013~15년에 맨땅·공사지(식생지수 0.25 미만)였다가 2022~24년에 녹지(0.5 초과)가 된 신규 공원 72곳을 골랐습니다.</li>
    <li><b>조성 전·후 지표온도 비교</b> — ${EV.method||''}.</li>
    <li><b>효과 = (공원 쪽 전·후 변화) − (같은 사례 바깥 300~500m 고리의 전·후 변화)</b>. 같은 시기 주변 개발과 해마다 다른 날씨의 영향을 뺀 값입니다(이중차분).</li>
    <li><b>면적 구간별 중앙값</b>을 계수로 씁니다(아래 표 1).</li>
    <li><b>상위 5곳의 면적</b>(도시계획시설 공원 경계)으로 구간을 골라 그 계수를 적용합니다(아래 표 2).</li>
  </ol>
  <p class="pz-cap" style="margin-top:10px"><b>표 1. 공원 조성 전·후 여름 지표온도 변화 계수</b> (전국 실측 중앙값, 본 연구 분석)</p>
  <table class="pz-t"><thead><tr><th>새 녹지 면적</th><th class="r">사례</th><th class="r">공원 안</th><th class="r">경계 밖 0~100m</th><th class="r">100~200m</th></tr></thead><tbody>
  ${cls.map(([c,l])=>{const b=B[c]||{};return `<tr><td>${l}</td><td class="r">${b.n?b.n+'곳':'—'}</td><td class="r">${b.in==null?'—':sg(b.in)+'°C'}</td><td class="r">${band(c,0)}${c==='lt04'?' <small>(가정)</small>':''}</td><td class="r">${band(c,100)}</td></tr>`;}).join('')}
  </tbody></table>
  <p class="pz-cap">0.4ha 미만은 위성 열센서 해상도(약 100m)보다 작아 실측 사례가 없어, 경계 밖 −0.3°C를 상한으로 가정했습니다(근거 문헌 원문 미확인).</p>
  <p class="pz-cap" style="margin-top:10px"><b>표 2. 상위 5곳 적용</b></p>
  <table class="pz-t"><thead><tr><th>순위</th><th>공원</th><th class="r">면적</th><th>적용 구간</th><th class="r">공원 안</th>${[[0,100],[100,200]].map(([a,b])=>`<th class="r">경계 밖 ${a}~${b}m</th>`).join('')}<th class="r">효과 범위</th></tr></thead><tbody>
  ${top5.map(p=>{const r=RP(p),c=pick(r.ha||0),bd=(lo,hi)=>{const x=r.bands.find(b=>b.from<hi&&b.to>lo);return x?`${sg(x.dt)}°C<br><small>${x.from}~${x.to}m · ${nf(x.pop)}명</small>`:'—';};
    return `<tr><td>${RR[p.id].rank}</td><td>${p.name}</td><td class="r">${(r.ha||0).toFixed(2)}ha</td><td>${lab[c]}</td><td class="r">${r.t_in==null?'—':sg(r.t_in)+'°C'}</td><td class="r">${bd(0,100)}</td><td class="r">${bd(100,200)}</td><td class="r">${r.range_m}m</td></tr>`;}).join('')}
  </tbody></table>
  <p class="pz-cap">효과 범위는 면적에 따라 0.4ha 미만 50m, 1~5ha 200m로 둡니다(우리 40곳 주변 실측 프로필). 각 칸 아래 작은 글씨는 그 거리 구간과 안에 사는 주민 수(SGIS 100m 격자)입니다.</p></div>`;
}
// 근린공원8 한 곳으로 ①→④를 끝까지 계산해 보이기
function chainExample(){
  if(!EN||!top5.length) return '';
  const p = top5[0], r = RP(p), k = 1;
  const rows = r.bands.map(b=>{const hh=b.pop/EN.persons_per_household, dA=Math.abs(b.dt)*EN.lst_to_air[k], dC=dA*EN.hot_days[k], kwh=hh*dC/100*EN.kwh_per_100cdd_month[k];
    return {b,hh,dA,dC,kwh};});
  const tot = rows.reduce((s,x)=>s+x.kwh,0);
  return more(`상세보기 — ${p.name}으로 ①→④ 끝까지 계산해 보기 (기준값)`, `<table class="pz-t"><thead><tr><th>거리 구간</th><th class="r">① 지표온도</th><th class="r">주민 → 가구</th><th class="r">② 기온 (× ${EN.lst_to_air[k]})</th><th class="r">냉방도일 감소 (× ${EN.hot_days[k]}일)</th><th class="r">③ 전력 (÷100 × ${EN.kwh_per_100cdd_month[k]} kWh)</th></tr></thead><tbody>
    ${rows.map(x=>`<tr><td>${x.b.from}~${x.b.to}m</td><td class="r">${sg(x.b.dt)}°C</td><td class="r">${nf(x.b.pop)}명 → ${fx(x.hh)}가구</td><td class="r">${sg(-x.dA,3)}°C</td><td class="r">${fx(x.dC,1)}</td><td class="r">${fx(x.kwh)} kWh</td></tr>`).join('')}
    <tr><td colspan="5"><b>합계 → ④ 탄소 = ${fx(tot)} kWh ÷ 1,000 × ${RC.ef}</b></td><td class="r"><b>${fx(tot/1000*RC.ef,2)} tCO₂</b></td></tr></tbody></table>
    <p class="pz-cap">가구 = 주민 ÷ ${EN.persons_per_household}명. 냉방도일 감소 = 기온 저감 × 여름 일평균 24°C 초과일수. 전력 = 가구 × 냉방도일 감소 ÷ 100 × 냉방도일 100당 세대 월 전력.</p>`);
}
const pCarbon = !D.R ? '' : `${head('carbon','③','에너지·탄소','상위 5곳을 조성하면 냉방 전력과 탄소를 얼마나 줄이는가?')}
<section class="pz-block pz-why" style="--tc:var(--pz-prio)"><h3 class="pz-h3"><span class="n">1</span>분석 목적</h3><p>②에서 <b>열 핫스팟이면서 주민이 많은</b> 조성형 상위 5곳을 골랐습니다. 이 5곳을 공원으로 조성했을 때 <b>지표온도 → 기온 → 주민 냉방 전력 → 탄소</b>가 얼마나 줄어드는지를 계산합니다.</p>
  <ul><li>전국 조성 전·후 실측 계수</li><li>주민 냉방 전력</li><li>국가 전력 배출계수</li></ul></section>
${sec(2,'계산 과정',`<div class="pz-flow" style="--cols:4">
  ${stepc('① 지표온도 저감','조성 전·후 실측 계수 적용',`전국 신규 공원 72곳 조성 전·후 여름 지표온도 변화(①장 표)를 상위 5곳의 면적·거리 구간에 적용하고, 구간 안 주민 수로 가중(인구 가중 냉각 효과).`,'공원 안·경계 밖 °C',cite(['landsat','liu2022']))}
  ${stepc('② 기온 저감','지표온도 → 기온 환산',EN?`위성 지표온도 변화는 기온 변화보다 크게 나타나므로 ${EN.lst_to_air[0]}~${EN.lst_to_air[2]}배(기준 ${EN.lst_to_air[1]})로 환산${EN.lst_to_air_src?' — '+EN.lst_to_air_src+', 문헌 주간값 0.08과 비슷':''}.`:'환산 비율 확보 후 산정.','기온 변화 (°C)',EN?cite(['kma','du2024']):'')}
  ${stepc('③ 주민 냉방 전력','냉방도일 감소 → 가구 전력',EN?`범위 안 가구(주민 ÷ ${EN.persons_per_household}명). 기온 저감 × 여름 일평균 24°C 초과일수(${EN.hot_days[0]}~${EN.hot_days[2]}일, ${EN.hot_days_src||'가정'}) = 냉방도일 감소. 냉방도일 100당 세대 월 전력 ${EN.kwh_per_100cdd_month[0]}~${EN.kwh_per_100cdd_month[2]} kWh(기준 ${EN.kwh_per_100cdd_month[1]})${EN.kwh_src?' — '+EN.kwh_src:''}.`:'민감도 확보 후 산정.','kWh/여름',EN?cite(EN.kwh_src?['bldhub','kma','hhsize']:['moon2026','kma','hhsize']):'')}
  ${stepc('④ 탄소','전력 배출계수',`전력 절감량 × 국가 전력 배출계수 ${RC.ef} tCO₂eq/MWh.`,'tCO₂/여름',cite(['ef2023']))}
</div>
<div style="margin-top:18px">${more('상세보기 — ① 지표온도 저감 계산 과정 (계수 표 · 상위 5곳 적용)', step1Detail())}${chainExample()}</div>`)}
${dash('carbon','색이 진할수록 열 노출 변화가 큼 · 공원을 누르면 오른쪽에 근거')}
${sec(4,'상위 5곳 적용 결과',`<table class="pz-t"><thead><tr><th>순위</th><th>공원</th><th class="r">주변 핫스팟</th><th class="r">공원 안</th><th class="r">경계 밖 0~100m</th><th class="r">범위 안 주민</th><th class="r">냉방 전력 절감<br><small>kWh/여름</small></th><th class="r">탄소 저감<br><small>tCO₂/여름</small></th></tr></thead><tbody>
  ${E5.map(({p,e})=>{const r=RP(p);return `<tr><td>${RR[p.id].rank}</td><td>${p.name}</td><td class="r">${pc(RH(p).hot2_share)}</td><td class="r">${r.t_in==null?'—':sg(r.t_in)+'°C'}</td><td class="r">${sg(r.t_edge)}°C</td><td class="r">${nf(r.pop_in_range)}명</td><td class="r">${e?fx(e.kwh[1])+'<br><small>'+rng(e.kwh)+'</small>':'산정 예정'}</td><td class="r">${e?fx(e.t[1],2)+'<br><small>'+rng(e.t,2)+'</small>':'산정 예정'}</td></tr>`;}).join('')}
  </tbody></table>
  <p class="pz-cap">공원 안 '—' = 0.4ha 미만이라 위성으로 공원 안 온도를 잴 수 없음. 냉방 전력·탄소는 기준값, 아래 작은 글씨는 최소~최대.</p>
  <div class="pz-kpis" style="--cols:2;margin-top:14px">
    ${kpi('상위 5곳 냉방 전력 절감',EN?fx(sumE('kwh')):'산정 예정',EN?'kWh/여름':'',EN?`범위 ${fx(E5.reduce((s,x)=>s+x.e.kwh[0],0))}~${fx(E5.reduce((s,x)=>s+x.e.kwh[2],0))}`:'전력 환산 계수 확보 후',true)}
    ${kpi('상위 5곳 탄소 저감',EN?fx(sumE('t'),2):'산정 예정',EN?'tCO₂/여름':'',EN?`범위 ${fx(E5.reduce((s,x)=>s+x.e.t[0],0),2)}~${fx(E5.reduce((s,x)=>s+x.e.t[2],0),2)}`:`배출계수 ${RC.ef} tCO₂eq/MWh`)}
  </div>`,`style="--tc:var(--pz-prio)"`)}
${sec(5,'해석',`<div class="pz-take" style="--tc:var(--pz-prio)"><div class="h">해석</div>
  <p>상위 5곳은 모두 열 핫스팟인 도심 시가지에 있어, 조성 시 경계 밖 100m 안 주민의 여름 지표온도가 약 0.3~0.7°C 낮아집니다.</p>
  <ul><li>${EN?'냉방 전력·탄소 저감은 문헌 계수를 쓴 추정(가정)입니다. 지표온도 → 기온 환산은 청주 관측소 실측(오전 11시 기준)이라 밤 시간 냉각은 반영하지 못합니다. 가구 냉방 전력은 청주 200세대 이상 아파트의 월 전기 사용량(공용 전기 포함, 검침 시차 1개월 보정)으로 구한 값이라 단독주택이 많은 지역에서는 다를 수 있습니다.':'전력·탄소 환산 계수를 확보하면 냉방 전력과 탄소 저감량을 채웁니다.'}</li>
  <li>냉각 효과는 여름에만 뚜렷하므로 여름(6~9월) 냉방 전력만 계산합니다.</li></ul></div>`)}
${refList()}`;


// ---------- 페이지 넘기기 ----------
const PAGES = D.R ? [['intro','주제·배경',pIntro+pPark],['frame','평가 기준',pFrame2],['type','① 현황·유형',pType],['rank','② 조성형 우선순위',pRank],['carbon','③ 에너지·탄소',pCarbon]]   // 사업성·이용성·열저감 1차 페이지는 이 발표판에서 뺌(2026-11-26)
  : [['intro','주제·배경',pIntro+pPark],['frame','평가 기준',pFrame],['use','이용성',pUse],['heat','에너지저감',pHeat],['biz','사업성',pBiz]];
const TC = {use:'var(--pz-use)',heat:'var(--pz-heat)',biz:'var(--pz-biz)',type:'var(--pz-prio)',rank:'var(--pz-prio)',carbon:'var(--pz-prio)'};
// 페이지 → 지도 주제·색·높이 (우선순위 세 장은 같은 주제를 색만 바꿔 씀)
const PTOPIC = {type:['prio','kind','expo'], rank:['prio','rank','expo'], carbon:['prio','expo','expo']};
$('pzMain').innerHTML = PAGES.map(([id,,h])=>`<div class="pz-page" id="pg-${id}" style="--tc:${TC[id]||'var(--pz-ink)'}">${h}</div>`).join('');
$('pzSteps').innerHTML = PAGES.map(([id,l],i)=>`<button data-go="${id}"><i>${i+1}</i>${l}</button>`).join('');
const app = document.getElementById('app'); $('pzHome').appendChild(app);
let HAS_DECK = false; try{ HAS_DECK = typeof window.deck==='object' && !!window.deck && typeof window.deck.DeckGL==='function' && !!deckgl; }catch(e){}
let cur = 0;
function go(i, push=true){
  i = Math.max(0, Math.min(PAGES.length-1, i)); cur = i; const id = PAGES[i][0];
  document.querySelectorAll('.pz-page').forEach(el=>el.classList.toggle('on', el.id==='pg-'+id));
  document.querySelectorAll('#pzSteps button').forEach((b,j)=>{ if(j===i) b.setAttribute('aria-current','step'); else b.removeAttribute('aria-current'); });
  $('pzPrev').disabled = i===0; $('pzNext').disabled = i===PAGES.length-1;
  $('pzNext').textContent = i<PAGES.length-1 ? `다음: ${PAGES[i+1][1]} →` : '끝';
  $('pzPos').textContent = `${i+1} / ${PAGES.length}`;
  const slot = $('slot-'+id);
  if(slot){
    if(!HAS_DECK){ slot.innerHTML = '<div class="pz-offline">지도 엔진(deck.gl)을 불러오지 못했습니다. 인터넷에 연결된 상태에서 파일을 다시 열어 주세요. 설명과 결과는 그대로 볼 수 있습니다.</div>'; }
    else { slot.appendChild(app); try{ S.sel=null; const tp=PTOPIC[id]||[id]; app.classList.toggle('pz-simple', !!PTOPIC[id]);
      if(PTOPIC[id]){ if(S.d3) $('d2').click(); if(S.bg==='none') $('bg-sat').click(); } if(S.topic!==tp[0]) setTopic(tp[0]); if(tp[1]){ S.colorCity=tp[1]; S.heightCity=tp[2]; } setView('city'); if(tp[1]){ fillSelects(); list(); render(); } }catch(e){ console.error(e); } }
  }
  if(push) history.replaceState(null,'','#'+id);
  window.scrollTo({top:0,behavior:'instant'});
}
document.addEventListener('click', e=>{ const b=e.target.closest('[data-go]'); if(b) go(PAGES.findIndex(p=>p[0]===b.dataset.go)); });
$('pzPrev').onclick = ()=>go(cur-1); $('pzNext').onclick = ()=>go(cur+1);
document.addEventListener('keydown', e=>{
  if(e.target.closest('input,select,textarea,#app,canvas')) return;
  if(e.key==='ArrowRight'||e.key==='PageDown') go(cur+1); if(e.key==='ArrowLeft'||e.key==='PageUp') go(cur-1);
});
const start = PAGES.findIndex(p=>'#'+p[0]===location.hash);
go(start<0?0:start, false);
})();
