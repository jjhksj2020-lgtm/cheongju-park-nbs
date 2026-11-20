// R1-c 조성 사례 전후 지표온도 DiD (거리별 고리) — Google Earth Engine, 학술용
// 입력 CASES: [id, 공원명, 전 시작연도, 전 끝연도, 후 시작연도, 후 끝연도, 위도, 경도]
//   전 = 위성 NDVI가 가장 낮던 공사/나대지 시기(trough), 후 = 녹지가 자리잡은 2022~2024 (r1_onset.py가 정함)
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
    return im.set('med', im.select('lst').reduceRegion(ee.Reducer.median(), box, 90, null, null, false, 1e8).get('lst'));
  }).filter(ee.Filter.notNull(['med'])).map(function (im) {
    return im.addBands(im.select('lst').subtract(ee.Number(im.get('med'))).rename('lsta'));
  });
  return {img: anom.select(['lsta', 'ndvi']).median(), n: anom.size()};
}
function one(c) {
  var pt = ee.Geometry.Point([c[7], c[6]]);
  var hit = GREEN.filterBounds(pt.buffer(300)).sort('px', false).first();
  var park = ee.Feature(hit).geometry();
  var pre = period(pt, c[2], c[3]), post = period(pt, c[4], c[5]);
  var d = post.img.subtract(pre.img);
  var ctrlZone = park.buffer(CTRL[1]).difference(park.buffer(CTRL[0]));
  var stable = d.select('ndvi').abs().lt(STABLE);
  var ctrl = d.select('lsta').updateMask(stable).reduceRegion(ee.Reducer.median(), ctrlZone, 30, null, null, false, 1e9).get('lsta');
  function zoneVal(img, g) { return img.select('lsta').reduceRegion(ee.Reducer.mean(), g, 30, null, null, false, 1e8).get('lsta'); }
  var zones = [['in', park]].concat(RINGS.map(function (r) {
    return [r[0] + '_' + r[1], park.buffer(r[1]).difference(r[0] === 0 ? park : park.buffer(r[0]))];
  }));
  var props = {id: c[0], pre: c[2] + '-' + c[3], post: c[4] + '-' + c[5], area_ha: park.area(1).divide(1e4), n_pre: pre.n, n_post: post.n, ctrl: ctrl,
               ndvi_pre: pre.img.select('ndvi').reduceRegion(ee.Reducer.mean(), park, 30).get('ndvi'),
               ndvi_post: post.img.select('ndvi').reduceRegion(ee.Reducer.mean(), park, 30).get('ndvi')};
  zones.forEach(function (z) {
    props['z_' + z[0]] = zoneVal(d, z[1]);   // 고리 ΔLSTa(후−전). 대조(ctrl) 빼기는 읽을 때 → 빈 값이 있어도 작업이 멈추지 않음
  });
  return ee.Feature(null, props);
}
var res = ee.FeatureCollection(CASES.map(one));
// 72곳은 대화형 5분 제한을 넘으므로 일괄 작업(Tasks → RUN)으로 자산에 저장 → r1_gee_did_read.js로 읽음
Export.table.toAsset({collection: res, description: 'r1_did', assetId: 'projects/cheongju-grpi/assets/r1_did'});
