// 청주 — 녹지가 실제로 변한 곳에서 지표온도가 얼마나 변했나 (시간 변화 계수) + 공원 주변 고리 면적
// 틀 파일. make_gee_script.py 가 CFG(params.yaml의 gee·change)와 PARKS(공원 경계)를 채워 gee_change.js 를 만든다.
// 출력: CHANGE| 한 줄, RING| 공원 수만큼, DONE|. energy/data/gee/gee_change_output.txt 에 붙인다.
var CFG = __CFG__;
var CH = __CHANGE__;
var PARKS = __PARKS__;

var aoi = ee.Geometry.Rectangle(CFG.aoi);
var M = CFG.months, LS = CFG.landsat_scale, SC = CFG.scale_m;
var notWater = ee.ImageCollection('ESA/WorldCover/v200').first().neq(CFG.worldcover.water);

function lsPrep(img) {
  var qa = img.select('QA_PIXEL');
  var clear = ee.Image(1);
  CFG.landsat_qa_bits.forEach(function (b) { clear = clear.and(qa.bitwiseAnd(1 << b).eq(0)); });
  var sr = img.select(['SR_B4', 'SR_B5']).multiply(LS.sr_mult).add(LS.sr_add);
  var ndvi = sr.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI');
  var st = img.select('ST_B10');
  var lst = st.multiply(LS.st_mult).add(LS.st_add).subtract(LS.kelvin).rename('LST');
  return ndvi.addBands(lst).toFloat().updateMask(clear.and(st.gt(0))).copyProperties(img, ['system:time_start']);
}
function composite(range) {   // 장면별 시가지 평균을 뺀 편차로 바꾼 뒤 중앙값 (날씨·연도 차이 제거)
  var col = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2').merge(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2'))
    .filterBounds(aoi).filterDate(range[0], range[1]).filter(ee.Filter.calendarRange(M[0], M[1], 'month'))
    .filter(ee.Filter.lt('CLOUD_COVER', CFG.landsat.max_cloud)).map(lsPrep)
    .map(function (img) { return img.set('m', img.select('LST').reduceRegion({reducer: ee.Reducer.mean(), geometry: aoi, scale: SC.scene_mean, maxPixels: 1e9}).get('LST')); })
    .filter(ee.Filter.notNull(['m']))
    .map(function (img) { return img.addBands(img.select('LST').subtract(ee.Number(img.get('m'))).rename('LSTa').toFloat()); });
  return {n: col.size(), img: col.select(['NDVI', 'LSTa']).median()};
}
var B = composite(CH.before), A = composite(CH.after);
var dN = A.img.select('NDVI').subtract(B.img.select('NDVI')).rename('dN');
var dT = A.img.select('LSTa').subtract(B.img.select('LSTa')).rename('dT');
var stack = ee.Image.constant(1).rename('c').addBands(dN).addBands(dT).updateMask(notWater);

function fit(mask, tag) {   // dT = a + b·dN, 녹지가 변한 픽셀만
  var s = stack.updateMask(mask);
  var reg = s.select(['c', 'dN', 'dT']).reduceRegion({reducer: ee.Reducer.linearRegression({numX: 2, numY: 1}), geometry: aoi, scale: SC.landsat, maxPixels: 1e10, tileScale: 8});
  var st = s.select(['dN', 'dT']).reduceRegion({reducer: ee.Reducer.mean().combine(ee.Reducer.count(), null, true), geometry: aoi, scale: SC.landsat, maxPixels: 1e10, tileScale: 8});
  var d = {}; d[tag + '_slope'] = ee.Array(reg.get('coefficients')).project([0]).get([1]);
  d[tag + '_n'] = st.get('dN_count'); d[tag + '_mean_dN'] = st.get('dN_mean'); d[tag + '_mean_dT'] = st.get('dT_mean');
  return ee.Dictionary(d);
}
var out = fit(dN.gte(CH.min_change), 'green')
  .combine(fit(dN.lte(-CH.min_change), 'loss'))
  .combine(fit(dN.abs().gte(CH.min_change), 'all'))
  .combine(ee.Dictionary({scenes_before: B.n, scenes_after: A.n}));

var fc = ee.FeatureCollection(PARKS.map(function (p) { return ee.Feature(ee.Geometry.MultiPolygon(p.g), {id: p.id}); }));
var rings = fc.map(function (f) {
  var g = f.geometry();
  return ee.Feature(null, {id: f.get('id'), ring_area: g.buffer(CH.ring_m, 1).difference(g, 1).area(1)});
});

out.evaluate(function (r, err) { print(err ? 'ERROR|change ' + err : 'CHANGE|' + JSON.stringify(r)); });
rings.evaluate(function (fc2, err) {
  if (err) { print('ERROR|ring ' + err); return; }
  try {
    fc2.features.forEach(function (ft) { print('RING|' + JSON.stringify(ft.properties)); });
    print('DONE|' + fc2.features.length);
  } catch (e) { print('ERROR|print ' + e); }
});
