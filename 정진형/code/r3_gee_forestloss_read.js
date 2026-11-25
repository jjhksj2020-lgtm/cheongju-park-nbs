// r3_forestloss 읽기: 위도,경도,픽셀수,주변300m 남은숲비율 (픽셀 큰 순)
var fc = ee.FeatureCollection('projects/cheongju-grpi/assets/r3_forestloss').sort('px', false);
print('N|' + fc.size().getInfo());
fc.limit(2000).evaluate(function (r, e) {
  if (e) { print('ERR|' + e); return; }
  print('F|' + r.features.map(function (f) { var p = f.properties;
    return p.lat.toFixed(4) + ',' + p.lon.toFixed(4) + ',' + p.px + ',' + (p.forest_ring == null ? 'na' : p.forest_ring.toFixed(2)); }).join(';'));
});
