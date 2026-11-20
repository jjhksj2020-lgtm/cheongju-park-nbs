// R1-b2 매칭된 공원 덩어리의 연도별 여름 NDVI (2013~2025) → 위성 기준 녹지 정착 연도, 주변(100~300m) 녹지 변화
var PTS = __PTS__;   // [idx, 덩어리 위도, 경도]
var GREEN = ee.FeatureCollection('projects/cheongju-grpi/assets/r1_newgreen');
var patch = ee.FeatureCollection(PTS.map(function (p) {
  var pt = ee.Geometry.Point([p[2], p[1]]);
  var g = ee.Feature(GREEN.filterBounds(pt.buffer(60)).sort('px', false).first()).geometry();
  return ee.Feature(g, {idx: p[0]});
}));
var ring = patch.map(function (f) { return ee.Feature(f.geometry().buffer(300).difference(f.geometry().buffer(100), 1), {idx: f.get('idx')}); });
function prep(img) {
  var qa = img.select('QA_PIXEL');
  var m = qa.bitwiseAnd(1 << 1).eq(0).and(qa.bitwiseAnd(1 << 3).eq(0)).and(qa.bitwiseAnd(1 << 4).eq(0)).and(qa.bitwiseAnd(1 << 5).eq(0));
  var sr = img.select(['SR_B4', 'SR_B5']).multiply(0.0000275).add(-0.2);
  return sr.normalizedDifference(['SR_B5', 'SR_B4']).rename('ndvi').updateMask(m).toFloat();
}
var col = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2').merge(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2'))
  .filterBounds(patch.geometry().bounds()).filter(ee.Filter.calendarRange(6, 9, 'month')).filter(ee.Filter.lt('CLOUD_COVER', 40)).map(prep);
var stack = ee.Image.cat(ee.List.sequence(2013, 2025).getInfo().map(function (y) {
  var c = col.filterDate(y + '-01-01', (y + 1) + '-01-01');
  var empty = ee.Image.constant(0).toFloat().updateMask(ee.Image.constant(0));
  return ee.Image(ee.Algorithms.If(c.size().gt(0), c.median(), empty)).rename('y' + y);
}));
var a = stack.reduceRegions(patch, ee.Reducer.mean(), 30);
var b = stack.reduceRegions(ring, ee.Reducer.mean(), 30);
var ha = patch.map(function (f) { return f.set('ha', f.geometry().area(1).divide(1e4)); }).aggregate_array('ha');
ee.List([a.toList(200), b.toList(200), ha]).evaluate(function (r, e) {
  if (e) { print('ERR|' + e); return; }
  var out = r[0].map(function (fa, i) {
    var pa = fa.properties, pb = r[1][i].properties, s = [];
    for (var y = 2013; y <= 2025; y++) {
      var x = pa['y' + y], z = pb['y' + y];
      s.push((x == null ? 'na' : x.toFixed(2)) + '/' + (z == null ? 'na' : z.toFixed(2)));
    }
    return pa.idx + ':' + r[2][i].toFixed(2) + ':' + s.join(',');
  });
  print('Y|' + out.join(';'));
  print('DONE|');
});
