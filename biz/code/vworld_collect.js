/* ============================================================================
 * 청주 장기미집행 공원 — V-World 토지 자료 수집기 (브라우저 콘솔용)
 *
 * 실행 방법은 biz/README.md 참고. 요약:
 *   1) 크롬/엣지 주소창에 https://api.vworld.kr/req/search 를 연다 (오류 글자가 떠도 정상. 이 주소 안에서만 V-World가 응답한다)
 *   2) F12 → Console 탭에 이 파일 전체를 붙여 넣고 Enter
 *   3) 아래 KEY 줄에 인증키를 넣고 실행:  await collectAll()
 *      → 다운로드 폴더에 6개 파일이 생긴다. 저장소의 같은 이름 파일에 덮어쓰면 끝.
 *   (선택) await collectBasemap()  → 위성사진·일반지도 (cheongju_basemap_vworld.json)
 *   (선택) await collectDem()      → 지형 표고 (cheongju_dem.json)
 *
 * 하는 일 (2026-11-13 수집과 같은 방법):
 *   공원 경계(biz/data/vworld/parks.txt, V-World 도시계획시설 lt_c_uq162에서 매칭해 둔 것)
 *   ∩ 연속지적도(lp_pa_cbnd_bubun) 필지 → 공원 안 격자 표본점으로 필지별 공원 안 면적 배분
 *   → 필지별 소유구분(getPossessionAttr, 없으면 ladfrlList 토지임야목록)
 *   → 필지별 토지특성(getLandCharacteristics: 개별공시지가·용도지역·이용상황, 기준연도 YEAR)
 *   → 공원별 집계 (국공유 비율, 사유지 공시지가 면적가중, 지목 '대' 사유지, 건물·시가지 사유지, 개발제한구역)
 * ========================================================================== */

