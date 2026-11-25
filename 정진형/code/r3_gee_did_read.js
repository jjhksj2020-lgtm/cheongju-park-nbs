// r3_did 읽기: px,forest_ring,area_ha,n_pre,n_post,ndvi_pre,ndvi_post,d_in,d_0_100,d_100_200,d_200_300,d_300_500,f_0_60,f_60_120,f_120_240,f_240_600
var fc = ee.FeatureCollection('projects/cheongju-grpi/assets/r3_did');
fc.toList(1000).evaluate(function (fs, e) {
  if (e) { print('ERR|' + e); return; }
  function f(v) { return v == null ? 'na' : (typeof v === 'number' ? v.toFixed(2) : v); }
  var K = ['px', 'forest_ring', 'area_ha', 'n_pre', 'n_post', 'ndvi_pre', 'ndvi_post', 'd_in', 'd_0_100', 'd_100_200', 'd_200_300', 'd_300_500', 'f_0_60', 'f_60_120', 'f_120_240', 'f_240_600'];
  print('D|' + fs.map(function (x) { var p = x.properties; return K.map(function (k) { return k === 'px' || k.indexOf('n_') === 0 ? p[k] : f(p[k]); }).join(','); }).join(';'));
});
