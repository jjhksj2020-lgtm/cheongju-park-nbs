"""GEE 핫스팟 스크립트 만들기 → need/edc/code/gee/hotspot_gee.js
params.yaml hotspot 값과 청주 경계·생활권 5개·공원 39개 경계를 스크립트 안에 넣는다(코드에 숫자를 직접 쓰지 않기 위해).
실행 후: code.earthengine.google.com 에 hotspot_gee.js 전체를 붙여넣고 Run → Tasks 탭에서 내보내기 2개 Run
        → Google Drive의 cheongju_hotspot 폴더에서 받은 파일 2개를 need/edc/data/raw/hotspot/ 에 둔다 → build_hotspot.py
"""
import json, os, sys
from shapely.geometry import mapping
from shapely.ops import transform, unary_union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_edc as be
from common import EDC, EDC_P, ROOT, _dec, parks_5186, sites, to4326

H = EDC_P['hotspot']


def coords(g, tol):
    g = transform(to4326, g.simplify(tol))
    m = mapping(g)
    polys = m['coordinates'] if m['type'] == 'MultiPolygon' else [m['coordinates']]
    return [[[[round(x, 5), round(y, 5)] for x, y in ring] for ring in p] for p in polys]


def zones_5186():
    """생활권 5개: 도심생활권 = params downtown_dongs, 나머지는 구 = 생활권 (build_edc.py와 같은 규칙)."""
    dgeo, _, dgu = be.dongs(); DT = set(EDC_P['downtown_dongs'])
    z = {}
    for n, g in dgeo.items():
        z.setdefault('도심생활권' if n in DT else f"{dgu[n][:2]}생활권", []).append(g)
    return {k: unary_union(v).buffer(0) for k, v in z.items()}