const KEY  = window.VWORLD_KEY || '여기에_인증키';   // biz/README.md 의 키
const YEAR = '2026';                                   // 토지특성(공시지가) 기준연도
// 아래 세 값은 biz/code/make_collector.py 가 저장소 파일에서 채운다 (저장소가 비공개여도 이 파일만 있으면 실행됨)
const PARKS_TXT = `1~12752203,3662537,106,104,21,1,15,6,12,2,13,-1,12,0,18,-4,13,0,11,2,9,5,14,5,12,13,8,7,11,3,28,1,70,-11,24,-24,6,-5,16,-9,18,-7,27,-7,22,-6,14,-3,98,-20,18,-10,3,-7,-4,-9,-6,-11,-23,-28,-38,-3,-25,-39,-38,-56,-73,10,-11,-8,-71,-32,-90,-3,-19,28,-58,34,-45,28,-18,19,-39,7,-32,5,-9,11,-19,11,-1,1
2~12760541,3672072,11,26,23,2,31,2,-1,22,32,67,17,28,28,-21,20,-22,16,-23,13,-26,3,-8,2,-9,5,-27,-1,-27,-1,-7,-3,-23,-31,12,-59,-8,-17,10,-4,5,-7,2,-12,3,-1,-1,-2,0,-6,-9,-54,27,-2,5
3~12748642,3663268,3,35,40,2,28,1,37,1,9,1,40,3,1,46,-2,1,-43,-1,1,124,8,0,19,1,-2,17,44,2,20,1,1,-10,1,-1,33,0,3,-25,4,0,4,0,2,-19,-12,-13,0,-21,1,0,1,-14,8,0,5,0,16,0,2,-38,-3,1,-101,-3,-2,-2,-2,-51,21,1,2,1,0,2,5,-1,3,-19,26,1,8,0,1,-12,2,0,10,0,-1,-8,12,-3,-5,-1,1,-11,-17,-2,0,-8,1,-7,-5,-4,-8,-8,1,-19,-199,-9,-10,11,-3,8,-3,8,-5,28,0,4,-1,10
4~12747137,3662877,-4,14,-22,61,3,8,48,-11,-25,-72
6~12745426,3674361,5,2,54,-17,3,-3,-5,-12,-2,-8,-10,3,-53,16,8,19
7~12753850,3671966,1,5,17,11,6,4,35,-35,-23,-15,-6,0,-30,30
8~12744628,3674158,4,4,50,-1,4,-3,0,-23,-59,0,1,23
9~12760306,3671796,18,8,6,-1,40,-50,-2,-4,-26,-14,-6,3,-12,9,-12,9,-3,9,-1,5,-1,11,-1,15
10~12760455,3672231,2,3,22,42,13,3,44,-14,2,-4,-26,-47,-57,17
11~12751239,3658969,7,1,1,0,7,2,12,11,2,1,31,17,0,-25,-2,-4,-21,-13,-6,-3,-6,-3,-6,-2,-7,-1,-7,-1,-5,0,0,13,0,7
12~12741252,3649282,11,45,9,-3,43,-13,-7,-16,-16,-5,-23,-13,-4,-1,-10,2,-3,4
13~12741242,3646010,6,12,15,-6,14,-1,2,0,4,1,8,4,8,3,6,1,12,-3,2,-4,-3,-4,-5,-6,-6,-10,-5,0,-9,1,-14,-2,-7,0,-4,1,-2,2,-8,7,-6,3,-8,1
14~12741212,3645806,3,2,32,-6,0,-5,1,-10,-2,-9,-11,2,-8,1,-11,0,-4,25
15~12744145,3645960,31,5,4,1,6,-28,-17,1,-18,-2,-6,23
16~12744652,3645941,4,3,-1,4,1,2,9,6,0,0,8,8,2,-11,7,-18,10,-20,8,-13,-7,-2,-4,1,-8,5,-6,1,-7,9,-16,25
17~12747371,3663025,20,58,14,-3,40,-9,0,0,-4,-6,-16,-50,-4,-1,-50,11
18~12730722,3660559,46,16,1,0,1,-4,-3,-10,2,-1,-2,0,-2,-2,-5,-6,-4,-13,0,-4,2,-3,-18,-6,-18,33
19~12754054,3673912,3,34,41,0,-5,-37,-4,-3,-23,2,-8,1,-4,3
20~12743747,3663615,30,33,0,-14,0,-1,0,-15,-2,-2,-2,-1,-21,0,-5,0
21~12744948,3663767,0,1,1,2,8,6,18,-6,-4,-6,-23,-1,0,3,0,1
22~12749897,3668117,4,5,34,6,34,5,0,-10,-1,-6,-3,-10,-10,-14,-1,-4,-7,0,-17,-1,-5,1,-7,4,-18,13,-3,11
23~12752751,3660585,9,3,5,-7,29,5,4,-12,-26,-4,-11,-4,-10,19
24~12739119,3662027,31,42,13,8,21,10,13,2,7,3,1,1,34,-9,4,-2,2,-2,1,-4,1,-3,-1,-3,-4,-6,-4,-7,-1,-4,-1,-5,1,-10,-1,-8,-1,-2,-23,-15,-31,-16,-12,-2,-20,2,-4,0,-20,12,5,13,-11,5
25~12748608,3670077,47,24,3,0,20,-3,8,13,10,-3,1,-8,5,-17,-14,-5,-13,-1,-46,5,-11,-1,-10,-4
26~12748647,3670064,3,2,-2,7,26,-3,12,0,4,-7,1,-1,2,0,3,-1,2,-1,3,-4,4,-8,2,-4,3,-8,-11,-3,-7,2,-3,2,-11,10,-23,16,-7,1,-1,0
27~12750083,3667958,19,41,3,15,8,-4,10,-12,7,-10,4,-9,1,-3,0,-2,0,-1,-18,-18,-11,-17,-21,14,-2,6
28~12739127,3660249,20,14,7,10,2,6,0,2,18,0,0,-4,-2,-8,-2,-5,-3,-4,-1,-4,0,-7,3,-6,7,-7,15,-17,-6,-8,-1,-5,2,-16,-3,0,-2,0,-5,3,-4,5,-4,11,-13,10,-9,17,-3,5,-16,8
29~12739138,3660061,12,4,32,22,5,-2,-6,-22,-1,-20,-4,1,-6,4,-18,10,-14,3
30~12739361,3660157,33,0,-1,-19,-31,0,-1,19
31~12759924,3672006,33,52,5,1,4,-1,11,-6,8,-6,6,-6,10,-15,-26,-41,-51,22
32~12759824,3671744,76,98,70,-27,2,-4,-78,-99,-5,-1,-65,33
33~12756589,3666452,36,10,4,-22,-21,-1,-4,1,-15,12
34~12752316,3655186,11,12,0,1,22,-10,-15,-19,-17,13,-1,3
35~12744398,3673751,13,17,14,-4,-6,-10,5,-3,-5,-5,-2,-3,-19,8
36~12742303,3669184,14,29,19,-5,-7,-27,-3,-1,-21,2,-2,2
37~12740256,3663335,20,10,22,48,14,13,9,-12,5,-6,134,-93,161,-18,17,40,0,0,-19,7,-17,59,8,56,-50,116,0,0,127,-65,40,-26,46,-5,128,-86,0,0,-79,-28,-118,-82,-41,-24,-94,-10,-71,0,-5,14,-9,18,-9,13,-14,7,-24,1,-12,-8,0,-7,13,-7,-1,-16,-15,-16,-68,0,-44,-19,-4,11,-24,72,-23,41,-3,2,0,0
38~12747186,3662788,80,16,29,-26,5,-10,3,-6,-52,-18,-9,0,-1,0,-29,-9,-7,3,-10,32,-9,18
39~12760148,3670641,22,13,23,12,-19,79,65,10,14,11,5,6,31,-10,8,-7,2,-1,-2,-16,0,-7,1,-1,-2,0,0,-3,2,-11,3,-5,0,-9,1,-9,-4,-7,-1,-3,-10,-4,-5,-5,-7,-3,-4,-4,-5,-5,-6,-1,4,-6,0,-5,7,-21,1,-9,0,-8,4,-5,0,-1,-2,1,-1,-17,7,-6,5,-6,0,-8,-3,-8,-3,-6,-13,-9,-7,8,3,3,-10,12,-5,-5,-7,5,-35,-12,-5,3,-17,9,-35,71
40~12742513,3667903,28,448,146,11,1752,273,73,17,76,41,62,51,30,49,136,382,17,27,227,162,645,398,78,60,88,89,61,93,80,145,71,166,131,-7,134,4,284,39,-79,-291,-83,-182,-38,-64,-132,-176,-123,-118,-160,-125,-523,-336,-68,-55,-85,-91,-67,-94,-71,-173,-82,-129,-129,-121,-160,-94,-103,-97,-19,-36,-2,-26,-1,-14,20,-48,187,-214,97,-85,100,-62,105,-44,322,-86,-258,-155,-189,55,-176,78,-98,57,-337,294,-135,143,-50,33,-73,23,-140,8,-91,-4,-949,-161,-529,-58`;            // biz/data/vworld/parks.txt
const AREA = {"1": 105864.0, "2": 31334.0, "3": 41315.0, "4": 2031.0, "5": 2758.0, "6": 1511.0, "7": 1500.0, "8": 1525.0, "9": 2796.0, "10": 3297.0, "11": 1551.0, "12": 1869.0, "13": 1320.0, "14": 820.0, "15": 883.0, "16": 1223.0, "17": 3274.0, "18": 1213.0, "19": 1530.0, "20": 496.0, "21": 247.0, "22": 2244.0, "23": 554.0, "24": 8177.0, "25": 1509.0, "26": 1119.0, "27": 2090.0, "28": 2174.0, "29": 858.0, "30": 606.0, "31": 3242.0, "32": 9629.0, "33": 586.0, "34": 522.0, "35": 369.0, "36": 705.0, "37": 75336.0, "38": 5215.0, "39": 24789.0, "40": 2579169.0};                    // biz/data/input/sites.csv 공고 면적
const IMG_BOUNDS = {"s1": {"bounds": [127.5194478, 36.6213488, 127.5307989, 36.629391]}, "s2": {"bounds": [127.6043129, 36.7191583, 127.6085186, 36.7232862]}, "s3": {"bounds": [127.4849546, 36.6305275, 127.490598, 36.6364853]}, "s4": {"bounds": [127.470417, 36.6280823, 127.4723107, 36.6302864]}, "s6": {"bounds": [127.4535352, 36.7425832, 127.45552, 36.7442704]}, "s7": {"bounds": [127.537896, 36.7187498, 127.5396985, 36.7204677]}, "s8": {"bounds": [127.4456683, 36.7407434, 127.4474627, 36.7422221]}, "s9": {"bounds": [127.6024139, 36.716703, 127.6043397, 36.7186896]}, "s10": {"bounds": [127.6038569, 36.7214416, 127.6060778, 36.723484]}, "s11": {"bounds": [127.5117767, 36.5888724, 127.513606, 36.5906276]}, "s12": {"bounds": [127.4118912, 36.4921417, 127.4137741, 36.4938904]}, "s13": {"bounds": [127.4117544, 36.4592873, 127.4138573, 36.4609052]}, "s14": {"bounds": [127.4115962, 36.457253, 127.4130043, 36.4586056]}, "s15": {"bounds": [127.4409074, 36.4588278, 127.4424067, 36.4602041]}, "s16": {"bounds": [127.445899, 36.4583748, 127.4476236, 36.4602602]}, "s17": {"bounds": [127.473051, 36.6294814, 127.4751055, 36.6314918]}, "s18": {"bounds": [127.3066494, 36.6046849, 127.3082694, 36.6063256]}, "s19": {"bounds": [127.5399855, 36.7385058, 127.5415331, 36.7400169]}, "s20": {"bounds": [127.4369511, 36.6356309, 127.4382922, 36.6369976]}, "s21": {"bounds": [127.4489835, 36.6371353, 127.4502522, 36.6382588]}, "s22": {"bounds": [127.49832, 36.6802293, 127.5003478, 36.6819802]}, "s23": {"bounds": [127.5269499, 36.605094, 127.5285405, 36.6064462]}, "s24": {"bounds": [127.390337, 36.619097, 127.3933196, 36.6217751]}, "s25": {"bounds": [127.4853516, 36.7000403, 127.4877441, 36.7018425]}, "s26": {"bounds": [127.4858424, 36.6997113, 127.48772, 36.7013479]}, "s27": {"bounds": [127.5001574, 36.6787063, 127.5020242, 36.6808101]}, "s28": {"bounds": [127.3905516, 36.6011794, 127.3926276, 36.6035308]}, "s29": {"bounds": [127.3908091, 36.5998551, 127.3924425, 36.6014378]}, "s30": {"bounds": [127.3930997, 36.6008629, 127.3944515, 36.6020838]}, "s31": {"bounds": [127.598573, 36.7191755, 127.6006812, 36.7212653]}, "s32": {"bounds": [127.5973177, 36.716187, 127.6006436, 36.7193432]}, "s33": {"bounds": [127.5653484, 36.6638449, 127.5668317, 36.6651616]}, "s34": {"bounds": [127.5226477, 36.5511789, 127.5240129, 36.5525062]}, "s35": {"bounds": [127.4434876, 36.7369389, 127.4447456, 36.7381791]}, "s36": {"bounds": [127.4225155, 36.6912764, 127.4238753, 36.6926551]}, "s37": {"bounds": [127.3998857, 36.6294254, 127.4116874, 36.6382072]}, "s38": {"bounds": [127.4710554, 36.6265367, 127.4738449, 36.6288572]}, "s39": {"bounds": [127.6002896, 36.7042789, 127.6042163, 36.7089151]}, "s40": {"bounds": [127.4102497, 36.6594685, 127.4811459, 36.7183843]}, "cityBase": {"bounds": [127.2498322, 36.4298461, 127.7500534, 36.8200041]}, "citySat": {"bounds": [127.2498322, 36.4298461, 127.7500534, 36.8200041]}};               // biz/data/map/img/manifest.json 경계 (지형을 위성사진과 같은 범위로)

