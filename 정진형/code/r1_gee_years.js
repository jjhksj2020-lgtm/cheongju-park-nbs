// R1-b2 매칭된 공원 덩어리의 연도별 여름 NDVI (2013~2025) → 위성 기준 녹지 정착 연도, 주변(100~300m) 녹지 변화
var PTS = __PTS__;   // [idx, 덩어리 위도, 경도]
var GREEN = ee.FeatureCollection('projects/cheongju-grpi/assets/r1_newgreen');
var feats = ee.FeatureCollection(PTS.map(function (p) {
  var pt = ee.Geometry.Point([p[2], p[1]]);
  var g = ee.Feature(GREEN.filterBounds(pt.buffer(60)).sort('px', false).first()).geometry();
  return ee.Feature(g, {idx: p[0], ring: g.buffer(300).difference(g.buffer(100))});
}));
function prep(img) {
  var qa = img.select('QA_PIXEL');
  var m = qa.bitwiseAnd(1 << 1).eq(0).and(qa.bitwiseAnd(1 << 3).eq(0)).and(qa.bitwiseAnd(1 << 4).eq(0)).and(qa.bitwiseAnd(1 << 5).eq(0));
  var sr = img.select(['SR_B4', 'SR_B5']).multiply(0.0000275).add(-0.2);
  return sr.normalizedDifference(['SR_B5', 'SR_B4']).rename('ndvi').updateMask(m).toFloat();
}
var col = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2').merge(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2'))
  .filterBounds(feats.geometry()).filter(ee.Filter.calendarRange(6, 9, 'month')).filter(ee.Filter.lt('CLOUD_COVER', 40)).map(prep);
var years = ee.List.sequence(2013, 2025);
var rows = feats.map(function (f) {
  var ring = ee.Geometry(f.get('ring'));
  var vals = years.map(function (y) {
    var im = col.filterDate(ee.Date.fromYMD(y, 1, 1), ee.Date.fromYMD(ee.Number(y).add(1), 1, 1)).median();
    var a = im.reduceRegion(ee.Reducer.mean(), f.geometry(), 30).get('ndvi');
    var b = im.reduceRegion(ee.Reducer.mean(), ring, 30).get('ndvi');
    return ee.List([a, b]);
  });
  return ee.Feature(null, {idx: f.get('idx'), v: vals, ha: f.geometry().area(1).divide(1e4)});
});
rows.evaluate(function (fc, e) {
  if (e) { print('ERR|' + e); return; }
  print('Y|' + fc.features.map(function (f) {
    var p = f.properties;
    return p.idx + ':' + p.ha.toFixed(2) + ':' + p.v.map(function (x) { return (x[0] === null ? 'na' : x[0].toFixed(2)) + '/' + (x[1] === null ? 'na' : x[1].toFixed(2)); }).join(',');
  }).join(';'));
  print('DONE|');
});
