// 발표판 지도 보정 — 지도 앱(total_template.html)은 고치지 않고, 같은 이름의 함수만 바꿔 끼운다.
//  1) 배경(항공사진·일반지도)과 3D 지형을 사각형이 아니라 청주시 경계 모양으로 잘라 보여 준다.
//  2) 도시 화면 3D: 원기둥 대신 공원 경계(검은 테두리) 모양 그대로 살짝 솟아오르고, 카메라가 기울며 확대된다.
//  3) 처음 화면은 청주시 경계에 꼭 맞게.
(function(){
try{ if(typeof deck!=='object' || !deck || typeof deck.DeckGL!=='function' || !deckgl) return; }catch(e){ return; }   // 지도 엔진을 못 불러왔으면 손대지 않음
const ELEV = 0.3;    // 기둥 높이(최대 6,000) → 공원 블록 높이 최대 약 1.8km
const EASE = t => 1-Math.pow(1-t,3);

// --- 청주시 경계 (4개 구 합집합) ---
let CITY = null;
function city(){
  if(CITY) return CITY;
  const polys = D.gu.flatMap(g=>g.poly);              // [폴리곤(링 배열)]
  let geom = null;
  if(typeof turf!=='undefined'){
    try{ let u = turf.polygon(polys[0]); for(let i=1;i<polys.length;i++) u = turf.union(u, turf.polygon(polys[i])) || u; geom = u.geometry; }catch(e){ geom = null; }
  }
  const outer = geom ? (geom.type==='Polygon'?[geom.coordinates]:geom.coordinates) : polys;   // 합치기 실패 시 구 경계 그대로
  const xs=[], ys=[]; outer.forEach(pg=>pg[0].forEach(([x,y])=>{xs.push(x);ys.push(y)}));
  CITY = {polys: outer, bb:[Math.min(...xs),Math.min(...ys),Math.max(...xs),Math.max(...ys)]};
  return CITY;
}
// 시 전체 배경(항공사진·일반지도)을 청주시 경계 모양으로 잘라 둔다 — 경계 밖은 투명.
// 같은 그림이 2D 바닥과 3D 지형의 겉면으로 쓰이므로, 3D에서도 지형이 청주시 모양으로 남는다.
const BM = D.basemap||{}, CB = (BM.citySat||BM.cityBase||{}).bounds;
let CUT = null;   // {sat, base, none}: 잘라 낸 그림(data URL)
function cutImage(src, fill, w, h){
  return new Promise(res=>{
    const draw = img => {
      const W = img?img.naturalWidth:w, H = img?img.naturalHeight:h;
      const cv = document.createElement('canvas'); cv.width=W; cv.height=H; const g = cv.getContext('2d');
      const ym = l => Math.log(Math.tan(Math.PI/4 + l*Math.PI/360));   // 지도 타일은 웹 메르카토르
      const X = x => (x-CB[0])/(CB[2]-CB[0])*W, Y = y => (ym(CB[3])-ym(y))/(ym(CB[3])-ym(CB[1]))*H;
      g.beginPath(); city().polys.forEach(pg=>{ const r=pg[0]; r.forEach(([x,y],i)=>i?g.lineTo(X(x),Y(y)):g.moveTo(X(x),Y(y))); g.closePath(); });
      g.clip();
      if(img) g.drawImage(img,0,0); else { g.fillStyle=fill; g.fillRect(0,0,W,H); }
      res(cv.toDataURL('image/webp',0.9));
    };
    if(!src) return draw(null);
    const img = new Image(); img.onload=()=>draw(img); img.onerror=()=>res(null); img.src=src;
  });
}
async function prepareCut(){
  if(!CB) return;
  const sat = BM.citySat, base = BM.cityBase, rgb = C['--gu'];
  const [a,b,c] = await Promise.all([sat?cutImage(asset('img/'+sat.file)):null, base?cutImage(asset('img/'+base.file)):null,
    cutImage(null, `rgb(${rgb.join(',')})`, (sat||base).w, (sat||base).h)]);
  CUT = {sat:a, base:b, none:c};
  if(S.view==='city') render();
}
// 2D 바닥 그림: 시 전체 화면이면 잘라 낸 그림
const _bgLayer = bgLayer;
bgLayer = function(){
  if(S.view==='city' && CUT && S.bg!=='none'){
    const m = S.bg==='base'?BM.cityBase:BM.citySat, img = CUT[S.bg==='base'?'base':'sat'];
    if(m && img) return new deck.BitmapLayer({id:'bg-cut-'+S.bg, image:img, bounds:m.bounds, opacity:0.95});
  }
  return _bgLayer();
};
// 3D 지형 겉면: 시 전체 화면이면 잘라 낸 그림(배경 없음일 때도 시 모양 단색) → 경계 밖 지형은 보이지 않음
const _terrainLayer = terrainLayer;
terrainLayer = function(){
  if(wide()){
    const m = demFor(), k = terK(), tex = CUT ? CUT[S.bg==='base'?'base':S.bg==='sat'?'sat':'none'] : (S.bg==='none'?null:asset('img/'+((S.bg==='base'?BM.cityBase:BM.citySat)||{}).file));
    return new deck.TerrainLayer({id:'terrain-wide-'+k+'-'+S.bg, elevationData:asset('dem/'+m.file), texture:tex, bounds:m.bounds,
      elevationDecoder:{rScaler:256*k,gScaler:k,bScaler:k/256,offset:(-32768-m.min)*k}, meshMaxError:2, skirtHeight:0,
      color:C['--gu'], loaders:[loaders.TerrainLoader], loadOptions:{worker:false}, operation:'terrain+draw'});
  }
  if(S.view!=='city' || !CUT) return _terrainLayer();
  const m = demFor(), k = terK(), tex = CUT[S.bg==='base'?'base':S.bg==='sat'?'sat':'none'];
  return new deck.TerrainLayer({id:'terrain-city-cut-'+k+'-'+S.bg, elevationData:asset('dem/'+m.file), texture:tex, bounds:m.bounds,
    elevationDecoder:{rScaler:256*k,gScaler:k,bScaler:k/256,offset:(-32768-m.min)*k}, meshMaxError:4, skirtHeight:0,
    color:C['--gu'], loaders:[loaders.TerrainLoader], loadOptions:{worker:false}, operation:'terrain+draw'});
};
// 항공사진 범위 밖으로 조금 나간 시 경계(동쪽 끝 등)도 비지 않게, 시 전체를 옅은 색으로 먼저 깐다
function cityFill(){
  if(S.bg==='none' || terrainOn()) return null;   // 3D 지형은 잘라 낸 그림이 겉면이라 깔지 않음
  return new deck.PolygonLayer({id:'city-fill', data:city().polys, getPolygon:d=>d, filled:true, stroked:false, getFillColor:[...C['--gu'],255], pickable:false, updateTriggers:{getFillColor:C['--gu']}});
}
function cityLine(){
  return new deck.PathLayer({id:'city-line', data:city().polys.map(pg=>pg[0]), getPath:d=>d, getColor:[...C['--ink'],170], getWidth:1.6, widthUnits:'pixels', pickable:false, updateTriggers:{getColor:C['--ink']}});
}

// --- 도시 화면 레이어 ---
cityLayers = function(){
  const ps = D.parks.filter(p=>p.c);
  const up = S.d3 && S.heightCity!=='none';
  const h = p => up ? cityHeight(p)*ELEV : 0;
  const L = [cityFill(), bgLayer(), guLayer(), cityLine(), guLabels()];
  // 공원 경계 모양 그대로: 2D는 납작한 면 + 검은 테두리, 3D는 같은 모양이 값만큼 솟음
  L.push(new deck.PolygonLayer({id:'park-poly', data:ps.filter(p=>p.poly).flatMap(p=>p.poly.map(poly=>({p,poly}))), getPolygon:d=>d.poly,
    extruded:true, wireframe:true, getElevation:d=>h(d.p), getFillColor:d=>[...cityColor(d.p), up?245:225], getLineColor:[...C['--ink'],235],
    material: up?{ambient:.55,diffuse:.55,shininess:28,specularColor:[255,255,255]}:false, pickable:true, autoHighlight:true, highlightColor:[255,255,255,70],
    onClick:i=>select(i.object.p.id,false),
    updateTriggers:{getElevation:[S.d3,S.topic,S.heightCity], getFillColor:[S.topic,S.colorCity,S.d3,C['--own-nat']], getLineColor:C['--ink']},
    transitions:{getElevation:{duration:1100, easing:EASE}}}));
  // 작은 공원(수백 ㎡)은 시 전체 화면에서 면이 안 보이므로 위치 점을 같이 — 3D에서는 블록 꼭대기에 얹힌다
  L.push(new deck.ScatterplotLayer({id:'park-dot', data:ps, getPosition:p=>[p.c[0],p.c[1],h(p)+2], radiusUnits:'pixels', getRadius:p=>S.sel===p.id?7:4.5,
    getFillColor:p=>[...cityColor(p),255], stroked:true, getLineColor:p=>S.sel===p.id?[...C['--ink'],255]:[255,255,255,235], getLineWidth:p=>S.sel===p.id?2.5:1.3, lineWidthUnits:'pixels',
    pickable:true, onClick:i=>select(i.object.id,false),
    updateTriggers:{getPosition:[S.d3,S.topic,S.heightCity], getFillColor:[S.topic,S.colorCity,C['--own-nat']], getRadius:S.sel, getLineColor:[S.sel,C['--ink']], getLineWidth:S.sel},
    transitions:{getPosition:{duration:1100, easing:EASE}}}));
  return L;
};

// --- 처음 화면: 청주시 경계에 맞춤. 3D는 기울이며 살짝 확대 ---
viewCity = function(){
  const b = city().bb, el = document.getElementById('deck');
  const w = el.clientWidth||900, hh = el.clientHeight||560;
  const vp = new deck.WebMercatorViewport({width:w, height:hh});
  const f = vp.fitBounds([[b[0],b[1]],[b[2],b[3]]], {padding:Math.round(Math.min(w,hh)*0.05)});
  if(!S.d3) return fly({longitude:f.longitude, latitude:f.latitude, zoom:f.zoom, pitch:0, bearing:0});
  // 3D: 공원이 모인 도심 쪽으로 기울이며 확대 (공원 위치의 중앙값)
  const ps = D.parks.filter(p=>p.c&&p.area<1e6), med = a => { a=[...a].sort((x,y)=>x-y); return a[Math.floor(a.length/2)]; };
  fly({longitude:med(ps.map(p=>p.c[0])), latitude:med(ps.map(p=>p.c[1]))-0.045, zoom:f.zoom+1.1, pitch:55, bearing:-14});
};

// 범례 아래 줄: '원 크기 = 공원 면적' 대신
const _legend = legend;
legend = function(){
  _legend();
  const el = document.getElementById('legend');
  el.innerHTML = el.innerHTML.replace(/원 크기 = 공원 면적/g, '공원 모양 = 도시계획시설 경계 · 점 = 위치(작은 공원)').replace(/기둥 높이 = /g, '공원 높이 = ');
};
// =================== 공원 상세: 주제마다 다른 그림 ===================
//  사업성  → 원래대로 필지(소유·이용상황)
//  이용성  → 걸어서 오는 거리(버퍼) 안 100m 인구 격자. 기존 공원 이용권 안은 회색, 밖(=새로 혜택)은 초록. 3D는 인구만큼 솟음
//  에너지저감 → 공원 일대(진한 파랑)와 주변 300m(옅은 파랑)를 저감 온도만큼 칠함
const ring300 = {};    // 공원별 주변 300m 고리(turf)
function parkFeature(p){ return turf.multiPolygon(p.poly); }
function heatRing(p){
  if(ring300[p.id]!==undefined) return ring300[p.id];
  let r = null;
  try{ const f = parkFeature(p), b = turf.buffer(f, (D.E.ring_m||300)/1000, {units:'kilometers', steps:16}); r = turf.difference(b, f); }catch(e){ r = null; }
  return ring300[p.id] = r ? (r.geometry.type==='Polygon'?[r.geometry.coordinates]:r.geometry.coordinates) : null;
}
const inside = (pt, mp) => { try{ return turf.booleanPointInPolygon(pt, turf.multiPolygon(mp)); }catch(e){ return false; } };
const cellCache = {};
function useCells(p){
  if(cellCache[p.id]) return cellCache[p.id];
  const buf = PZU && PZU.buffer[String(p.id)]; if(!buf) return cellCache[p.id] = [];
  const bbx = bb(buf), h = 0.00045, w = 0.00056;     // 100m 격자 반 칸(위도·경도)
  const out = [];
  for(const [x,y,pop,vul] of PZU.cells){
    if(x<bbx[0]-w||x>bbx[2]+w||y<bbx[1]-h||y>bbx[3]+h) continue;
    if(!inside([x,y], buf)) continue;
    out.push({x,y,pop,vul, served: inside([x,y], PZU.served), sq:[[x-w,y-h],[x+w,y-h],[x+w,y+h],[x-w,y+h],[x-w,y-h]]});
  }
  return cellCache[p.id] = out;
}
const G0=[190,222,203], G1=[34,112,78], GR=[205,207,203];
function useParkLayers(p){
  const cs = useCells(p), mx = Math.max(1,...cs.map(c=>c.pop)), up = S.d3, buf = PZU.buffer[String(p.id)];
  const L = [cityBgUnder(), parkImg(),
    new deck.PolygonLayer({id:'u-served', data:PZU.served, getPolygon:d=>d, filled:true, stroked:false, getFillColor:[...GR,60], pickable:false}),
    new deck.PolygonLayer({id:'u-exist', data:PZU.existing, getPolygon:d=>d, filled:true, stroked:true, getFillColor:[120,140,125,90], getLineColor:[90,105,95,200], lineWidthMinPixels:1, pickable:false}),
    new deck.PolygonLayer({id:'u-cells', data:cs, getPolygon:d=>d.sq, extruded:up, wireframe:false, getElevation:d=>up?Math.sqrt(d.pop/mx)*260:0,
      getFillColor:d=>d.served?[...GR,up?200:130]:[...lerp(G0,G1,Math.sqrt(d.pop/mx)),235], stroked:!up, getLineColor:[255,255,255,200], lineWidthMinPixels:1,
      material:{ambient:.55,diffuse:.55}, pickable:true, updateTriggers:{getElevation:S.d3}, transitions:{getElevation:{duration:900,easing:EASE}}}),
    new deck.PathLayer({id:'u-buffer', data:buf.map(pg=>pg[0]), getPath:d=>d, getColor:[...C['--ink'],200], getWidth:2, widthUnits:'pixels', getDashArray:[6,4], dashJustified:true,
      extensions:deck.PathStyleExtension?[new deck.PathStyleExtension({dash:true})]:[], pickable:false}),
    bldLayer(p),
    new deck.PolygonLayer({id:'park-outline', data:p.poly, getPolygon:d=>d, filled:true, stroked:true, getFillColor:[255,255,255,40], getLineColor:[...C['--ink'],255], lineWidthMinPixels:2.4, pickable:false})];
  return L;
}
const B0=[214,231,245], B1=[33,102,172];
function heatParkLayers(p){
  const e = E(p), ok = e.status==='산정', ring = ok && e.ring_applied==='적용' ? heatRing(p) : null;
  const mx = Math.max(...D.parks.filter(q=>E(q).status==='산정').map(q=>E(q).dlst_cell_base||0), 0.01);
  const col = v => lerp(B0,B1,Math.min(1,Math.sqrt((v||0)/mx)));
  const lab = [];
  if(ok){ lab.push({c:p.c, t:`공원 일대 −${f2(e.dlst_cell_base)}°C`}); }
  if(ring){ const r0=ring[0][0]; let top=r0[0]; r0.forEach(q=>{ if(q[1]>top[1]) top=q; }); lab.push({c:[p.c[0], top[1]-0.0006], t:`주변 300m −${f2(e.dlst_ring_base)}°C`}); }
  return [cityBgUnder(), parkImg(),
    ring ? new deck.PolygonLayer({id:'h-ring', data:ring, getPolygon:d=>d, filled:true, stroked:true, getFillColor:[...col(e.dlst_ring_base),150], getLineColor:[...B1,160], lineWidthMinPixels:1, pickable:true}) : null,
    new deck.PolygonLayer({id:'h-park', data:p.poly, getPolygon:d=>d, filled:true, stroked:true, getFillColor:ok?[...col(e.dlst_cell_base),200]:[...C['--own-unk'],120], getLineColor:[...C['--ink'],255], lineWidthMinPixels:2.4, pickable:true}),
    bldLayer(p),
    new deck.TextLayer({id:'h-label', data:lab, getPosition:d=>d.c, getText:d=>d.t, getSize:14, getColor:[...C['--ink'],255], background:true, getBackgroundColor:[255,255,255,230], backgroundPadding:[6,3],
      characterSet:'auto', fontFamily:'Pretendard Variable, IBM Plex Sans KR, sans-serif', fontWeight:700, pickable:false})];
}
// 공원 사진 범위가 좁아서, 버퍼·고리까지 보이도록 시 전체 항공사진을 밑에 깐다
// 공원 고해상도 사진: id가 bg-로 시작하지 않아야 3D 지형 위에 덧입혀진다
function parkImg(){
  if(S.bg==='none') return null; const m = (D.basemap||{})['s'+S.sel]; if(!m) return null;
  return new deck.BitmapLayer({id:'pimg-'+m.file, image:asset('img/'+m.file), bounds:m.bounds, opacity:0.95});
}
function bldLayer(p){
  if(!(D.bld&&D.bld[p.id]&&S.showBld)) return null;
  return new deck.PolygonLayer({id:'bld', data:D.bld[p.id], getPolygon:d=>d.poly, extruded:S.d3, getElevation:d=>d.h, wireframe:false,
    getFillColor:d=>d.in?[...C['--own-org'],S.d3?245:220]:[...C['--muted'],S.d3?200:120], getLineColor:[...C['--panel'],255], lineWidthMinPixels:0.5, stroked:!S.d3, pickable:true,
    material:{ambient:.55,diffuse:.6}, updateTriggers:{getFillColor:[S.d3,C['--own-org']]}});
}
function cityBgUnder(){
  if(S.bg==='none') return null; const m = S.bg==='base'?BM.cityBase:BM.citySat; if(!m) return null;
  return new deck.BitmapLayer({id:'bg-under-'+S.bg, image:asset('img/'+m.file), bounds:m.bounds, opacity:0.95});
}
const _parkLayers = parkLayers;
parkLayers = function(){
  const p = byId[S.sel]; if(!p||!p.poly) return _parkLayers();
  if(S.topic==='use' && PZU && PZU.buffer[String(p.id)]) return useParkLayers(p);
  if(S.topic==='heat') return heatParkLayers(p);
  return _parkLayers();
};
// 이용성·에너지저감 공원 화면은 범위(이용 거리 500m·주변 300m)가 공원 둘레 지형 자료보다 넓다
// → 3D 지형은 시 전체 지형을 쓰고(겉면 = 청주시 항공사진), 공원 고해상도 사진은 그 위에 덧입힌다. 건물·지형 배율 등 기존 3D는 그대로.
const wide = () => S.view==='park' && (S.topic==='use'||S.topic==='heat');
const _demFor = demFor;
demFor = function(){ return wide() ? (D.dem||{}).city : _demFor(); };
// 지형 배율: 원래 공원 화면처럼 '높이차 × 배율 ≤ 화면 폭의 1/4' (높이차는 그 공원 둘레 지형 자료로)
const _terK = terK;
terK = function(){
  if(!wide()) return _terK();
  const p = byId[S.sel], loc = (D.dem||{})['s'+S.sel];
  const poly = S.topic==='use' && PZU && PZU.buffer[String(S.sel)] ? PZU.buffer[String(S.sel)] : p.poly, b = bb(poly);
  const ext = Math.max((b[2]-b[0])*89000,(b[3]-b[1])*111320), rel = loc ? Math.max(20, loc.max-loc.min) : 60;
  return Math.round(Math.min(S.ter, 0.25*ext/rel)*10)/10;
};
const _viewPark = viewPark;
viewPark = function(){
  const p = byId[S.sel]; if(!p||!p.poly) return;
  let poly = null;
  if(S.topic==='use' && PZU && PZU.buffer[String(p.id)]) poly = PZU.buffer[String(p.id)];
  if(S.topic==='heat') poly = heatRing(p) ? [...p.poly, ...heatRing(p)] : p.poly;
  if(!poly) return _viewPark();
  const b = bb(poly), el = document.getElementById('deck');
  const vp = new deck.WebMercatorViewport({width:el.clientWidth||800,height:el.clientHeight||500});
  const f = vp.fitBounds([[b[0],b[1]],[b[2],b[3]]],{padding:Math.round(Math.min(el.clientWidth||800, el.clientHeight||500)*0.08)});
  fly({longitude:f.longitude, latitude:f.latitude-(S.d3?0.0012:0), zoom:Math.min(f.zoom,18), pitch:S.d3?50:0, bearing:S.d3?-18:0});
};
const _tip = tip;
tip = function(info){
  const o = info.object, l = info.layer; if(!o||!l) return _tip(info);
  if(l.id==='u-cells') return {html:`<div class="tt"><b>100m 격자 인구 ${Math.round(o.pop).toLocaleString('ko-KR')}명</b><br>${o.served?'기존 공원 이용권 안':'기존 공원 이용권 밖 → 이 공원으로 새로 혜택'}${o.vul!=null?`<br>아동·고령 ${Math.round(o.vul*100)}%`:''}</div>`, style:ttStyle()};
  if(l.id==='h-ring'){ const e=E(byId[S.sel]); return {html:`<div class="tt"><b>주변 ${D.E.ring_m||300}m</b> · −${f2(e.dlst_ring_base)}°C (범위 ${f2(e.dlst_ring_low)}~${f2(e.dlst_ring_high)})<br>특례사업지 실측 퍼짐 비율 적용</div>`, style:ttStyle()}; }
  if(l.id==='h-park'){ const e=E(byId[S.sel]); return {html:`<div class="tt"><b>공원 일대</b> · −${f2(e.dlst_cell_base)}°C (범위 ${f2(e.dlst_cell_low)}~${f2(e.dlst_cell_high)})<br>지금 녹지 ${f2(e.ndvi_now)} → 조성 후 목표</div>`, style:ttStyle()}; }
  return _tip(info);
};
deckgl.setProps({getTooltip: tip});
// 공원 화면 범례(이용성·에너지저감)
const _legend2 = legend;
legend = function(){
  _legend2();
  // 이용성·에너지저감 공원 화면에서는 필지용 색·높이 선택만 숨긴다(지형·건물·3D는 그대로)
  const own = S.view==='park' && (S.topic==='use'||S.topic==='heat');
  ['colorBy','heightBy'].forEach(id=>{ const n=document.getElementById(id); const w=n&&(n.closest('label')||n.closest('.seg')); if(w) w.style.display = own?'none':''; });
  if(S.view!=='park') return;
  const el = document.getElementById('legend'), p = byId[S.sel]; if(!p) return;
  if(S.topic==='use' && PZU && PZU.buffer[String(p.id)]){
    const u = U(p);
    el.innerHTML = `<div class="t">걸어서 오는 거리 ${u.buffer_m||''}m 안 인구 (100m 격자)</div>
      <div class="ramp" style="background:linear-gradient(90deg,rgb(${G0}),rgb(${G1}))"></div><div class="ramp-l"><span>적음</span><span>많음</span></div>
      <div class="row" style="margin-top:6px"><span class="k"><i class="sw" style="background:rgb(${G1})"></i>기존 공원 이용권 밖 = 새로 혜택</span><span class="k"><i class="sw" style="background:rgb(${GR})"></i>이미 공원 이용권 안</span><span class="k"><i class="sw" style="background:rgb(120,140,125)"></i>기존 공원</span></div>
      <div class="meta" style="margin-top:5px">점선 = 이용 거리 · 검은 선 = 공원 경계${S.d3?' · 높이 = 격자 인구(제곱근)':''}<br>${PZU.pop_source} 100m 격자 · 기존 공원 청주시 도시공원정보</div>`;
  } else if(S.topic==='heat'){
    const e = E(p);
    el.innerHTML = e.status!=='산정' ? `<div class="t">에너지저감 미산정</div><div class="meta">${p.name}: 경계 없음 또는 하천 위주</div>` :
      `<div class="t">조성 후 여름 지표온도 저감 (기준 시나리오)</div>
      <div class="ramp" style="background:linear-gradient(90deg,rgb(${B0}),rgb(${B1}))"></div><div class="ramp-l"><span>0°C</span><span>더 시원해짐</span></div>
      <div class="row" style="margin-top:6px"><span class="k"><i class="sw" style="background:rgb(${B1})"></i>공원 일대 −${f2(e.dlst_cell_base)}°C</span>${e.ring_applied==='적용'?`<span class="k"><i class="sw" style="background:rgba(${B1},.45)"></i>주변 ${D.E.ring_m||300}m −${f2(e.dlst_ring_base)}°C</span>`:''}</div>
      <div class="meta" style="margin-top:5px">${e.ring_applied==='적용'?'주변 300m 효과: 특례사업지 실측 퍼짐 비율':'1ha 미만이라 주변 300m 효과는 넣지 않음'} · 녹지 ${f2(e.ndvi_now)} → 목표</div>`;
  }
};

prepareCut();
})();