// ---------- V-World 호출 ----------
async function q(path, params) {
  const u = new URL(path, location.origin);
  Object.entries({ ...params, key: KEY, domain: 'localhost' }).forEach(([k, v]) => u.searchParams.set(k, v));
  for (let i = 0; i < 3; i++) {
    try { return await fetch(u).then(r => r.json()); } catch (e) { await new Promise(r => setTimeout(r, 1000)); }
  }
  return null;
}
async function feats(layer, box, maxPage = 20) {
  let out = [], p = 1;
  while (p <= maxPage) {
    const j = await q('/req/data', { service: 'data', request: 'GetFeature', data: layer, geomFilter: box, size: 1000, page: p,
      format: 'json', crs: 'EPSG:4326', geometry: 'true', attribute: 'true' });
    if (!j || j.response.status !== 'OK') break;
    const fs = j.response.result.featureCollection.features; out = out.concat(fs);
    if (fs.length < 1000 || out.length >= +j.response.record.total) break; p++;
  }
  return out;
}
// 연속지적 조회는 10㎢ 미만 상자만 허용 → 0.025° 격자로 나눈다
const tilesOf = b => { const o = [], st = 0.025; for (let x = b[0]; x < b[2]; x += st) for (let y = b[1]; y < b[3]; y += st)
  o.push(`BOX(${x},${y},${Math.min(x + st, b[2])},${Math.min(y + st, b[3])})`); return o; };

