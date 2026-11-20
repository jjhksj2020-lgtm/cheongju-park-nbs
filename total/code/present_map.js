// 발표판 지도 보정 — 지도 앱(total_template.html)은 고치지 않고, 같은 이름의 함수만 바꿔 끼운다.
//  1) 배경(항공사진·일반지도)을 사각형이 아니라 청주시 경계 모양으로: 시 경계 밖을 바탕색으로 덮고 시 경계선을 그린다.
//  2) 도시 화면 3D: 원기둥 대신 공원 경계(검은 테두리) 모양 그대로 살짝 솟아오르고, 카메라가 기울며 확대된다.
//  3) 처음 화면은 청주시 경계에 꼭 맞게.
(function(){
try{ if(typeof deck!=='object' || !deck || typeof deck.DeckGL!=='function' || !deckgl) return; }catch(e){ return; }   // 지도 엔진을 못 불러왔으면 손대지 않음
const ELEV = 0.22;   // 기둥 높이(최대 6,000) → 공원 블록 높이 최대 약 1.3km. "살짝" 솟게
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
// 시 경계 밖을 덮는 마스크: 큰 사각형에 시 경계(바깥 링)를 구멍으로
function maskLayer(){
  if(S.bg==='none' || S.view!=='city') return null;
  const c = city(), b = c.bb, m = 0.6;
  const box = [[b[0]-m,b[1]-m],[b[2]+m,b[1]-m],[b[2]+m,b[3]+m],[b[0]-m,b[3]+m],[b[0]-m,b[1]-m]];
  return new deck.PolygonLayer({id:'city-mask', data:[[box, ...c.polys.map(pg=>pg[0])]], getPolygon:d=>d, filled:true, stroked:false,
    getFillColor:[...C['--map'],255], pickable:false, updateTriggers:{getFillColor:C['--map']}});
}
function cityLine(){
  return new deck.PathLayer({id:'city-line', data:city().polys.map(pg=>pg[0]), getPath:d=>d, getColor:[...C['--ink'],170], getWidth:1.6, widthUnits:'pixels', pickable:false, updateTriggers:{getColor:C['--ink']}});
}

// --- 도시 화면 레이어 ---
cityLayers = function(){
  const ps = D.parks.filter(p=>p.c);
  const up = S.d3 && S.heightCity!=='none';
  const h = p => up ? cityHeight(p)*ELEV : 0;
  const L = [bgLayer(), maskLayer(), guLayer(), cityLine(), guLabels()];
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
  fly({longitude:f.longitude, latitude:f.latitude-(S.d3?0.035:0), zoom:f.zoom+(S.d3?0.45:0), pitch:S.d3?52:0, bearing:S.d3?-14:0});
};

// 범례 아래 줄: '원 크기 = 공원 면적' 대신
const _legend = legend;
legend = function(){
  _legend();
  const el = document.getElementById('legend');
  el.innerHTML = el.innerHTML.replace(/원 크기 = 공원 면적/g, '공원 모양 = 도시계획시설 경계 · 점 = 위치(작은 공원)').replace(/기둥 높이 = /g, '공원 높이 = ');
};
})();
