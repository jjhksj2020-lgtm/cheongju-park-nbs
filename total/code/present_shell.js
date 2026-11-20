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
const pIntro = `<div class="pz-cover">
  <div class="pz-eyebrow" style="--tc:var(--pz-ink)">청주시 공고 제2026-2004호 · 장기미집행 도시공원 ${n}개소</div>
  <h1 class="pz-h1">어떤 공원부터 먼저 만들어야 하는가</h1>
  <p class="pz-lead">청주시에는 공원으로 지정만 되고 아직 만들지 못한 땅이 <b>${n}곳</b> 있습니다. 이 땅들은 ${y0}년부터 ${y1}년 사이에 차례로 <b>공원 지정이 풀립니다(실효)</b>. 시의 재원으로 한꺼번에 조성하기는 어렵기 때문에, <b>무엇을 기준으로 순서를 정할지</b>를 데이터로 제시하는 것이 이 작업의 목적입니다.</p>
</div>
<div class="pz-kpis" style="--cols:4;margin-top:26px">
  ${kpi('대상 공원',n,'곳',`소공원·어린이공원 ${small}곳, 근린·주제공원 ${n-small}곳`)}
  ${kpi('실효 시점',`${y0}–${y1}`,'',`${PZ.stage1_expiry_max}년까지 ${early}곳이 먼저 풀림`)}
  ${kpi('평가 기준','3','가지','이용성 · 에너지저감 · 사업성')}
  ${kpi('분석한 필지',nf(D.parcels.length),'필지','공원 경계 안 땅을 한 필지씩 소유·땅값 확인')}
</div>
<h3 class="pz-h3" style="margin-top:40px">세 가지 눈으로 봅니다</h3>
<div class="pz-lenses">
  <button class="pz-lens" style="--tc:var(--pz-use)" data-go="use"><span class="k">기준 1</span><span class="t">이용성</span><span class="q">누가 이 공원을 쓰게 되나?</span><span class="d">주변에 사는 사람 중 지금 가까운 공원이 없는 사람이 얼마나 되는지 봅니다.</span><span class="go">자세히 →</span></button>
  <button class="pz-lens" style="--tc:var(--pz-heat)" data-go="heat"><span class="k">기준 2</span><span class="t">에너지저감</span><span class="q">만들면 여름이 얼마나 시원해지나?</span><span class="d">녹지가 늘어 여름철 땅 온도가 얼마나 내려가는지 위성 실측으로 봅니다.</span><span class="go">자세히 →</span></button>
  <button class="pz-lens" style="--tc:var(--pz-biz)" data-go="biz"><span class="k">기준 3</span><span class="t">사업성</span><span class="q">시가 얼마를 내고, 언제 할 수 있나?</span><span class="d">땅 주인과 땅값으로 시 부담을 계산하고, 실효 시기와 재원으로 단계를 나눕니다.</span><span class="go">자세히 →</span></button>
</div>
<section class="pz-block" style="margin-top:22px">
  <h3 class="pz-h3">발표 순서</h3>
  <div class="pz-steps3">
    <div><div class="t">① 공원이란</div><div class="d">도시공원의 종류와 장기미집행·실효가 무엇인지, 왜 순서가 필요한지</div></div>
    <div><div class="t">② 세 가지 기준</div><div class="d">기준마다 <b>왜 보는지 → 어떻게 평가하는지 → 대시보드 → 결과</b> 순서로 설명</div></div>
    <div><div class="t">③ 활용</div><div class="d">대시보드에서 공원을 눌러 필지·근거까지 바로 확인</div></div>
  </div>
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
const pPark = `<div class="pz-eyebrow" style="--tc:var(--pz-ink)">배경</div>
<h2 class="pz-h2">공원이란, 그리고 장기미집행 공원이란</h2>
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
    <div><div class="t">그래서 근거 있는 순서가 필요하다</div><div class="d">시민에게 쓰임이 크고, 환경 효과가 있고, 재정적으로 가능한 곳부터 — 세 기준으로 나눠 봅니다.</div></div>
  </div>
</section>`;

// ---------- 3. 이용성 ----------
const UO = P.filter(useOK), uNew = sum(UO,p=>U(p).new_served_pop), uPop = sum(UO,p=>U(p).E1_pop);
const uTop = [...UO].sort((a,b)=>U(b).new_served_pop-U(a).new_served_pop);
const u5 = uTop.slice(0,5), u5s = sum(u5,p=>U(p).new_served_pop);
const uMiss = P.filter(p=>!useOK(p)).map(p=>p.name).join('·');
const B = UM.buffer_m;
const pUse = `${head('use','기준 1','이용성','누가 이 공원을 쓰게 되나?')}
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
  ${rank(u5.map(p=>({p,v:U(p).new_served_pop,segs:[[U(p).new_served_pop,'var(--pz-use)'],[U(p).E1_pop-U(p).new_served_pop,'#cfe3d8']]})), Math.max(...u5.map(p=>U(p).E1_pop)), r=>`${nf(r.v)}명<small>공백 ${pc(U(r.p).D1_unserved)}</small>`)}</div>
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
const pHeat = `${head('heat','기준 2','에너지저감','공원을 만들면 여름이 얼마나 시원해지나?')}
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
const pBiz = `${head('biz','기준 3','사업성','시가 얼마를 내야 하고, 언제 할 수 있나?')}
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

// ---------- 페이지 넘기기 ----------
const PAGES = [['intro','주제·목적',pIntro],['park','공원이란',pPark],['use','이용성',pUse],['heat','에너지저감',pHeat],['biz','사업성',pBiz]];
const TC = {use:'var(--pz-use)',heat:'var(--pz-heat)',biz:'var(--pz-biz)'};
$('pzMain').innerHTML = PAGES.map(([id,,h])=>`<div class="pz-page" id="pg-${id}" style="--tc:${TC[id]||'var(--pz-ink)'}">${h}</div>`).join('');
$('pzSteps').innerHTML = PAGES.map(([id,l],i)=>`<button data-go="${id}"><i>${i+1}</i>${l}</button>`).join('');
const app = document.getElementById('app'); $('pzHome').appendChild(app);
const HAS_DECK = typeof window.deck==='object' && window.deck && typeof window.deck.DeckGL==='function' && typeof deckgl!=='undefined';
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
    else { slot.appendChild(app); try{ S.sel=null; if(S.topic!==id) setTopic(id); setView('city'); }catch(e){ console.error(e); } }
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