// ---------- 기하 ----------
const rings = g => g.type === 'Polygon' ? [g.coordinates] : g.type === 'MultiPolygon' ? g.coordinates : [];
const inRing = (pt, r) => { let c = false; for (let i = 0, j = r.length - 1; i < r.length; j = i++) { const [xi, yi] = r[i], [xj, yj] = r[j];
  if (((yi > pt[1]) !== (yj > pt[1])) && (pt[0] < (xj - xi) * (pt[1] - yi) / (yj - yi) + xi)) c = !c; } return c; };
const inGeom = (pt, g) => rings(g).some(poly => inRing(pt, poly[0]) && !poly.slice(1).some(h => inRing(pt, h)));
const bbOf = g => { let a = [1e9, 1e9, -1e9, -1e9]; const w = c => { if (typeof c[0] === 'number') { a[0] = Math.min(a[0], c[0]); a[1] = Math.min(a[1], c[1]);
  a[2] = Math.max(a[2], c[0]); a[3] = Math.max(a[3], c[1]); } else c.forEach(w); }; w(g.coordinates); return a; };
const areaM2 = g => { let s = 0; rings(g).forEach(poly => poly.forEach((r, k) => { let a = 0; const cy = r[0][1];
  for (let i = 0, j = r.length - 1; i < r.length; j = i++) a += (r[j][0] * r[i][1] - r[i][0] * r[j][1]);
  a = Math.abs(a) / 2 * 111320 * 111320 * Math.cos(cy * Math.PI / 180); s += k ? -a : a; })); return s; };
