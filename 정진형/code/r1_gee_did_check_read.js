// 정규화 점검 결과 읽기: id, 10km중앙값 전, 후, r_in, r_0_100, r_100_200, r_200_300, r_300_500, z_in, z_300_500
var fc = ee.FeatureCollection('projects/cheongju-grpi/assets/r1_did_raw_check');
fc.toList(500).evaluate(function (fs, e) {
  if (e) { print('ERR|' + e); return; }
  function f(v) { return v == null ? 'na' : v.toFixed(2); }
  print('K|' + fs.map(function (x) { var p = x.properties; return [p.id, f(p.box_pre), f(p.box_post)]
    .concat(['in', '0_100', '100_200', '200_300', '300_500'].map(function (k) { return f(p['r_' + k]); }))
    .concat([f(p.z_in), f(p.z_300_500)]).join(','); }).join(';'));
});
