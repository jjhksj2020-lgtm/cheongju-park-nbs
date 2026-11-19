/* MapLibre GL JS + OpenFreeMap. Real park polygons and metrics ONLY; never simulate data. */
const metrics = [
  {id:'d_irreplaceable_pop',name:'D · 대체 불가 인구 (명)',why:'현재 조성된 공원 서비스권 밖에서 해당 후보지에 의존하는 인구',scheme:'normal',unit:'명'},
  {id:'d_unserved_share',name:'D · 서비스권 밖 비율',why:'후보지 서비스권 내 인구 중 기존 공원 공급이 닿지 않는 비율',scheme:'normal',unit:'비율'},
  {id:'d_area_gap_m2pc',name:'D · 1인당 공원 면적 부족 (㎡/인)',why:'생활권 공원 공급 부족량',scheme:'normal',unit:'㎡/인'},
  {id:'c_dpc_median',name:'C · 녹지 연결 기여도 dPC (%)',why:'시나리오 이동거리별 dPC의 중앙값이며 가정 의존성이 있습니다.',scheme:'normal',unit:'%'},
  {id:'c_axis_dist_m',name:'C · 녹지축까지 거리 (m)',why:'값이 낮을수록 녹지축에 가까움(해석에 주의)',scheme:'normal',unit:'m'},
  {id:'f_public_ratio',name:'F · 국공유지 비율',why:'공원 부지 중 국공유 필지 면적 비율',scheme:'finance',unit:'비율'},
  {id:'f_private_owners',name:'F · 사유 필지 소유자 수 상한',why:'같은 사람이 중복 집계될 수 있음',scheme:'finance',unit:'명'},
  {id:'f_margin_direct',name:'F · 직접조성 착수 여유',why:'실효 전 남은 개월 수에서 가정 리드타임·심사기간 차감',scheme:'finance',unit:'개월'},
  {id:'f_paid_area_ratio',name:'F/K4 · 기매입 면적 비율',why:'청주시 행정자료로 확인된 경우만 표시',scheme:'finance',unit:'비율'},
  {id:'f_spent_won',name:'F/K4 · 기존 투자액',why:'청주시 행정자료. 미확보 시 미산정',scheme:'finance',unit:'원'},
  {id:'k2_city_burden_won',name:'K2 · 잔여 시 재정부담',why:'추가 확보된 사업성 결과에 한해 표시. 없으면 미산정',scheme:'finance',unit:'원'},
  {id:'lst_mean_c',name:'H · 공원별 평균 LST',why:'위성영상 분석 결과가 있어야 표시. 기온이 아닌 지표면 온도',scheme:'hot',unit:'°C'},
  {id:'heat_reduction_c',name:'H · 예상 열저감',why:'복원 전후 시나리오·모형 결과가 있어야 표시. LST와 다름',scheme:'hot',unit:'°C'}
];
const metricSelect = document.querySelector('#metric');
const statusEl = document.querySelector('#status');
const legendEl = document.querySelector('#legend');
const detailEl = document.querySelector('#detail');
const metricHelp = document.querySelector('#metricHelp');
metrics.forEach(m => { const opt=document.createElement('option');opt.value=m.id;opt.textContent=m.name;metricSelect.append(opt); });
let data=null, selected=null;
const map = new maplibregl.Map({container:'map',style:'https://tiles.openfreemap.org/styles/liberty',center:[127.48,36.64],zoom:10.7,pitch:55,bearing:-13,attributionControl:true});
map.addControl(new maplibregl.NavigationControl({showCompass:true}), 'top-right');

