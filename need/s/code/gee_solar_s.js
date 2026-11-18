// 청주 장기미집행 공원 40개소 — S 회복력(에너지 자립) 입력값 (V-World 좌표, 2026-11-16)
// 출력: site_id, ghi(kWh/㎡/yr), slope(°), aspect(°), hs_winter(0~1 겨울 정오 지형 일조), shadow_frac(지형 그늘 비율),
//       bh300(주변 300m 평균 건물높이 m), tree_frac(공원 내 수목 비율), pop2000(2km 인구), pop300
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
function circ(r){ return ee.Geometry.Point([r[2], r[3]]).buffer(Math.max(30, Math.sqrt(r[4]/Math.PI))); }
var parks = ee.FeatureCollection(P.map(function(r){ return ee.Feature(circ(r), {site_id: r[0], name: r[1], lon: r[2], lat: r[3]}); }));
var box = ee.Geometry.Rectangle([127.25, 36.42, 127.70, 36.80]);

// 일사: ERA5-Land 월합 하향 단파복사 (J/㎡) → 2024년 합 → kWh/㎡/yr
var era = ee.ImageCollection('ECMWF/ERA5_LAND/MONTHLY_AGGR').filterDate('2024-01-01','2025-01-01')
  .select('surface_solar_radiation_downwards_sum').sum().divide(3.6e6).rename('ghi');
// 지형: SRTM 30m
var dem = ee.Image('USGS/SRTMGL1_003').clip(box);
var slope = ee.Terrain.slope(dem).rename('slope');
var aspect = ee.Terrain.aspect(dem).rename('aspect');
var hs = ee.Terrain.hillshade(dem, 180, 30).divide(255).rename('hs_winter');          // 동지 정오 태양고도 ≈ 30°
var shadow = ee.Terrain.hillShadow(dem, 180, 30, 150, false).not().rename('shadow');  // 1 = 지형 그늘
// 건물 높이: GHSL 2018 (100m)
var bh = ee.Image('JRC/GHSL/P2023A/GHS_BUILT_H/2018').select('built_height').rename('bh');
// 수목: ESA WorldCover 2021 (10m) class 10
var tree = ee.Image('ESA/WorldCover/v200/2021').select('Map').eq(10).rename('tree');
var pop = ee.Image('JRC/GHSL/P2023A/GHS_POP/2020').select('population_count');

var out = parks.map(function(f){
  var g = f.geometry(); var pt = ee.Geometry.Point([f.get('lon'), f.get('lat')]);
  var t = ee.Image.cat([slope, aspect, hs, shadow, tree]).reduceRegion({reducer: ee.Reducer.mean(), geometry: g, scale: 10, maxPixels: 1e8});
  var ghi = era.reduceRegion({reducer: ee.Reducer.mean(), geometry: pt.buffer(5000), scale: 1000, maxPixels: 1e8}).get('ghi');
  var b = bh.reduceRegion({reducer: ee.Reducer.mean(), geometry: pt.buffer(300), scale: 100, maxPixels: 1e8}).get('bh');
  var p2 = pop.reduceRegion({reducer: ee.Reducer.sum(), geometry: pt.buffer(2000), scale: 100, maxPixels: 1e8}).get('population_count');
  var p3 = pop.reduceRegion({reducer: ee.Reducer.sum(), geometry: pt.buffer(300), scale: 100, maxPixels: 1e8}).get('population_count');
  return ee.Feature(null, {site_id: f.get('site_id'), ghi: ghi, slope: t.get('slope'), aspect: t.get('aspect'),
    hs_winter: t.get('hs_winter'), shadow_frac: t.get('shadow'), bh300: b, tree_frac: t.get('tree'), pop2000: p2, pop300: p3});
});
out.evaluate(function(fc){
  var rows = fc.features.map(function(f){ var p=f.properties; return [p.site_id, p.ghi, p.slope, p.aspect, p.hs_winter, p.shadow_frac, p.bh300, p.tree_frac, p.pop2000, p.pop300]; });
  print('SOLAR_JSON ' + JSON.stringify(rows));
});
