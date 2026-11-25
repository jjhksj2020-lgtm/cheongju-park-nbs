// R1-f 우리 40개 공원(경계 39개) 주변 현재 여름 지표온도의 거리별 분포 — 공원 밖 "건물(시가지) 픽셀"만으로
// 질문: 이 공원(현재 상태) 덕분에 주변 시가지가 몇 m까지 시원한가? → 에너지 단계의 혜택 범위
// 경계: biz/data/vworld/parks.txt (V-World 도시계획시설 공원) → 정진형/data/parks40_geom.json
var PARKS = __PARKS__;  // [site_id, 이름, 면적㎡, kind, 우세토지이용, 멀티폴리곤 좌표]
var EDGES = [0, 30, 60, 90, 120, 150, 210, 300, 420, 600];   // 공원 경계 바깥 거리(m)
var BASE = [600, 1500];                                         // 기준 고리(m)
var AOI = ee.Geometry.Rectangle([127.25, 36.45, 127.75, 36.85]);
var built = ee.ImageCollection('ESA/WorldCover/v200').first().eq(50);        // 2021 시가지
var water = ee.ImageCollection('ESA/WorldCover/v200').first().eq(80);
function prep(img) {
  var qa = img.select('QA_PIXEL');
  var m = qa.bitwiseAnd(1 << 1).eq(0).and(qa.bitwiseAnd(1 << 3).eq(0)).and(qa.bitwiseAnd(1 << 4).eq(0)).and(qa.bitwiseAnd(1 << 5).eq(0));
  var t = img.select('ST_B10').multiply(0.00341802).add(149.0).subtract(273.15).rename('lst');
  var sr = img.select(['SR_B4', 'SR_B5']).multiply(0.0000275).add(-0.2);
  return t.addBands(sr.normalizedDifference(['SR_B5', 'SR_B4']).rename('ndvi')).updateMask(m).toFloat()
    .copyProperties(img, ['system:time_start']);
}
var col = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2').merge(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2'))
  .filterBounds(AOI).filterDate('2020-01-01', '2025-12-31').filter(ee.Filter.calendarRange(6, 9, 'month'))
  .filter(ee.Filter.lt('CLOUD_COVER', 40)).map(prep)
  .map(function (im) { return im.set('med', im.select('lst').reduceRegion(ee.Reducer.median(), AOI, 120, null, null, false, 1e9).get('lst')); })
  .filter(ee.Filter.notNull(['med']))
  .map(function (im) { return im.addBands(im.select('lst').subtract(ee.Number(im.get('med'))).rename('lsta')); });
var comp = col.select(['lsta', 'ndvi']).median();
var img = comp.select('lsta').rename('all')
  .addBands(comp.select('lsta').updateMask(built).rename('bld'))
  .addBands(comp.select('ndvi'))
  .addBands(built.rename('bfrac'))
  .updateMask(water.not());
var feats = [];
PARKS.forEach(function (p) {
  var g = ee.Geometry.MultiPolygon(p[5]);
  feats.push(ee.Feature(g, {sid: p[0], z: 'in'}));
  for (var i = 0; i < EDGES.length - 1; i++) {
    feats.push(ee.Feature(g.buffer(EDGES[i + 1], 5).difference(g.buffer(EDGES[i], 5), 5), {sid: p[0], z: EDGES[i] + '_' + EDGES[i + 1]}));
  }
  feats.push(ee.Feature(g.buffer(BASE[1], 10).difference(g.buffer(BASE[0], 10), 10), {sid: p[0], z: 'base'}));
});
var red = ee.Reducer.mean().combine(ee.Reducer.count(), null, true);
var out = img.select(['all', 'bld', 'ndvi', 'bfrac']).reduceRegions(ee.FeatureCollection(feats), red, 30);
print('NSCENE|' + col.size().getInfo());
Export.table.toAsset({collection: out.map(function (f) { return f.setGeometry(f.geometry().centroid(10)); }),
                      description: 'r1_profile40', assetId: 'projects/cheongju-grpi/assets/r1_profile40'});
