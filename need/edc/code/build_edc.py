"""E·D·C 지표 계산 → need/out/indicators_edc.csv (+ edc_wide.csv, 사람이 보는 가로표)

실행: need/edc/code 에서  python build_edc.py
입력(읽기 전용): biz/data/input/sites.csv, biz/data/vworld/parks.txt, biz/data/vworld/gu.txt, need/presets.yaml
원자료: data/raw/worldpop/*.tif (WorldPop 2020 100m constrained), data/raw/osm/*.json (Overpass)
"""
import csv, json, os, sys, warnings
import numpy as np
warnings.filterwarnings('ignore', category=DeprecationWarning)
import rasterio
from rasterio.windows import from_bounds
from shapely.geometry import box
from shapely.ops import transform, unary_union
from shapely.strtree import STRtree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import EDC_P, OUT, RAW, ROOT, _dec, buffers, sites, to4326, to5186, write_rows
import osm

BBOX = None  # 청주시 경계(구 4개)의 범위로 채운다


# ---------- 인구 ----------
class Pop:
    """100m 격자 하나. 도형 안 인구 = Σ 값 × (격자∩도형 면적 / 격자 면적)."""
    def __init__(self, path):
        with rasterio.open(path) as r:
            w = from_bounds(*BBOX, r.transform)
            a = r.read(1, window=w, boundless=True, fill_value=0).astype('float64')
            t = r.window_transform(w); nd = r.nodata
        if nd is not None:
            a[a == nd] = 0
        a[~np.isfinite(a)] = 0; a[a < 0] = 0
        rows, cols = np.nonzero(a)
        self.cells, self.vals, self.wt = [], [], None
        for i, j in zip(rows, cols):
            x0, y0 = t * (j, i); x1, y1 = t * (j + 1, i + 1)
            self.cells.append(transform(to5186, box(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))))
            self.vals.append(a[i, j])
        self.tree = STRtree(self.cells)

    def sum(self, g):
        if g is None or g.is_empty:
            return 0.0
        s = 0.0
        for k in self.tree.query(g):
            c = self.cells[k]; s += self.vals[k] * c.intersection(g).area / c.area
        return s

    def set_ratio(self, dongs, ratio):
        """격자 중심이 속한 행정동의 비율(취약연령 ÷ 총인구)을 격자마다 붙인다."""
        names = list(dongs); tree = STRtree([dongs[n] for n in names]); self.wt = []
        for c in self.cells:
            p = c.centroid; hit = [names[k] for k in tree.query(p) if dongs[names[k]].contains(p)]
            self.wt.append(ratio[hit[0]] if hit else None)

    def ratio(self, g):
        """도형 안 인구 가중 평균 비율 (동 비율이 없는 격자는 제외)."""
        num = den = 0.0
        for k in self.tree.query(g):
            if self.wt[k] is None:
                continue
            c = self.cells[k]; v = self.vals[k] * c.intersection(g).area / c.area
            num += v * self.wt[k]; den += v
        return num / den if den > 0 else None


def worldpop():
    return Pop(f'{RAW}/worldpop/kor_ppp_2020_UNadj_constrained.tif')


def dongs():
    """행정동 경계(5186)와 주민등록 연령 집계. 이름 = 동 이름(청주 안에서 중복 없음)."""
    from shapely.geometry import shape
    gj = json.load(open(f'{RAW}/dong/cheongju_dong_20261001.geojson', encoding='utf-8'))
    geo = {f['properties']['adm_nm'].split()[-1].replace('·', ''): transform(to5186, shape(f['geometry'])) for f in gj['features']}
    age = {r['dong'].replace('·', ''): r for r in csv.DictReader(open(f'{RAW}/mois/cheongju_age_dong_20261031.csv', encoding='utf-8-sig'))}
    assert set(geo) == set(age), set(geo) ^ set(age)
    ratio = {n: (int(r['age0_9']) + int(r['age65p'])) / int(r['total']) for n, r in age.items()}
    gu = {n: r['gu'].split()[-1] for n, r in age.items()}
    return geo, ratio, gu


