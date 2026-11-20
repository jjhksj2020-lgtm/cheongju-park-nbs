// R1-c DiD 결과 자산 읽기 → 한 줄 요약(id,전,후,면적ha,장면수전,장면수후,대조,d_in,d_0_100,d_100_200,d_200_300,d_300_500,ndvi전,ndvi후)
var fc = ee.FeatureCollection('projects/cheongju-grpi/assets/r1_did');
fc.toList(500).evaluate(function (fs, e) {
  if (e) { print('ERR|' + e); return; }
  function f(v) { return v == null ? 'na' : v.toFixed(2); }
  print('R|' + fs.map(function (x) { var p = x.properties; return [p.id, p.pre, p.post, f(p.area_ha), p.n_pre, p.n_post, f(p.ctrl)]
    .concat(['in', '0_100', '100_200', '200_300', '300_500'].map(function (k) { return f(p['d_' + k]); }))
    .concat([f(p.ndvi_pre), f(p.ndvi_post)]).join(','); }).join(';'));
  print('DONE|');
});
