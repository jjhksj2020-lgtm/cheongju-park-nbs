"""관측소 위치의 위성 지표온도를 뽑는 GEE 스크립트 만들기 → code/gee/kma_lst_gee.js
입력: data/raw/kma/stations.csv(기간별 좌표), params.yaml priority.energy.lst_air
실행 후: GEE 코드 편집기에 붙여넣고 Run → Tasks에서 cheongju_station_lst RUN → Drive cheongju_hotspot 폴더의 CSV를 data/raw/kma/ 에 둔다 → kma_lst_air.py"""
import csv, json, os
from common import EDC, EDC_P, RAW

A = EDC_P['priority']['energy']['lst_air']
S = [[int(r['stn']), r['name'], r['start'], r['end'] or '2100-01-01', float(r['lon']), float(r['lat'])]
     for r in csv.DictReader(open(f'{RAW}/kma/stations.csv', encoding='utf-8'))]
js = r"""// 청주 기상 관측소 위치의 Landsat 8·9 여름 지표온도 (자동 생성: need/edc/code/build_kma_gee.py)
// 실행: 붙여넣기 → Run → 오른쪽 Tasks 탭에서 cheongju_station_lst RUN
var C = __CFG__;
var STN = __STN__;   // [지점번호, 이름, 시작일, 종료일, 경도, 위도] — 이전한 지점은 기간별로 따로
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
"""
js = js.replace('__CFG__', json.dumps(A, ensure_ascii=False)).replace('__STN__', json.dumps(S, ensure_ascii=False))
out = f'{EDC}/code/gee/kma_lst_gee.js'
open(out, 'w', encoding='utf-8').write(js)
print(out, len(js), '자 · 관측소 기간', len(S))