# ---------- 기존 공원 서비스권 (D1) ----------
def existing_service(targets):
    R = EDC_P['service_radius_m']; small = EDC_P['small_park_m2']; tgt = unary_union(list(targets))
    parks, zones = [], []
    for tags, g in osm.areas('parks'):
        if g.intersection(tgt).area > 0:          # 평가 대상 40개소 자신은 '기존 공원'에서 뺀다
            continue
        name = tags.get('name', '')
        if tags.get('leisure') == 'playground' or '어린이' in name:
            r = R['어린이공원']
        elif '근린' in name:
            r = R['근린공원']
        elif g.area < small:
            r = R['소공원']
        else:
            r = R['default']
        parks.append(g); zones.append(g.buffer(r))
    return unary_union(parks), unary_union(zones), len(parks)


# ---------- 녹지·수변축 (C1) ----------
def axes():
    names = set(EDC_P['axis_rivers']); ww = osm.waterways()
    water = unary_union([g for t, g in ww if t.get('name') in names])
    anyriver = unary_union([g for t, g in ww if t.get('waterway') in ('river', 'stream')])
    forest = unary_union([g for t, g in osm.areas('forests')])
    big = [p for p in getattr(forest, 'geoms', [forest]) if p.area >= EDC_P['axis_forest_min_ha'] * 1e4]
    return water, unary_union(big), anyriver


def landuse():
    L = osm.areas('landuse')
    return {k: unary_union([g for t, g in L if t.get('landuse') in v])
            for k, v in {'res': ['residential'], 'ind': ['industrial'], 'com': ['commercial', 'retail']}.items()}


def area_type(dens, res, ind):
    """밀집/주거/산업/기타 — 표시용 라벨 (params area_type, 가정)."""
    A = EDC_P['area_type']; t = []
    if dens >= A['dense_per_km2']:
        t.append('밀집')
    elif dens >= A['residential_per_km2'] or res >= A['residential_share']:
        t.append('주거')
    if ind >= A['industrial_share']:
        t.append('산업')
    return '+'.join(t) or '기타'


def _geo(g, tol=8):
    """5186 도형 → 단순화한 경위도 좌표 목록 (지도용)."""
    from shapely.geometry import mapping
    g = transform(to4326, g.simplify(tol))
    m = mapping(g)
    rnd = lambda c: [round(c[0], 5), round(c[1], 5)]
    if m['type'] == 'Polygon':
        return [[[rnd(c) for c in r] for r in m['coordinates']]]
    if m['type'] == 'MultiPolygon':
        return [[[rnd(c) for c in r] for r in p] for p in m['coordinates']]
    if m['type'] == 'LineString':
        return [[rnd(c) for c in m['coordinates']]]
    if m['type'] == 'MultiLineString':
        return [[rnd(c) for c in l] for l in m['coordinates']]
    return []


