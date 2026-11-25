// R1-g 보전형 공원의 반사실 사례 찾기: "도시 숲 일부가 아파트·도로로 개발되고 나머지 숲은 남은 곳" (전국)
// 민간공원 특례사업(공원 30% 이내 개발 + 70% 이상 공원)과 같은 모양을 위성으로 직접 찾는다.
// 실측 자료만: Landsat 8·9 C2 L2(여름 NDVI), Dynamic World(2023~24 건물 확률), GHSL SMOD 2015(도시 여부).
var AOI = ee.Geometry.Rectangle([126.0, 34.3, 129.6, 38.3]);   // 남한 본토
var PRE = ['2013-01-01', '2015-12-31'], POST = ['2022-01-01', '2024-12-31'];
var NDVI_PRE_MIN = 0.65, NDVI_POST_MAX = 0.35, MIN_PIX = 22;   // 30m 22칸 ≈ 2ha (특례 비공원시설 규모)
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
var built = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filterBounds(AOI).filterDate('2023-01-01', '2024-12-31')
  .select('built').mean().gt(0.4).reproject('EPSG:4326', null, 30);
var smod = ee.Image('JRC/GHSL/P2023A/GHS_SMOD/2015').select('smod_code');
var urban = smod.gte(21).reproject('EPSG:4326', null, 1000).focal_max(1000, 'circle', 'meters');
var forestNow = post.gt(NDVI_PRE_MIN).and(pre.gt(NDVI_PRE_MIN));            // 전후 모두 숲 = 남은 숲
var remain = forestNow.focal_max(150, 'circle', 'meters');                    // 남은 숲과 150m 이내
var cand = pre.gt(NDVI_PRE_MIN).and(post.lt(NDVI_POST_MAX)).and(built).and(urban).and(remain).selfMask().rename('c');
var vec = cand.reduceToVectors({
  geometry: AOI, scale: 30, geometryType: 'polygon', eightConnected: true, labelProperty: 'c',
  reducer: ee.Reducer.countEvery(), maxPixels: 1e11, bestEffort: false, tileScale: 8});
vec = vec.filter(ee.Filter.gte('count', MIN_PIX));
var out = vec.map(function (f) {
  var g = f.geometry(), c = g.centroid(10).coordinates();
  var ring = g.buffer(300, 10).difference(g, 10);
  var fr = forestNow.rename('f').reduceRegion(ee.Reducer.mean(), ring, 30, null, null, false, 1e8).get('f');  // 주변 300m 중 남은 숲 비율
  return ee.Feature(g, {lon: c.get(0), lat: c.get(1), px: f.get('count'), forest_ring: fr});
});
Export.table.toAsset({collection: out, description: 'r3_forestloss', assetId: 'projects/cheongju-grpi/assets/r3_forestloss'});
print('EXPORT|queued');