const dp = (pts, eps) => { if (pts.length < 4) return pts; let dm = 0, idx = 0; const [a, b] = [pts[0], pts[pts.length - 1]];
  for (let i = 1; i < pts.length - 1; i++) { const p = pts[i], dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1e-12;
    const d = Math.abs(dy * p[0] - dx * p[1] + b[0] * a[1] - b[1] * a[0]) / L; if (d > dm) { dm = d; idx = i; } }
  return dm > eps ? dp(pts.slice(0, idx + 1), eps).slice(0, -1).concat(dp(pts.slice(idx), eps)) : [a, b]; };
const dpr = (r, eps) => { if (eps <= 0 || r.length < 8) return r; const m = Math.floor(r.length / 2); return dp(r.slice(0, m + 1), eps).slice(0, -1).concat(dp(r.slice(m), eps)); };
// 압축 좌표: 정수(경위도×1e5) 누적차분, 링 '|', 다각형 ';'  (biz/code/build_mapdata.py가 읽는 형식)
const enc = (g, eps) => rings(g).map(poly => poly.map(r => { const s = dpr(r, eps); if (s.length < 4) return null; let px = 0, py = 0; const a = [];
  for (const p of s) { const x = Math.round(p[0] * 1e5), y = Math.round(p[1] * 1e5); a.push(x - px, y - py); px = x; py = y; } return a.join(','); })
  .filter(Boolean).join('|')).filter(Boolean).join(';');
const dec = s => ({ type: 'MultiPolygon', coordinates: s.split(';').map(p => p.split('|').map(r => { const v = r.split(',').map(Number); let x = 0, y = 0; const ring = [];
  for (let i = 0; i < v.length; i += 2) { x += v[i]; y += v[i + 1]; ring.push([x / 1e5, y / 1e5]); } if (ring[0][0] !== ring.at(-1)[0] || ring[0][1] !== ring.at(-1)[1]) ring.push(ring[0]); return ring; })) });
const clip = (ring, b) => { let pts = ring.slice(0, -1); const E = [[p => p[0] >= b[0], (a, c) => [b[0], a[1] + (b[0] - a[0]) / (c[0] - a[0]) * (c[1] - a[1])]],
  [p => p[0] <= b[2], (a, c) => [b[2], a[1] + (b[2] - a[0]) / (c[0] - a[0]) * (c[1] - a[1])]], [p => p[1] >= b[1], (a, c) => [a[0] + (b[1] - a[1]) / (c[1] - a[1]) * (c[0] - a[0]), b[1]]],
  [p => p[1] <= b[3], (a, c) => [a[0] + (b[3] - a[1]) / (c[1] - a[1]) * (c[0] - a[0]), b[3]]]];
  for (const [ins, X] of E) { const o = []; for (let i = 0; i < pts.length; i++) { const c = pts[i], p = pts[(i + pts.length - 1) % pts.length];
    if (ins(c)) { if (!ins(p)) o.push(X(p, c)); o.push(c); } else if (ins(p)) o.push(X(p, c)); } pts = o; if (!pts.length) break; }
  return pts.length >= 3 ? pts.concat([pts[0]]) : null; };
const clipG = (g, b) => ({ type: 'MultiPolygon', coordinates: rings(g).map(poly => poly.map(r => clip(r, b)).filter(Boolean)).filter(p => p.length) });

