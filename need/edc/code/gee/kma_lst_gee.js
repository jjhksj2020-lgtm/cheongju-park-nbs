// 청주 기상 관측소 위치의 Landsat 8·9 여름 지표온도 (자동 생성: need/edc/code/build_kma_gee.py)
// 실행: 붙여넣기 → Run → 오른쪽 Tasks 탭에서 cheongju_station_lst RUN
var C = {"years": [2020, 2024], "months": [6, 9], "cloud_max": 60, "buffer_m": 60, "hour_kst": 11, "min_stations": 4, "lapse_c_per_m": 0.0065};
var STN = [[131, "청주", "2000-01-01", "2100-01-01", 127.44066, 36.63924], [181, "서청주", "2000-01-01", "2100-01-01", 127.38458, 36.63994], [327, "청주금천", "2022-10-22", "2100-01-01", 127.5128, 36.6261], [327, "우암산", "2001-10-25", "2022-10-22", 127.512, 36.6503], [624, "상당", "2018-05-08", "2100-01-01", 127.6571, 36.6244], [641, "가덕", "2020-09-18", "2100-01-01", 127.5239, 36.5461], [641, "대청", "2017-08-25", "2020-09-18", 127.5017, 36.5223], [888, "청남대", "2012-08-10", "2100-01-01", 127.4907, 36.4627], [977, "오창가곡", "2020-10-23", "2100-01-01", 127.4669, 36.7246], [977, "오창가곡", "2018-02-01", "2020-10-23", 127.4428, 36.6363]];   // [지점번호, 이름, 시작일, 종료일, 경도, 위도] — 이전한 지점은 기간별로 따로
var pts = ee.FeatureCollection(STN.map(function (s) {
  return ee.Feature(ee.Geometry.Point([s[4], s[5]]).buffer(C.buffer_m), {stn: s[0], name: s[1], start: s[2], end: s[3]});
}));
function prep(img) {
  var qa = img.select('QA_PIXEL');
  var m = qa.bitwiseAnd(1 << 1).eq(0).and(qa.bitwiseAnd(1 << 3).eq(0)).and(qa.bitwiseAnd(1 << 4).eq(0)).and(qa.bitwiseAnd(1 << 5).eq(0));
  return img.select('ST_B10').multiply(0.00341802).add(149.0).subtract(273.15).rename('lst').updateMask(m)
    .set('t', img.date().format('YYYY-MM-dd HH:mm', 'Asia/Seoul'), 'cloud', img.get('CLOUD_COVER'));
}
var col = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2').merge(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2'))
  .filterBounds(pts.geometry()).filterDate(C.years[0] + '-01-01', (C.years[1] + 1) + '-01-01')
  .filter(ee.Filter.calendarRange(C.months[0], C.months[1], 'month')).filter(ee.Filter.lt('CLOUD_COVER', C.cloud_max)).map(prep);
var out = col.map(function (im) {
  return im.reduceRegions({collection: pts, reducer: ee.Reducer.mean().combine(ee.Reducer.count(), null, true), scale: 30})
    .map(function (f) { return f.set('t', im.get('t'), 'cloud', im.get('cloud')).setGeometry(null); });
}).flatten();
print('장면 수', col.size());
Export.table.toDrive({collection: out, description: 'cheongju_station_lst', folder: 'cheongju_hotspot', fileFormat: 'CSV',
  selectors: ['stn', 'name', 'start', 'end', 't', 'cloud', 'mean', 'count']});
