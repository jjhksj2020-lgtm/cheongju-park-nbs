// R1-b 조성 사례 위성 탐지 (Google Earth Engine, 프로젝트 cheongju-grpi · 학술용)
// 수도권·충청권 도시지역에서 "조성 전 비녹지 → 조성 후 녹지"로 바뀐 덩어리(0.5ha 이상)를 찾는다.
// 실측 자료만: Landsat 8·9 C2 L2(여름 NDVI), ESA WorldCover v200(2021), GHSL SMOD 2015(도시 여부).
var AOI = ee.Geometry.Rectangle([126.6, 36.0, 127.9, 37.75]);
var PRE = ['2013-01-01', '2015-12-31'], POST = ['2022-01-01', '2024-12-31'];
var NDVI_PRE_MAX = 0.25, NDVI_POST_MIN = 0.5, MIN_PIX = 6;   // 30m 6칸 = 0.54ha
function prep(img) {
  var qa = img.select('QA_PIXEL');
  var mask = qa.bitwiseAnd(1 << 1).eq(0).and(qa.bitwiseAnd(1 << 3).eq(0)).and(qa.bitwiseAnd(1 << 4).eq(0)).and(qa.bitwiseAnd(1 << 5).eq(0));
  var sr = img.select(['SR_B4', 'SR_B5']).multiply(0.0000275).add(-0.2);
  return sr.normalizedDifference(['SR_B5', 'SR_B4']).rename('ndvi').updateMask(mask).toFloat();
}
function ndvi(range) {
  return ee.ImageCollection('LANDSAT/LC08/C02/T1_L2').merge(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2'))
    .filterBounds(AOI).filterDate(range[0], range[1]).filter(ee.Filter.calendarRange(6, 9, 'month'))
    .filter(ee.Filter.lt('CLOUD_COVER', 40)).map(prep).median();
}
var pre = ndvi(PRE), post = ndvi(POST);
var wc = ee.Image('ESA/WorldCover/v200/2021').select('Map');
var smod = ee.Image('JRC/GHSL/P2023A/GHS_SMOD/2015').select('smod_code');
var urban = smod.gte(21).reproject('EPSG:4326', null, 1000).focal_max(1000, 'circle', 'meters');   // 교외 이상 + 1km
var cand = pre.lt(NDVI_PRE_MAX).and(post.gt(NDVI_POST_MIN)).and(wc.eq(10).or(wc.eq(30))).and(urban).selfMask().rename('c');
var vec = cand.reduceToVectors({
  geometry: AOI, scale: 30, geometryType: 'polygon', eightConnected: true, labelProperty: 'c',
  reducer: ee.Reducer.countEvery(), maxPixels: 1e10, bestEffort: false, tileScale: 4});
vec = vec.filter(ee.Filter.gte('count', MIN_PIX));
var out = vec.map(function (f) {
  var c = f.geometry().centroid(10).coordinates();
  return ee.Feature(f.geometry(), {lon: c.get(0), lat: c.get(1), px: f.get('count')});
});
// 대화형 실행은 5분 제한이라 배치 작업으로 자산에 저장한다. 읽기는 r1_gee_read.js
Export.table.toAsset({collection: out, description: 'r1_newgreen', assetId: 'projects/cheongju-grpi/assets/r1_newgreen'});
print('EXPORT|queued');