// ---------- 분류 (land_own / land_price 집계 규칙) ----------
const isPub = o => o && o.split('|').every(x => /국유지|도유지|군유지|시유지/.test(x));   // 국유·시도유·군유(청주시) = 국공유
const URB = new Set(['단독', '연립', '다세대', '아파트', '주거기타', '주거나지', '주상기타', '주상나지', '상업용', '업무용', '공업용']);  // 건물·시가지 이용상황

function download(name, text) {
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([text], { type: 'text/plain;charset=utf-8' }));
  a.download = name; document.body.appendChild(a); a.click(); a.remove();
}
const csv = rows => rows.map(r => r.map(v => (v == null ? '' : /[,"\n]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : v)).join(',')).join('\n') + '\n';

// ---------- 한 공원 ----------
async function doPark(id, geom, log) {
  const A = areaM2(geom), bb = bbOf(geom), pad = 0.0003;
  let ps = []; for (const t of tilesOf([bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad])) ps = ps.concat(await feats('lp_pa_cbnd_bubun', t));
  const seen = {}; ps = ps.filter(f => !seen[f.properties.pnu] && (seen[f.properties.pnu] = 1)); ps.forEach(f => f._bb = bbOf(f.geometry));
  // 격자 표본점 (공원 면적이 클수록 많이)
  const N = A > 200000 ? 2500 : A > 20000 ? 800 : 300, st = Math.max(2, Math.sqrt(A / N));
  const dx = st / (111320 * Math.cos(bb[1] * Math.PI / 180)), dy = st / 111320; const cnt = {}; let tot = 0;
  for (let x = bb[0] + dx / 2; x < bb[2]; x += dx) for (let y = bb[1] + dy / 2; y < bb[3]; y += dy) {
    if (!inGeom([x, y], geom)) continue; tot++;
    const f = ps.find(f => x >= f._bb[0] && x <= f._bb[2] && y >= f._bb[1] && y <= f._bb[3] && inGeom([x, y], f.geometry));
    if (f) cnt[f.properties.pnu] = (cnt[f.properties.pnu] || 0) + 1;
  }
  const rows = [];
  for (const [pnu, c] of Object.entries(cnt)) {
    const f = ps.find(f => f.properties.pnu === pnu);
    let fl = (await q('/ned/data/getPossessionAttr', { pnu, format: 'json', numOfRows: 10, pageNo: 1 }))?.possessions?.field || [];
    let src = 'getPossessionAttr';
    if (!fl.length) { fl = (await q('/ned/data/ladfrlList', { pnu, format: 'json', numOfRows: 10, pageNo: 1 }))?.ladfrlVOList?.ladfrlVOList || []; src = 'ladfrlList'; }
    const lc = (await q('/ned/data/getLandCharacteristics', { pnu, stdrYear: YEAR, format: 'json', numOfRows: 5, pageNo: 1 }))?.landCharacteristicss?.field?.[0] || {};
    rows.push({ pnu, in: Math.round(A * c / tot), jibun: f.properties.jibun, geom: f.geometry,
      own: [...new Set(fl.map(x => x.posesnSeCodeNm))].join('|').replace('시 도유지', '시도유지') || '미확인', src,
      jimok: fl[0]?.lndcgrCodeNm || f.properties.jibun.replace(/[\d\-산 ]/g, ''), jiga: f.properties.jiga || '',
      p: +lc.pblntfPclnd || null, zone: lc.prposArea1Nm || '', gb: lc.prposArea2Nm === '개발제한구역' ? 1 : 0, use: lc.ladUseSittnNm || '' });
  }
  log(`공원 ${id}: 필지 ${rows.length}개, 표본 ${tot}점`);
  return { id, A, bb, rows };
}

// ---------- 전체 ----------
async function collectAll() {
  if (!KEY || KEY.startsWith('여기에')) throw new Error('KEY에 V-World 인증키를 넣으세요 (window.VWORLD_KEY = "..." 후 다시 붙여넣기)');
  if (location.hostname !== 'api.vworld.kr') throw new Error('https://api.vworld.kr/req/search 페이지의 콘솔에서 실행하세요');
  const log = m => console.log('%c[수집] ' + m, 'color:#1f6b43');
  const area = AREA;
  const parks = PARKS_TXT.trim().split('\n').map(l => { const [id, g] = l.split('~'); return { id: +id, geom: dec(g) }; });
  const own = [['site_id', 'public_share', 'plan_notice', 'public_m2', 'private_m2', 'owner_unknown_m2', 'polygon_m2', 'boundary_ratio', 'boundary', 'source']];
  const price = [['site_id', 'land_price_krw_m2', 'jimok_dae_m2', 'urban_private_m2', 'greenbelt_m2', 'source']];
  const pTxt = [], aTxt = [];
  const SRC_O = `V-World lt_c_uq162 경계∩lp_pa_cbnd_bubun 면적가중 + getPossessionAttr/ladfrlList 소유구분 · ${new Date().toISOString().slice(0, 10)} 조회; 소유 미확인 면적은 사유지로 계산`;
  const SRC_P = `getLandCharacteristics ${YEAR} 개별공시지가 사유지 면적가중 · urban_private_m2 = 이용상황 단독·연립·주거·주상·상업·업무·공업인 사유지`;
  for (const pk of parks) {
    const r = await doPark(pk.id, pk.geom, log);
    let T = 0, pub = 0, priv = 0, unk = 0, pv = 0, pw = 0, dae = 0, urb = 0, gb = 0;
    for (const x of r.rows) {
      T += x.in; if (x.gb) gb += x.in;
      if (isPub(x.own)) { pub += x.in; continue; }
      priv += x.in; if (x.own === '미확인') unk += x.in;
      const p = x.p || +x.jiga; if (p) { pv += p * x.in; pw += x.in; }
      if (x.jimok === '대') dae += x.in; if (URB.has(x.use)) urb += x.in;
    }
    const ratio = +(r.A / area[pk.id]).toFixed(3);
    own.push([pk.id, (pub / T).toFixed(4), '', pub, priv, unk, Math.round(T), ratio, Math.abs(ratio - 1) <= 0.02 ? '일치' : Math.abs(ratio - 1) <= 0.15 ? '근사' : '불일치', SRC_O]);
    price.push([pk.id, pw ? Math.round(pv / pw) : '', dae, urb, gb, SRC_P]);
    // 지도용 필지 (생태공원3은 사유지·2만㎡ 이상 국유 필지만, 나머지는 공원 상자로 잘라 저장)
    const b = [r.bb[0] - 0.00015, r.bb[1] - 0.00015, r.bb[2] + 0.00015, r.bb[3] + 0.00015];
    for (const x of r.rows.filter(x => pk.id !== 40 || x.own !== '국유지' || x.in >= 20000)) {
      const g = enc(pk.id === 40 ? x.geom : clipG(x.geom, b), pk.id === 40 ? 0.0001 : 0.00001); if (!g) continue;
      const jb = x.jibun.replace(/\s/g, '');
      pTxt.push([pk.id, jb, x.in, x.own, x.jimok, x.jiga, g].join('~'));
      aTxt.push([pk.id, jb, x.own, x.p || '', x.zone, x.gb, x.use].join('~'));
    }
  }
  own.push([5, '', '', '', '', '', '', '', '미확인', '공원 경계 미확인(lt_c_uq162 매칭 실패) → 사유지 100% 가정 유지']);
  download('land_own.csv', csv(own));            // → biz/data/vworld/land_own.csv
  download('land_price.csv', csv(price));        // → biz/data/vworld/land_price.csv
  download('parcels.txt', pTxt.join('\n') + '\n');       // → biz/data/vworld/parcels.txt
  download('parcel_attr.txt', aTxt.join('\n') + '\n');   // → biz/data/vworld/parcel_attr.txt
  log('끝. 다운로드 폴더의 4개 파일을 저장소 같은 위치에 덮어쓰고 biz/README.md 3단계를 진행하세요.');
}

// ---------- 배경지도 (선택) ----------
const lon2x = (lon, z) => (lon + 180) / 360 * 2 ** z * 256;
const lat2y = (lat, z) => { const r = lat * Math.PI / 180; return (1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2 * 2 ** z * 256; };
const x2lon = (x, z) => x / (2 ** z * 256) * 360 - 180;
const y2lat = (y, z) => { const n = Math.PI - 2 * Math.PI * y / (2 ** z * 256); return 180 / Math.PI * Math.atan(Math.sinh(n)); };
async function mosaic(b, layer, maxPx, zmax, qual) {
  let z = zmax; while (z > 5 && (lon2x(b[2], z) - lon2x(b[0], z) > maxPx || lat2y(b[1], z) - lat2y(b[3], z) > maxPx)) z--;
  const X0 = Math.floor(lon2x(b[0], z)), X1 = Math.ceil(lon2x(b[2], z)), Y0 = Math.floor(lat2y(b[3], z)), Y1 = Math.ceil(lat2y(b[1], z));
  const cv = document.createElement('canvas'); cv.width = X1 - X0; cv.height = Y1 - Y0; const cx = cv.getContext('2d'); const ext = layer === 'Satellite' ? 'jpeg' : 'png';
  const jobs = []; for (let tx = Math.floor(X0 / 256); tx <= Math.floor((X1 - 1) / 256); tx++) for (let ty = Math.floor(Y0 / 256); ty <= Math.floor((Y1 - 1) / 256); ty++)
    jobs.push((async () => { const r = await fetch(`/req/wmts/1.0.0/${KEY}/${layer}/${z}/${ty}/${tx}.${ext}`); if (!r.ok) return;
      cx.drawImage(await createImageBitmap(await r.blob()), tx * 256 - X0, ty * 256 - Y0); })());
  await Promise.all(jobs);
  return { z, bounds: [x2lon(X0, z), y2lat(Y1, z), x2lon(X1, z), y2lat(Y0, z)].map(v => +v.toFixed(7)), w: cv.width, h: cv.height,
    data: cv.toDataURL(layer === 'Satellite' ? 'image/jpeg' : 'image/png', qual) };
}
const CITY_BOX = [127.25, 36.43, 127.75, 36.82];
async function collectBasemap() {
  const parks = PARKS_TXT.trim().split('\n').map(l => { const [id, g] = l.split('~'); return { id, geom: dec(g) }; });
  const OUT = {};
  for (const p of parks) { const b = bbOf(p.geom), w = Math.max(b[2] - b[0], b[3] - b[1]) * 0.35 + 0.0004;
    OUT['s' + p.id] = await mosaic([b[0] - w, b[1] - w, b[2] + w, b[3] + w], 'Satellite', 900, 19, 0.62); console.log('위성', p.id); }
  OUT.cityBase = await mosaic(CITY_BOX, 'Base', 1800, 13); OUT.citySat = await mosaic(CITY_BOX, 'Satellite', 1800, 13, 0.6);
  download('cheongju_basemap_vworld.json', JSON.stringify(OUT));   // → python biz/code/extract_basemap.py <파일>
  window.__BASEMAP = OUT;
}
// ---------- 지형 (선택, collectBasemap 다음에 실행: 같은 경계를 쓴다) ----------
async function demTile(b, z, maxPx) {
  const X0 = lon2x(b[0], z), X1 = lon2x(b[2], z), Y0 = lat2y(b[3], z), Y1 = lat2y(b[1], z), s = Math.min(1, maxPx / Math.max(X1 - X0, Y1 - Y0));
  const cv = document.createElement('canvas'); cv.width = Math.max(2, Math.round((X1 - X0) * s)); cv.height = Math.max(2, Math.round((Y1 - Y0) * s));
  const cx = cv.getContext('2d'); cx.imageSmoothingEnabled = false; const jobs = [];
  for (let tx = Math.floor(X0 / 256); tx <= Math.floor((X1 - 1e-9) / 256); tx++) for (let ty = Math.floor(Y0 / 256); ty <= Math.floor((Y1 - 1e-9) / 256); ty++)
    jobs.push((async () => { const r = await fetch(`https://s3.amazonaws.com/elevation-tiles-prod/terrarium/${z}/${tx}/${ty}.png`);
      cx.drawImage(await createImageBitmap(await r.blob()), (tx * 256 - X0) * s, (ty * 256 - Y0) * s, 256 * s, 256 * s); })());
  await Promise.all(jobs);
  const d = cx.getImageData(0, 0, cv.width, cv.height).data; let mn = 1e9, mx = -1e9;
  for (let i = 0; i < d.length; i += 4) { const e = d[i] * 256 + d[i + 1] + d[i + 2] / 256 - 32768; mn = Math.min(mn, e); mx = Math.max(mx, e); }
  return { data: cv.toDataURL('image/png'), w: cv.width, h: cv.height, min: Math.round(mn), max: Math.round(mx) };
}
async function collectDem() {
  const B = window.__BASEMAP || IMG_BOUNDS;
  const OUT = {};
  for (const [k, m] of Object.entries(B)) { if (k === 'cityBase') continue; const city = k === 'citySat';
    OUT[city ? 'city' : k] = { bounds: m.bounds, ...await demTile(m.bounds, city ? 12 : 15, city ? 512 : 256) }; }
  download('cheongju_dem.json', JSON.stringify(OUT));   // → python biz/code/extract_dem.py <파일>
}
console.log('%c준비됨: await collectAll()  /  await collectBasemap()  /  await collectDem()', 'font-weight:bold');