def main():
    zones = zones_5186()
    city = unary_union(list(zones.values()))
    parks = parks_5186()
    P = [[int(s['site_id']), s['name'], coords(parks[s['site_id']], 1)] for s in sites() if s['site_id'] in parks]
    Z = [[k, coords(g, 30)] for k, g in zones.items()]
    cfg = dict(H, city=coords(city, 50))
    js = TEMPLATE.replace('__CFG__', json.dumps(cfg, ensure_ascii=False)) \
                 .replace('__ZONES__', json.dumps(Z, ensure_ascii=False)) \
                 .replace('__PARKS__', json.dumps(P, ensure_ascii=False))
    os.makedirs(f'{EDC}/code/gee', exist_ok=True)
    out = f'{EDC}/code/gee/hotspot_gee.js'
    open(out, 'w', encoding='utf-8').write(js)
    print(out, os.path.getsize(out) // 1024, 'KB · 공원', len(P), '· 생활권', len(Z))


TEMPLATE = r"""// 청주 열 핫스팟 (자동 생성: need/edc/code/build_hotspot_gee.py — 직접 고치지 말고 params.yaml을 고친 뒤 다시 만든다)
// 방법: 여름 NDVI·지표온도 5년 → 취약도 comb → 시가지만 → 상위 30/20/10% = 등급 1/2/3 → 공원 경계+150m 최고 등급
// 실행: 이 파일 전체를 code.earthengine.google.com 에 붙여넣고 Run → 오른쪽 Tasks 탭에서 두 작업 모두 RUN
var C = __CFG__;
var ZONES = __ZONES__;   // [생활권 이름, 멀티폴리곤]
var PARKS = __PARKS__;   // [site_id, 이름, 멀티폴리곤]
var CITY = ee.Geometry.MultiPolygon(C.city);

function prep(img) {
  var qa = img.select('QA_PIXEL');
  var m = qa.bitwiseAnd(1 << 1).eq(0).and(qa.bitwiseAnd(1 << 3).eq(0)).and(qa.bitwiseAnd(1 << 4).eq(0)).and(qa.bitwiseAnd(1 << 5).eq(0));
  var t = img.select('ST_B10').multiply(0.00341802).add(149.0).subtract(273.15).rename('lst');   // Collection 2 L2 지표온도(°C)
  var sr = img.select(['SR_B4', 'SR_B5']).multiply(0.0000275).add(-0.2);
  return t.addBands(sr.normalizedDifference(['SR_B5', 'SR_B4']).rename('ndvi')).updateMask(m).toFloat();
}
var L89 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2').merge(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2'))
  .filterBounds(CITY).filter(ee.Filter.calendarRange(C.months[0], C.months[1], 'month'))
  .filter(ee.Filter.lt('CLOUD_COVER', C.cloud_max));
var years = ee.List.sequence(C.years[0], C.years[1]);
var yearly = ee.ImageCollection(years.map(function (y) {
  return L89.filter(ee.Filter.calendarRange(y, y, 'year')).map(prep).median().set('year', y);
}));
var env = yearly.mean();                                       // 연도별 여름 중앙값의 평균
var nscene = L89.filterDate(C.years[0] + '-01-01', (C.years[1] + 1) + '-01-01').size();

var dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filterBounds(CITY)
  .filterDate(C.years[0] + '-01-01', (C.years[1] + 1) + '-01-01').select('label').mode();
var urban = ee.Image(0);
C.urban_dw.forEach(function (k) { urban = urban.or(dw.eq(k)); });

var comb = ee.Image(C.ndvi_ref).subtract(env.select('ndvi')).divide(C.ndvi_span)
  .add(env.select('lst').subtract(C.lst_ref).divide(C.lst_span)).rename('comb');
var combU = comb.updateMask(urban);
var pct = combU.reduceRegion({reducer: ee.Reducer.percentile(C.percentiles), geometry: CITY, scale: C.scale_m, maxPixels: 1e10, tileScale: 4});
var grade = ee.Image(0);
C.percentiles.forEach(function (p) { grade = grade.add(combU.gte(ee.Number(pct.get('comb_p' + p)))); });
grade = grade.updateMask(urban).unmask(0).clip(CITY).rename('grade').toByte();

// 1) 공원별(경계 + 150m)·생활권별 값 → CSV
var feats = PARKS.map(function (p) {
  var g = ee.Geometry.MultiPolygon(p[2]);
  return ee.Feature(g.buffer(C.sample_buffer_m, 5), {kind: 'park', id: p[0], name: p[1]});
}).concat(ZONES.map(function (z) {
  return ee.Feature(ee.Geometry.MultiPolygon(z[1]), {kind: 'zone', id: z[0], name: z[0]});
}));
var stack = grade.addBands(comb).addBands(env).addBands(urban.rename('urban'));
var out = ee.FeatureCollection(feats).map(function (f) {
  var g = f.geometry();
  var a = stack.select('grade').reduceRegion(ee.Reducer.max(), g, C.scale_m, null, null, false, 1e9);
  var b = stack.select(['comb', 'lst', 'ndvi', 'urban']).reduceRegion(ee.Reducer.mean(), g, C.scale_m, null, null, false, 1e9);
  var h = stack.select('grade').eq(2).or(stack.select('grade').eq(3)).reduceRegion(ee.Reducer.mean(), g, C.scale_m, null, null, false, 1e9);
  return ee.Feature(null, {kind: f.get('kind'), id: f.get('id'), name: f.get('name'),
    grade_max: a.get('grade'), comb_mean: b.get('comb'), lst_mean: b.get('lst'), ndvi_mean: b.get('ndvi'),
    urban_share: b.get('urban'), hot2_share: h.get('grade'),
    p70: pct.get('comb_p' + C.percentiles[0]), p80: pct.get('comb_p' + C.percentiles[1]), p90: pct.get('comb_p' + C.percentiles[2]),
    nscene: nscene});
});
print('Landsat 장면 수', nscene, '시가지 comb 분위', pct);
Map.centerObject(CITY, 11);
Map.addLayer(grade.updateMask(grade.gt(0)), {min: 1, max: 3, palette: ['fdd49e', 'fc8d59', 'b30000']}, '핫스팟 등급');
Export.table.toDrive({collection: out, description: 'cheongju_hotspot_sites', folder: C.drive_folder, fileFormat: 'CSV'});
// 2) 핫스팟 등급 지도 → GeoTIFF (0 = 시가지 아님 또는 등급 없음)
Export.image.toDrive({image: grade, description: 'cheongju_hotspot_grade', folder: C.drive_folder,
  region: CITY.bounds(), scale: C.scale_m, crs: 'EPSG:4326', maxPixels: 1e10});
"""

if __name__ == '__main__':
    main()
