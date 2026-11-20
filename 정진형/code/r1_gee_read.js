// R1-b 결과 읽기: 배치로 저장한 새 녹지 덩어리 → 콘솔에 압축 출력 (위도,경도,픽셀수;...)
var fc = ee.FeatureCollection('projects/cheongju-grpi/assets/r1_newgreen');
fc.size().evaluate(function (n, e) { print('N|' + n + '|' + (e || '')); });
fc.sort('px', false).limit(1500).evaluate(function (r, e) {
  if (e) { print('ERR|' + e); return; }
  print('C|' + r.features.map(function (f) { var p = f.properties; return p.lat.toFixed(4) + ',' + p.lon.toFixed(4) + ',' + p.px; }).join(';'));
  print('DONE|');
});
