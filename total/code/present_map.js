// 발표판 지도 보정 — 지도 앱(total_template.html)은 고치지 않고, 같은 이름의 함수만 바꿔 끼운다.
//  1) 배경(항공사진·일반지도)과 3D 지형을 사각형이 아니라 청주시 경계 모양으로 잘라 보여 준다.
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
  if(S.view!=='city' || !CUT) return _terrainLayer();
  const m = demFor(), k = terK(), tex = CUT[S.bg==='base'?'base':S.bg==='sat'?'sat':'none'];
  return new deck.TerrainLayer({id:'terrain-city-cut-'+k+'-'+S.bg, elevationData:asset('dem/'+m.file), texture:tex, bounds:m.bounds,
    elevationDecoder:{rScaler:256*k,gScaler:k,bScaler:k/256,offset:(-32768-m.min)*k}, meshMaxError:4, skirtHeight:0,
    color:C['--gu'], loaders:[loaders.TerrainLoader], loadOptions:{worker:false}, operation:'terrain+draw'});
};
function cityLine(){
  return new deck.PathLayer({id:'city-line', data:city().polys.map(pg=>pg[0]), getPath:d=>d, getColor:[...C['--ink'],170], getWidth:1.6, widthUnits:'pixels', pickable:false, updateTriggers:{getColor:C['--ink']}});
}

// --- 도시 화면 레이어 ---
cityLayers = function(){
  const ps = D.parks.filter(p=>p.c);
  const up = S.d3 && S.heightCity!=='none';
  const h = p => up ? cityHeight(p)*ELEV : 0;
  const L = [bgLayer(), guLayer(), cityLine(), guLabels()];
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
prepareCut();
})();
