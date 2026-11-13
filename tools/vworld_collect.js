/* ============================================================================
 * 청주 장기미집행 공원 — V-World 토지 자료 수집기 (브라우저 콘솔용)
 *
 * 실행 방법은 저장소 맨 위 「실행방법.md」 참고. 요약:
 *   1) 크롬/엣지에서 https://api.vworld.kr 을 연다 (V-World가 같은 주소에서만 응답을 허용)
 *   2) F12 → Console 탭에 이 파일 전체를 붙여 넣고 Enter
 *   3) 아래 KEY 줄에 인증키를 넣고 실행:  await collectAll()
 *      → 다운로드 폴더에 6개 파일이 생긴다. 저장소의 같은 이름 파일에 덮어쓰면 끝.
 *   (선택) await collectBasemap()  → 위성사진·일반지도 (cheongju_basemap_vworld.json)
 *   (선택) await collectDem()      → 지형 표고 (cheongju_dem.json)
 *
 * 하는 일 (2026-11-13 수집과 같은 방법):
 *   공원 경계(data/geo/parks.txt, V-World 도시계획시설 lt_c_uq162에서 매칭해 둔 것)
 *   ∩ 연속지적도(lp_pa_cbnd_bubun) 필지 → 공원 안 격자 표본점으로 필지별 공원 안 면적 배분
 *   → 필지별 소유구분(getPossessionAttr, 없으면 ladfrlList 토지임야목록)
 *   → 필지별 토지특성(getLandCharacteristics: 개별공시지가·용도지역·이용상황, 기준연도 YEAR)
 *   → 공원별 집계 (국공유 비율, 사유지 공시지가 면적가중, 지목 '대' 사유지, 건물·시가지 사유지, 개발제한구역)
 * ========================================================================== */

const KEY  = window.VWORLD_KEY || '여기에_인증키';   // 실행방법.md 의 키
const YEAR = '2026';                                   // 토지특성(공시지가) 기준연도
const RAW  = 'https://raw.githubusercontent.com/jjhksj2020-lgtm/cheongju-park-nbs/main/';

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
// 압축 좌표: 정수(경위도×1e5) 누적차분, 링 '|', 다각형 ';'  (dashboard/build_mapdata.py가 읽는 형식)
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
const URB = new Set(['단독', '연립', '주거기타', '주거나지', '주상기타', '주상나지', '상업용', '업무용', '공업용']);  // 건물·시가지 이용상황

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
  if (location.hostname !== 'api.vworld.kr') throw new Error('https://api.vworld.kr 페이지의 콘솔에서 실행하세요');
  const log = m => console.log('%c[수집] ' + m, 'color:#1f6b43');
  const parksTxt = await fetch(RAW + 'data/geo/parks.txt').then(r => r.text());
  const sitesCsv = await fetch(RAW + 'biz/data/sites.csv').then(r => r.text());
  const area = {}; sitesCsv.trim().split('\n').slice(1).forEach(l => { const c = l.split(','); area[c[0]] = +c[7]; });   // site_id … area_m2(8번째 열)
  const parks = parksTxt.trim().split('\n').map(l => { const [id, g] = l.split('~'); return { id: +id, geom: dec(g) }; });
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
  download('land_own.csv', csv(own));            // → biz/data/land_own.csv
  download('land_price.csv', csv(price));        // → biz/data/land_price.csv
  download('parcels.txt', pTxt.join('\n') + '\n');       // → data/geo/parcels.txt
  download('parcel_attr.txt', aTxt.join('\n') + '\n');   // → data/geo/parcel_attr.txt
  log('끝. 다운로드 폴더의 4개 파일을 저장소 같은 위치에 덮어쓰고 실행방법.md 3단계를 진행하세요.');
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
  const parks = (await fetch(RAW + 'data/geo/parks.txt').then(r => r.text())).trim().split('\n').map(l => { const [id, g] = l.split('~'); return { id, geom: dec(g) }; });
  const OUT = {};
  for (const p of parks) { const b = bbOf(p.geom), w = Math.max(b[2] - b[0], b[3] - b[1]) * 0.35 + 0.0004;
    OUT['s' + p.id] = await mosaic([b[0] - w, b[1] - w, b[2] + w, b[3] + w], 'Satellite', 900, 19, 0.62); console.log('위성', p.id); }
  OUT.cityBase = await mosaic(CITY_BOX, 'Base', 1800, 13); OUT.citySat = await mosaic(CITY_BOX, 'Satellite', 1800, 13, 0.6);
  download('cheongju_basemap_vworld.json', JSON.stringify(OUT));   // → python dashboard/extract_basemap.py <파일>
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
  const B = window.__BASEMAP || await fetch(RAW + 'dashboard/img/manifest.json').then(r => r.json());
  const OUT = {};
  for (const [k, m] of Object.entries(B)) { if (k === 'cityBase') continue; const city = k === 'citySat';
    OUT[city ? 'city' : k] = { bounds: m.bounds, ...await demTile(m.bounds, city ? 12 : 15, city ? 512 : 256) }; }
  download('cheongju_dem.json', JSON.stringify(OUT));   // → python dashboard/extract_dem.py <파일>
}
console.log('%c준비됨: await collectAll()  /  await collectBasemap()  /  await collectDem()', 'font-weight:bold');
