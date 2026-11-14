// 청주 장기미집행 공원 — 열저감 입력값 뽑기 (Google Earth Engine Code Editor)
// 이 파일은 틀이다. make_gee_script.py 가 CFG(params.yaml의 gee)와 PARKS(biz/data/vworld/parks.txt 경계)를 채워 gee_energy.js 를 만든다.
// 출력: 콘솔에 CITY| 한 줄, PARK| 공원 수만큼. 그대로 복사해 energy/data/gee/gee_output.txt 에 붙인다.
var CFG = __CFG__;
var PARKS = __PARKS__;

var aoi = ee.Geometry.Rectangle(CFG.aoi);
var M = CFG.months, LS = CFG.landsat_scale, WC = CFG.worldcover, SC = CFG.scale_m;
var wc = ee.ImageCollection('ESA/WorldCover/v200').first();
var notWater = wc.neq(WC.water);

// ---------- Landsat: NDVI, 지표온도 편차(장면별 시가지 평균 대비) ----------
function lsPrep(img) {
  var qa = img.select('QA_PIXEL');
  var clear = ee.Image(1);
  CFG.landsat_qa_bits.forEach(function (b) { clear = clear.and(qa.bitwiseAnd(1 << b).eq(0)); });
  var sr = img.select(['SR_B4', 'SR_B5']).multiply(LS.sr_mult).add(LS.sr_add);
  var ndvi = sr.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI');
  var st = img.select('ST_B10');
  var lst = st.multiply(LS.st_mult).add(LS.st_add).subtract(LS.kelvin).rename('LST');
  return ndvi.addBands(lst).toFloat().updateMask(clear.and(st.gt(0))).copyProperties(img, ['system:time_start']);
}
var ls = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2').merge(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2'))
  .filterBounds(aoi).filterDate(CFG.landsat.start, CFG.landsat.end)
  .filter(ee.Filter.calendarRange(M[0], M[1], 'month')).filter(ee.Filter.lt('CLOUD_COVER', CFG.landsat.max_cloud))
  .map(lsPrep)
  .map(function (img) { return img.set('m', img.select('LST').reduceRegion({reducer: ee.Reducer.mean(), geometry: aoi, scale: SC.scene_mean, maxPixels: 1e9}).get('LST')); })
  .filter(ee.Filter.notNull(['m']))
  .map(function (img) { return img.addBands(img.select('LST').subtract(ee.Number(img.get('m'))).rename('LSTa').toFloat()); });
var lsComp = ls.select(['NDVI', 'LSTa']).median();
var proj30 = ee.Projection('EPSG:32652').atScale(SC.landsat);
var built = wc.eq(WC.built).reduceResolution({reducer: ee.Reducer.mean(), maxPixels: 1024}).reproject(proj30).rename('built');
var elev = ee.Image('USGS/SRTMGL1_003').rename('elev');
function regress(xs) {
  var img = ee.Image.constant(1).rename('const');
  xs.forEach(function (x) { img = img.addBands(x); });
  img = img.addBands(lsComp.select('LSTa')).updateMask(notWater);
  var r = img.reduceRegion({reducer: ee.Reducer.linearRegression({numX: xs.length + 1, numY: 1}), geometry: aoi, scale: SC.landsat, maxPixels: 1e10, tileScale: 8});
  return ee.Array(r.get('coefficients')).project([0]).get([1]);
}
var bSimple = regress([lsComp.select('NDVI')]);
var bControlled = regress([lsComp.select('NDVI'), built, elev]);

// ---------- Sentinel-2: 여름 NDVI (10m) ----------
var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(aoi)
  .filterDate(CFG.sentinel2.start, CFG.sentinel2.end).filter(ee.Filter.calendarRange(M[0], M[1], 'month'))
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', CFG.sentinel2.max_cloud))
  .map(function (img) {
    var scl = img.select('SCL'); var ok = ee.Image(1);
    CFG.sentinel2.scl_bad.forEach(function (c) { ok = ok.and(scl.neq(c)); });
    return img.normalizedDifference(['B8', 'B4']).rename('NDVI').toFloat().updateMask(ok);
  });
var s2n = s2.median();
function cityMedian(cls) {
  return s2n.updateMask(wc.eq(cls)).reduceRegion({reducer: ee.Reducer.median(), geometry: aoi, scale: SC.s2_city, maxPixels: 1e10, tileScale: 4}).get('NDVI');
}

// ---------- GHSL: 인구·건물부피 ----------
var yr = CFG.ghsl_year;
var pop = ee.ImageCollection('JRC/GHSL/P2023A/GHS_POP').filterDate(yr + '-01-01', (Number(yr) + 1) + '-01-01').first().select('population_count');
var vol = ee.ImageCollection('JRC/GHSL/P2023A/GHS_BUILT_V').filterDate(yr + '-01-01', (Number(yr) + 1) + '-01-01').first().select('built_volume_total');
var ghsl = pop.rename('pop').addBands(vol.rename('vol'));

// ---------- 공원별 ----------
var fc = ee.FeatureCollection(PARKS.map(function (p) { return ee.Feature(ee.Geometry.MultiPolygon(p.g), {id: p.id}); }));
var rows = fc.map(function (f) {
  var g = f.geometry();
  var n = s2n.reduceRegion({reducer: ee.Reducer.mean(), geometry: g, scale: SC.s2, maxPixels: 1e9}).get('NDVI');
  var t = lsComp.select('LSTa').reduceRegion({reducer: ee.Reducer.mean(), geometry: g, scale: SC.landsat, maxPixels: 1e9}).get('LSTa');
  var props = {ndvi_s2: n, lsta: t, area_poly: g.area(1)};
  CFG.rings_m.forEach(function (d) {
    var ring = g.buffer(d, 1).difference(g, 1);
    var s = ghsl.reduceRegion({reducer: ee.Reducer.sum(), geometry: ring, scale: SC.ghsl, maxPixels: 1e9});
    props['pop_' + d] = s.get('pop'); props['vol_' + d] = s.get('vol');
  });
  return f.set(props);
});
var table = rows.map(function (f) { return ee.Feature(null, f.toDictionary()); });   // 경계는 빼고 값만
var city = ee.Dictionary({b_simple: bSimple, b_controlled: bControlled, ndvi_grass: cityMedian(WC.grass), ndvi_tree: cityMedian(WC.tree),
  ls_scenes: ls.size(), s2_scenes: s2.size()});
ee.Dictionary({city: city, table: table}).evaluate(function (r, err) {
  if (err) { print('ERROR| ' + err); return; }
  print('CITY|' + JSON.stringify(r.city));
  r.table.features.forEach(function (ft) { print('PARK|' + JSON.stringify(ft.properties)); });
  print('DONE|' + r.table.features.length);
});