function numeric(v) { const n=Number(v); return v===null || v===undefined || v==='' || !Number.isFinite(n) ? null:n; }
function fmt(v,unit='') {const n=numeric(v);return n===null?'미산정':n.toLocaleString('ko-KR',{maximumFractionDigits:2})+' '+unit;}
function color(v,min,max,scheme) {
  if(v===null) return '#a6b0ad';
  const t=max===min?.55:Math.min(1,Math.max(0,(v-min)/(max-min)));
  const stops=scheme==='hot'?[[251,230,173],[238,139,85],[172,41,53]]:scheme==='finance'?[[214,226,250],[85,139,201],[41,56,111]]:[[201,231,215],[70,163,122],[23,74,66]];
  const i=t<.5?0:1,u=t<.5?t*2:(t-.5)*2;
  return 'rgb('+stops[i].map((a,j)=>Math.round(a+(stops[i+1][j]-a)*u)).join(',')+')';
}
function markBad(t){statusEl.classList.add('error');statusEl.textContent=t;}
function safeText(tag,content,parent,cl){const el=document.createElement(tag);el.textContent=content; if(cl)el.className=cl;parent.append(el);return el;}
function updateDetail(feature) {
  detailEl.replaceChildren();safeText('h2', feature?.properties?.park_name || '공원 상세정보',detailEl);
  if(!feature){safeText('p','지도에서 공원을 선택하세요.',detailEl);return;}
  const p=feature.properties||{},m=metrics.find(x=>x.id===metricSelect.value),dl=document.createElement('dl');detailEl.append(dl);
  const items=[['site_id',p.site_id],['판정',p.judgment??'별도 필요성 결과와 연결'],['기존 단계',p.exec_stage??'미연결'],[m.name,fmt(p[m.id],m.unit)],['자료 상태',p[m.id+'__status']||'미산정'],['출처 키',p[m.id+'__src']||'미산정']];
  items.forEach(([k,v])=>{safeText('dt',k,dl);safeText('dd',String(v),dl);});
  safeText('p','경로별 재정부담은 필요성 등급을 변경하지 않습니다. 높이는 지도 시각화용 상대값입니다.',detailEl,'note');
}
function changeMetric(){
  if(!data)return;
  const m=metrics.find(x=>x.id===metricSelect.value);metricHelp.textContent=m.why;
  const vals=data.features.map(f=>numeric(f.properties[m.id])).filter(v=>v!==null);
  const min=vals.length?Math.min(...vals):0,max=vals.length?Math.max(...vals):0;
  for(const f of data.features){
    const v=numeric(f.properties[m.id]);
    f.properties.visual_color=color(v,min,max,m.scheme);
    // 3D thematic height, NOT physical terrain or building elevation
    f.properties.visual_height=v===null?0:(max===min?30:8+70*(v-min)/(max-min));
  }
  if(map.getSource('parks'))map.getSource('parks').setData(data);
  statusEl.classList.remove('error');
  statusEl.textContent=vals.length?`${m.name} · 값 확보 ${vals.length}/${data.features.length}개소 · 회색은 미산정`:`${m.name}: 실제 값이 없습니다. 데이터를 확보한 뒤 CSV를 연결하세요.`;
  legendEl.replaceChildren();safeText('div',`${m.name} · 상대적 높이/색상`,legendEl);
  const grad=document.createElement('div');grad.className='gradient'+(m.scheme==='hot'?' hot':m.scheme==='finance'?' finance':'');legendEl.append(grad);
  const labs=document.createElement('div');labs.className='legendLabels';legendEl.append(labs);
  safeText('span',vals.length?fmt(min,m.unit):'미산정',labs);safeText('span',vals.length?fmt(max,m.unit):'미산정',labs);
  updateDetail(selected);
}
metricSelect.addEventListener('change',changeMetric);
document.querySelector('#view').addEventListener('change',e=>map.easeTo({pitch:e.target.value==='3d'?55:0,bearing:e.target.value==='3d'?-13:0,duration:650}));
map.on('load',async()=>{
  try{
    const res=await fetch('./parks_3d.geojson',{cache:'no-store'});
    if(!res.ok)throw new Error(`GeoJSON 응답 ${res.status}`);
    data=await res.json();
    if(data.type!=='FeatureCollection' || !Array.isArray(data.features) || !data.features.length)throw new Error('유효한 공원 FeatureCollection이 없습니다.');
    if(new Set(data.features.map(f=>String(f.properties?.site_id))).size!==data.features.length)throw new Error('site_id 중복 또는 누락');
    const bad=data.features.filter(f=>!['Polygon','MultiPolygon'].includes(f.geometry?.type));
    if(bad.length)throw new Error('Polygon 경계가 아닌 공원이 있습니다.');
    data.features.forEach(f=>{f.properties.visual_color='#a6b0ad';f.properties.visual_height=0});
    map.addSource('parks',{type:'geojson',data});
    map.addLayer({id:'park-prisms',type:'fill-extrusion',source:'parks',paint:{'fill-extrusion-color':['get','visual_color'],'fill-extrusion-height':['get','visual_height'],'fill-extrusion-base':0,'fill-extrusion-opacity':.75}});
    map.addLayer({id:'park-outlines',type:'line',source:'parks',paint:{'line-width':1.8,'line-color':'#133a30'}});
    const bounds=new maplibregl.LngLatBounds();
    data.features.forEach(f=>{ const go=c=>{if(typeof c[0]==='number')bounds.extend(c);else c.forEach(go)};go(f.geometry.coordinates); });
    if(!bounds.isEmpty())map.fitBounds(bounds,{padding:65,maxZoom:12.7,duration:650});
    map.on('click','park-prisms',e=>{
      if(!e.features?.length)return;
      const sid=String(e.features[0].properties.site_id);
      selected=data.features.find(f=>String(f.properties.site_id)===sid)||e.features[0];
      updateDetail(selected);
      const popup=document.createElement('div');
      safeText('strong',selected.properties.park_name||`공원 ${sid}`,popup);
      safeText('div',`${metrics.find(x=>x.id===metricSelect.value).name}: ${fmt(selected.properties[metricSelect.value],metrics.find(x=>x.id===metricSelect.value).unit)}`,popup);
      new maplibregl.Popup().setLngLat(e.lngLat).setDOMContent(popup).addTo(map);
    });
    map.on('mouseenter','park-prisms',()=>map.getCanvas().style.cursor='pointer');
    map.on('mouseleave','park-prisms',()=>map.getCanvas().style.cursor='');
    changeMetric();
  }catch(err){markBad('실제 공원 경계 파일이 아직 없습니다: '+err.message+'\nREADME_3D.md의 export_map3d.py를 실행하세요.');metricHelp.textContent='실데이터를 업로드하기 전에는 임의 공원·평가값을 표시하지 않습니다.';}
});
