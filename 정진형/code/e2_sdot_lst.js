// e2_sdot_lst.js — ② 지표온도→기온 환산 (재현용)
// [A] 브라우저(datafile.seoul.go.kr 출처 탭)에서 S-DoT 주간 CSV 집계
//   fetch('/bigfile/iot/inf/nio_download.do?&useCache=false',{method:'POST',
//     headers:{'Content-Type':'application/x-www-form-urlencoded'},
//     body:'infId=OA-15969&seqNo=&seq=<seq>&infSeq=3'})   // seq: 20260629, 20260817, 20260914, 20260928
//   위치정보 xlsx seq=100000001 → 시리얼별 위도·경도 (변경 전 시리얼 열 포함 매칭)
//   센서·날짜별: T11=11시 기록 평균, Tday=시간평균들의 평균(≥20시간), T18=18시, Tn=21~23시 ('온도 평균(℃)' 열)
function agg(L,date){const S={};for(const l of L){if(!l.includes(date))continue;const p=l.split(',').map(x=>x.replace(/"/g,''));
 if(p[2].slice(0,10)!=date)continue;const t=+p[7];if(p[7]===''||isNaN(t))continue;const h=+p[2].slice(11,13);const s=p[1];
 S[s]=S[s]||{type:p[3],h:{}};(S[s].h[h]=S[s].h[h]||[]).push(t);}
 const out={};for(const s in S){const H=S[s].h;const hm=k=>H[k]?H[k].reduce((a,b)=>a+b)/H[k].length:null;const hs=Object.keys(H);if(hs.length<20)continue;
 out[s]={type:S[s].type,T11:hm(11),Tday:hs.map(k=>hm(k)).reduce((a,b)=>a+b)/hs.length,T18:hm(18),
  Tn:[21,22,23].map(hm).filter(x=>x!=null).reduce((a,b,i,arr)=>a+b/arr.length,0)}}return out;}
// [B] GEE: 센서 좌표(e2_sdot_coords_b36.txt) → Landsat LST 반경 45m 평균 → e2_sdot_lst_b36.txt
/*
var feats=[];for(var i=0;i*6<C.length;i++){var la=37.4+parseInt(C.substr(i*6,3),36)/1e5,lo=126.75+parseInt(C.substr(i*6+3,3),36)/1e5;
 feats.push(ee.Feature(ee.Geometry.Point([lo,la]).buffer(45),{i:i}));}
var fc=ee.FeatureCollection(feats);
var L=ee.ImageCollection('LANDSAT/LC09/C02/T1_L2').merge(ee.ImageCollection('LANDSAT/LC08/C02/T1_L2'));
function lst(img){var qa=img.select('QA_PIXEL');var m=qa.bitwiseAnd(1<<1).eq(0).and(qa.bitwiseAnd(1<<3).eq(0)).and(qa.bitwiseAnd(1<<4).eq(0)).and(qa.bitwiseAnd(1<<5).eq(0));
 return img.select('ST_B10').multiply(0.00341802).add(149).subtract(273.15).updateMask(m).rename('lst');}
['2026-06-16','2026-08-03','2026-09-04','2026-09-20'].forEach(function(d){
 var im=lst(L.filterDate(d,ee.Date(d).advance(1,'day')).filterBounds(fc.geometry()).first());
 im.reduceRegions(fc,ee.Reducer.mean(),30).map(function(f){return f.set('m',ee.Algorithms.If(f.propertyNames().contains('mean'),f.get('mean'),-999))})
   .sort('i').aggregate_array('m').evaluate(function(a){ ... base36 2자 인코딩 ... });});
*/
// [C] 날짜별 (기온−중앙값) ~ (LST−중앙값) OLS, |ΔLST|≤10, |ΔT|≤6, 4일 pooled → e2_lst_to_air.json
