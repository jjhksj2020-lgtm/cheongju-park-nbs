// R1-h 숲 일부 개발 사례(r3_forestloss)의 전후 지표온도: (A) 숲을 잃은 곳이 얼마나 더워졌나 (B) 남은 숲이 새 단지를 얼마나 식히나
// 전 2013~2015, 후 2022~2024 여름. 장면별 10km 중앙값 정규화(LSTa). 학술용 GEE.
var MIN_FOREST_RING = 0.3;   // 주변 300m 중 남은 숲 30% 이상인 사례만 (특례사업형: 개발부 + 남은 공원 숲)
var P = ee.FeatureCollection('projects/cheongju-grpi/assets/r3_forestloss').filter(ee.Filter.gte('forest_ring', MIN_FOREST_RING));
function prep(img) {
  var qa = img.select('QA_PIXEL');
  var m = qa.bitwiseAnd(1 << 1).eq(0).and(qa.bitwiseAnd(1 << 3).eq(0)).and(qa.bitwiseAnd(1 << 4).eq(0)).and(qa.bitwiseAnd(1 << 5).eq(0));
  var t = img.select('ST_B10').multiply(0.00341802).add(149.0).subtract(273.15).rename('lst');
  var sr = img.select(['SR_B4', 'SR_B5']).multiply(0.0000275).add(-0.2);
  return t.addBands(sr.normalizedDifference(['SR_B5', 'SR_B4']).rename('ndvi')).updateMask(m).toFloat().copyProperties(img, ['system:time_start']);
}
function comp(pt, a, b) {
  var box = pt.buffer(10000).bounds();
  return ee.ImageCollection('LANDSAT/LC08/C02/T1_L2').merge(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2'))
    .filterBounds(pt).filterDate(a, b).filter(ee.Filter.calendarRange(6, 9, 'month')).filter(ee.Filter.lt('CLOUD_COVER', 40)).map(prep)
    .map(function (im) { return im.set('med', im.select('lst').reduceRegion(ee.Reducer.median(), box, 90, null, null, false, 1e8).get('lst')); })
    .filter(ee.Filter.notNull(['med']))
    .map(function (im) { return im.addBands(im.select('lst').subtract(ee.Number(im.get('med'))).rename('lsta')); });
}
var out = P.map(function (f) {
  var g = f.geometry(), pt = g.centroid(10);
  var pre = comp(pt, '2013-01-01', '2015-12-31'), post = comp(pt, '2022-01-01', '2024-12-31');
  var a = pre.select(['lsta', 'ndvi']).median(), b = post.select(['lsta', 'ndvi']).median();
  var d = b.subtract(a);
  function mean(img, band, geom) { return img.select(band).reduceRegion(ee.Reducer.mean(), geom, 30, null, null, false, 1e8).get(band); }
  var props = {n_pre: pre.size(), n_post: post.size(), area_ha: g.area(10).divide(1e4),
               ndvi_pre: mean(a, 'ndvi', g), ndvi_post: mean(b, 'ndvi', g)};
  // (A) 개발부와 바깥 고리의 전후 변화
  [[0, 100], [100, 200], [200, 300], [300, 500]].forEach(function (r) {
    var z = g.buffer(r[1], 10).difference(r[0] === 0 ? g : g.buffer(r[0], 10), 10);
    props['d_' + r[0] + '_' + r[1]] = mean(d, 'lsta', z);
  });
  props.d_in = mean(d, 'lsta', g);
  // (B) 후 시점, 개발부 안에서 남은 숲(전후 모두 NDVI>0.65)까지 거리별 LSTa
  var forest = a.select('ndvi').gt(0.65).and(b.select('ndvi').gt(0.65));
  var fd = forest.selfMask().reproject(ee.Projection('EPSG:32652').atScale(30)).fastDistanceTransform(30).sqrt().multiply(30).rename('fd');   // 남은 숲까지 거리(m)
  var bands = b.select('lsta');
  [[0, 60], [60, 120], [120, 240], [240, 600]].forEach(function (r) {
    var msk = fd.gte(r[0]).and(fd.lt(r[1]));
    props['f_' + r[0] + '_' + r[1]] = bands.updateMask(msk).reduceRegion(ee.Reducer.mean(), g, 30, null, null, false, 1e8).get('lsta');
  });
  return ee.Feature(pt, props).copyProperties(f, ['lat', 'lon', 'px', 'forest_ring']);
});
Export.table.toAsset({collection: out, description: 'r3_did', assetId: 'projects/cheongju-grpi/assets/r3_did'});
print('N|' + P.size().getInfo());
