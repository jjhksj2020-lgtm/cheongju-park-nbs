// 청주 장기미집행 공원 40개소 — 열환경 값 재산출 (V-World 좌표, 2026-11-16)
// 출력: site_id, lsta(청주 평균 대비 ℃), ndvi, pop300(명), vol300(㎥)  — 모두 300m 버퍼
var P = [
  [1, '근린공원165', 127.524994, 36.625398, 105864],
  [2, '근린공원151', 127.606874, 36.717545, 31334],
  [3, '근린공원8', 127.489879, 36.636583, 41315],
  [4, '어린이공원144', 127.472398, 36.629710, 2031],
  [5, '어린이공원152', 127.381294, 36.729772, 2758],
  [6, '어린이공원194', 127.454528, 36.743425, 1511],
  [7, '어린이공원218', 127.538424, 36.719997, 1500],
  [8, '어린이공원219', 127.447092, 36.741424, 1525],
  [9, '어린이공원220', 127.603316, 36.717423, 2796],
  [10, '어린이공원221', 127.605555, 36.722358, 3297],
  [11, '어린이공원223', 127.513353, 36.590405, 1551],
  [12, '소공원23', 127.412476, 36.493197, 1869],
  [13, '소공원52', 127.413000, 36.460176, 1320],
  [14, '소공원53', 127.411976, 36.458188, 820],
  [15, '소공원54', 127.438262, 36.458517, 883],
  [16, '소공원55', 127.448167, 36.459655, 1223],
  [17, '소공원169', 127.474076, 36.630903, 3274],
  [18, '소공원68', 127.307642, 36.605904, 1213],
  [19, '소공원73', 127.540758, 36.739316, 1530],
  [20, '소공원76', 127.437693, 36.636305, 496],
  [21, '소공원77', 127.449581, 36.637716, 247],
  [22, '소공원78', 127.499324, 36.681110, 2244],
  [23, '소공원79', 127.527851, 36.605606, 554],
  [24, '소공원80', 127.392421, 36.620544, 8177],
  [25, '소공원37', 127.486786, 36.700651, 1509],
  [26, '소공원38', 127.486786, 36.700651, 1119],
  [27, '소공원39', 127.501170, 36.679925, 2090],
  [28, '소공원40', 127.391122, 36.602685, 2174],
  [29, '소공원41', 127.391783, 36.603204, 858],
  [30, '소공원42', 127.394125, 36.601638, 606],
  [31, '소공원155', 127.599087, 36.720397, 3242],
  [32, '소공원156', 127.597658, 36.717946, 9629],
  [33, '소공원162', 127.566386, 36.664612, 586],
  [34, '소공원163', 127.523439, 36.551783, 522],
  [35, '소공원164', 127.444166, 36.737609, 369],
  [36, '소공원165', 127.423458, 36.692242, 705],
  [37, '역사공원167', 127.407487, 36.633779, 75336],
  [38, '역사공원199', 127.472215, 36.628002, 5215],
  [39, '문화공원4', 127.601385, 36.706181, 24789],
  [40, '생태공원3', 127.450220, 36.677464, 2579169]
];
var pts = ee.FeatureCollection(P.map(function(r){
  return ee.Feature(ee.Geometry.Point([r[2], r[3]]).buffer(300), {site_id: r[0], name: r[1]});
}));
var box = ee.Geometry.Rectangle([127.25, 36.42, 127.70, 36.80]);   // 청주 대략 범위 (가정)

function maskL(img){
  var qa = img.select('QA_PIXEL');
  var m = qa.bitwiseAnd(1<<3).eq(0).and(qa.bitwiseAnd(1<<4).eq(0)).and(qa.bitwiseAnd(1<<1).eq(0));
  return img.select('ST_B10').multiply(0.00341802).add(149).subtract(273.15).rename('lst').updateMask(m);
}
var L = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2').merge(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2'))
  .filterBounds(box).filter(ee.Filter.calendarRange(2024, 2025, 'year')).filter(ee.Filter.calendarRange(6, 9, 'month'))
  .filter(ee.Filter.lt('CLOUD_COVER', 40)).map(maskL);
var lst = L.median().clip(box);
var S = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(box)
  .filter(ee.Filter.calendarRange(2024, 2025, 'year')).filter(ee.Filter.calendarRange(6, 9, 'month'))
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
  .map(function(i){ var scl=i.select('SCL'); var m=scl.neq(3).and(scl.neq(8)).and(scl.neq(9)).and(scl.neq(10));
    return i.normalizedDifference(['B8','B4']).rename('ndvi').updateMask(m); });
var ndvi = S.median().clip(box);
var pop = ee.Image('JRC/GHSL/P2023A/GHS_POP/2020').select('population_count');
var vol = ee.Image('JRC/GHSL/P2023A/GHS_BUILT_V/2020').select('built_volume_total');

var cityMean = ee.Number(lst.reduceRegion({reducer: ee.Reducer.mean(), geometry: box, scale: 90, maxPixels: 1e9}).get('lst'));
var out = pts.map(function(f){
  var g = f.geometry();
  var a = lst.reduceRegion({reducer: ee.Reducer.mean(), geometry: g, scale: 30, maxPixels: 1e8}).get('lst');
  var n = ndvi.reduceRegion({reducer: ee.Reducer.mean(), geometry: g, scale: 10, maxPixels: 1e8}).get('ndvi');
  var p = pop.reduceRegion({reducer: ee.Reducer.sum(), geometry: g, scale: 100, maxPixels: 1e8}).get('population_count');
  var v = vol.reduceRegion({reducer: ee.Reducer.sum(), geometry: g, scale: 100, maxPixels: 1e8}).get('built_volume_total');
  return ee.Feature(null, {site_id: f.get('site_id'), name: f.get('name'),
    lsta: ee.Number(a).subtract(cityMean), ndvi: n, pop300: p, vol300: v});
});
print('n_landsat', L.size(), 'n_s2', S.size(), 'city_mean_lst', cityMean);
out.evaluate(function(fc){
  var rows = fc.features.map(function(f){ var p=f.properties; return [p.site_id, p.lsta, p.ndvi, p.pop300, p.vol300]; });
  print('RESULT_JSON ' + JSON.stringify(rows));
});
