// R1-c 조성 사례 전후 지표온도 DiD (거리별 고리) — Google Earth Engine, 학술용
// 입력 CASES: 공식 기록으로 조성 연도를 확인한 사례 [id, 공원명, 개장연도, 위도, 경도]
// 공원 범위 = r1_newgreen 자산에서 그 좌표를 포함(없으면 300m 안 가장 큰) "새 녹지 덩어리"(위성 실측 변화 범위)
var CASES = __CASES__;
var GREEN = ee.FeatureCollection('projects/cheongju-grpi/assets/r1_newgreen');
var RINGS = [[0, 100], [100, 200], [200, 300], [300, 500]];
var CTRL = [2000, 5000];          // 대조 고리(m)
var STABLE = 0.05;                // 대조 픽셀: 전후 NDVI 변화 < 0.05
function lst(img) {
  var qa = img.select('QA_PIXEL');
  var m = qa.bitwiseAnd(1 << 1).eq(0).and(qa.bitwiseAnd(1 << 3).eq(0)).and(qa.bitwiseAnd(1 << 4).eq(0)).and(qa.bitwiseAnd(1 << 5).eq(0));
  var t = img.select('ST_B10').multiply(0.00341802).add(149.0).subtract(273.15);
  var sr = img.select(['SR_B4', 'SR_B5']).multiply(0.0000275).add(-0.2);
  return t.rename('lst').addBands(sr.normalizedDifference(['SR_B5', 'SR_B4']).rename('ndvi')).updateMask(m).toFloat()
    .copyProperties(img, ['system:time_start']);
}
function period(pt, y0, y1) {
  var box = pt.buffer(10000).bounds();
  var col = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2').merge(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2'))
    .filterBounds(pt).filterDate(y0 + '-01-01', y1 + '-12-31').filter(ee.Filter.calendarRange(6, 9, 'month'))
    .filter(ee.Filter.lt('CLOUD_COVER', 40)).map(lst);
  var anom = col.map(function (im) {      // 장면별 10km 상자 중앙값 대비 → 날씨 영향 제거
    var med = im.select('lst').reduceRegion(ee.Reducer.median(), box, 90, null, null, false, 1e8).get('lst');
    return im.addBands(im.select('lst').subtract(ee.Number(med)).rename('lsta')).set('ok', ee.Algorithms.IsEqual(med, null).not());
  }).filter(ee.Filter.eq('ok', true));
  return {img: anom.select(['lsta', 'ndvi']).median(), n: anom.size()};
}
function one(c) {
  var pt = ee.Geometry.Point([c[4], c[3]]);
  var hit = GREEN.filterBounds(pt.buffer(300)).sort('px', false).first();
  var park = ee.Feature(hit).geometry();
  var y = c[2];
  var pre = period(pt, y - 3, y - 1), post = period(pt, y + 1, y + 3), late = period(pt, y + 4, Math.min(y + 6, 2025));
  var d = post.img.subtract(pre.img), dl = late.img.subtract(pre.img);
  var ctrlZone = park.buffer(CTRL[1]).difference(park.buffer(CTRL[0]));
  var stable = d.select('ndvi').abs().lt(STABLE);
  var ctrl = d.select('lsta').updateMask(stable).reduceRegion(ee.Reducer.median(), ctrlZone, 30, null, null, false, 1e9).get('lsta');
  function zoneVal(img, g) { return img.select('lsta').reduceRegion(ee.Reducer.mean(), g, 30, null, null, false, 1e8).get('lsta'); }
  var zones = [['in', park]].concat(RINGS.map(function (r) {
    return [r[0] + '_' + r[1], park.buffer(r[1]).difference(r[0] === 0 ? park : park.buffer(r[0]))];
  }));
  var props = {id: c[0], name: c[1], year: y, area_ha: park.area(1).divide(1e4), n_pre: pre.n, n_post: post.n, n_late: late.n, ctrl: ctrl,
               ndvi_pre: pre.img.select('ndvi').reduceRegion(ee.Reducer.mean(), park, 30).get('ndvi'),
               ndvi_post: post.img.select('ndvi').reduceRegion(ee.Reducer.mean(), park, 30).get('ndvi')};
  zones.forEach(function (z) {
    props['d_' + z[0]] = ee.Number(zoneVal(d, z[1])).subtract(ee.Number(ctrl));
    props['dl_' + z[0]] = zoneVal(dl, z[1]);
  });
  return ee.Feature(null, props);
}
var res = ee.FeatureCollection(CASES.map(one));
res.evaluate(function (fc, e) {
  if (e) { print('ERR|' + e); return; }
  fc.features.forEach(function (f) { print('R|' + JSON.stringify(f.properties)); });
  print('DONE|');
});