def main():
    global BBOX
    gu_lines = [l for l in open(f'{ROOT}/biz/data/vworld/gu.txt', encoding='utf-8').read().split('\n') if l]
    gu4326 = {l.split('~')[0]: _dec(l.split('~')[1]) for l in gu_lines}
    BBOX = unary_union(list(gu4326.values())).bounds
    gu = {k: transform(to5186, v) for k, v in gu4326.items()}

    B = buffers()
    print('공원 경계', len(B), '/ 40')
    total = worldpop(); print('WorldPop 격자', len(total.cells), '칸')
    dgeo, dratio, dgu = dongs(); total.set_ratio(dgeo, dratio)
    ex_parks, served, n_ex = existing_service(g for g, _, _ in B.values()); print('기존 공원(OSM)', n_ex)
    water, green, anyriver = axes()
    LU = landuse()
    LZ = EDC_P['living_zone_park']; DT = set(EDC_P['downtown_dongs'])
    zone_of = lambda dong: '도심생활권' if dong in DT else f"{dgu[dong][:2]}생활권"

    rows, wide, geo_out = [], [], {}
    WP, OS, MO, LZK = 'WP-2020', 'OSM-2026-11', 'MOIS-2026-10', 'PARK2030-T11-2'
    def add(sid, ind, val, unit, src, tag):
        rows.append({'site_id': sid, 'indicator': ind, 'value': '' if val is None else val, 'unit': unit, 'source_key': src, 'tag': tag})

    for s in sites():
        sid = s['site_id']
        if sid not in B:
            for ind, unit in [('E1', '명'), ('E2', '비율(0~1)'), ('D1', '비율(0~1)'), ('D2', '㎡/인'), ('C1', 'm'),
                              ('C1_near', '1/0'), ('river_adjacent', '1/0'), ('new_served_pop', '명')]:
                add(sid, ind, None, unit, 'VW-upis', '미산정')
            wide.append({'site_id': sid, 'name': s['name'], 'note': '공원 경계 없음(V-World 매칭 실패) → 미산정'}); continue
        park, buf, rad = B[sid]
        dong = max(dgeo, key=lambda k: dgeo[k].intersection(park).area)
        zone = zone_of(dong)
        e1 = total.sum(buf)
        e2 = total.ratio(buf)
        e2_src = '버퍼 격자 가중'
        if e2 is None:                       # 버퍼에 거주 격자가 없으면 공원이 속한 동의 비율
            e2, e2_src = dratio[dong], '소속 동 값'
        new = total.sum(buf.difference(served))
        d1 = new / e1 if e1 > 0 else None
        d2 = LZ['per_cap_built'][zone]
        cw, cg = park.distance(water), park.distance(green)
        c1 = min(cw, cg)
        radj = int(park.distance(anyriver) <= EDC_P['river_adjacent_m'])
        dens = e1 / (buf.area / 1e6)
        sh = {k: buf.intersection(v).area / buf.area for k, v in LU.items()}
        atype = area_type(dens, sh['res'], sh['ind'])
        add(sid, 'E1', round(e1), '명', WP, '대체자료')
        add(sid, 'E2', round(e2, 4), '비율(0~1)', f'{MO};{WP}', '실자료')
        add(sid, 'D1', None if d1 is None else round(d1, 4), '비율(0~1)', f'{WP};{OS}', '대체자료')
        add(sid, 'D2', d2, '㎡/인', LZK, '실자료' if zone != '도심생활권' else '가정')
        add(sid, 'C1', round(c1), 'm', OS, '대체자료')
        add(sid, 'C1_near', int(c1 <= EDC_P['c1_near_m']), '1/0', OS, '가정')
        add(sid, 'river_adjacent', radj, '1/0', OS, '가정')
        add(sid, 'new_served_pop', round(new), '명', f'{WP};{OS}', '대체자료')
        wide.append({'site_id': sid, 'name': s['name'], 'type': s['type'], 'dong': dong, 'living_zone': zone, 'buffer_m': rad,
                     'E1_pop': round(e1), 'E2_vulnerable': round(e2, 3), 'E2_basis': e2_src,
                     'D1_unserved': None if d1 is None else round(d1, 3), 'new_served_pop': round(new),
                     'D2_built_m2_per_cap': d2, 'D2_decided_m2_per_cap': LZ['per_cap_decided'][zone],
                     'C1_m': round(c1), 'C1_water_m': round(cw), 'C1_green_m': round(cg),
                     'C1_near': int(c1 <= EDC_P['c1_near_m']), 'river_adjacent': radj,
                     'area_type': atype, 'pop_density_km2': round(dens), 'osm_res_share': round(sh['res'], 3),
                     'osm_ind_share': round(sh['ind'], 3), 'osm_com_share': round(sh['com'], 3), 'note': ''})
        geo_out[sid] = {'park': _geo(park, 2), 'buffer': _geo(buf, 8)}

    write_rows(f'{OUT}/indicators_edc.csv', rows)
    keys = list(dict.fromkeys(k for w in wide for k in w))
    with open(f'{OUT}/edc_wide.csv', 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(wide)

    # 지도용 데이터 (need/out/edc_map.json → build_page.py)
    from shapely.geometry import box as _box
    near = unary_union([b for _, b, _ in B.values()]).buffer(1500)
    view = _box(*near.bounds).buffer(3000)
    cells = []
    for c, v, w in zip(total.cells, total.vals, total.wt):
        if c.intersects(near):
            x, y = transform(to4326, c.centroid).coords[0]
            cells.append([round(x, 5), round(y, 5), round(float(v), 1), None if w is None else round(w, 3)])
    big_parks = unary_union([p for p in getattr(ex_parks, 'geoms', [ex_parks]) if p.intersects(near)])
    mapd = {'asof': '2026-11-15', 'sites': wide, 'geo': geo_out,
            'served': _geo(served.intersection(near), 10), 'existing': _geo(big_parks, 4),
            'water': _geo(water.intersection(view), 15), 'forest': _geo(green.intersection(view), 25),
            'gu': {k: _geo(g, 30) for k, g in gu.items()}, 'cells': cells,
            'zones': EDC_P['living_zone_park'], 'params': {k: EDC_P[k] for k in ('area_type', 'c1_near_m', 'river_adjacent_m', 'axis_forest_min_ha', 'axis_rivers')},
            'buffer_m': {k: v for k, v in __import__('common').PRESETS['buffer_m'].items()}}
    json.dump(mapd, open(f'{OUT}/edc_map.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('지도 데이터', f'{OUT}/edc_map.json', os.path.getsize(f'{OUT}/edc_map.json') // 1024, 'KB, 격자', len(cells))

    # 검증: site_id 1~40, 값 범위, 주민등록 합계, 상관
    ok = [w for w in wide if w.get('E1_pop') is not None]
    assert {r['site_id'] for r in rows} == {str(i) for i in range(1, 41)}
    pos = [w for w in ok if w['E1_pop'] > 0]
    assert all(0 <= w['D1_unserved'] <= 1 for w in pos) and all(0 <= w['E2_vulnerable'] <= 1 for w in ok)
    print('E2 범위', min(w['E2_vulnerable'] for w in ok), '~', max(w['E2_vulnerable'] for w in ok),
          '/ 서로 다른 값', len({w['E2_vulnerable'] for w in ok}))
    from collections import Counter
    print('지역 유형', Counter(w['area_type'] for w in ok))
    print('C1_near', sum(w['C1_near'] for w in ok), '/', len(ok))
    print('생활권 배정', {z: [w['site_id'] for w in ok if w['living_zone'] == z] for z in LZ['per_cap_built']})
    from scipy.stats import spearmanr
    cols = ['E1_pop', 'E2_vulnerable', 'D1_unserved', 'D2_built_m2_per_cap', 'C1_m']
    M = np.array([[w[c] for c in cols] for w in pos], float)
    print('행', len(rows), '/ 산정 공원', len(ok), '/ 인구 0 공원', len(ok) - len(pos))
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            r = float(np.corrcoef(M[:, i], M[:, j])[0, 1]); rs = float(spearmanr(M[:, i], M[:, j])[0])
            flag = '  ← |r|≥0.7' if max(abs(r), abs(rs)) >= 0.7 else ''
            print(f'  r({cols[i]},{cols[j]}) pearson {r:.2f} spearman {rs:.2f}{flag}')
    print('저장:', f'{OUT}/indicators_edc.csv', f'{OUT}/edc_wide.csv')


if __name__ == '__main__':
    main()
