// r1_profile40 읽기: sid,구역,all평균,bld평균,bld픽셀수,ndvi,bfrac
var fc = ee.FeatureCollection('projects/cheongju-grpi/assets/r1_profile40');
fc.toList(1000).evaluate(function (fs, e) {
  if (e) { print('ERR|' + e); return; }
  function f(v) { return v == null ? 'na' : v.toFixed(2); }
  print('P|' + fs.map(function (x) { var p = x.properties;
    return [p.sid, p.z, f(p.all_mean), f(p.bld_mean), p.bld_count == null ? 0 : p.bld_count, f(p.ndvi_mean), f(p.bfrac_mean)].join(','); }).join(';'));
});
