"""E·D·C 지표 계산 → need/out/indicators_edc.csv (+ edc_wide.csv, 사람이 보는 가로표)

실행: need/edc/code 에서  python build_edc.py
입력(읽기 전용): biz/data/input/sites.csv, biz/data/vworld/parks.txt, biz/data/vworld/gu.txt, need/presets.yaml
원자료: data/raw/worldpop/*.tif (WorldPop 2020 100m constrained), data/raw/osm/*.json (Overpass)
"""
import csv, glob, os, re, sys, warnings
import numpy as np
warnings.filterwarnings('ignore', category=DeprecationWarning)
import rasterio
from rasterio.windows import from_bounds
from shapely.geometry import box
from shapely.ops import transform, unary_union
from shapely.strtree import STRtree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import EDC_P, OUT, RAW, ROOT, _dec, buffers, sites, to5186, write_rows
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
        self.cells, self.vals = [], []
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


def worldpop():
    d = f'{RAW}/worldpop'
    total = Pop(f'{d}/kor_ppp_2020_UNadj_constrained.tif')
    vp = EDC_P['vulnerable_age']; vul = []
    for f in sorted(glob.glob(f'{d}/kor_[fm]_*_2020_constrained.tif')):
        age = int(re.search(r'_[fm]_(\d+)_', f).group(1))       # 밴드 시작 나이: 0, 1(1~4), 5(5~9), 65, 70, 75, 80(80+)
        if age >= vp['old_min'] or age + 4 <= vp['young_max']:
            vul.append(Pop(f))
    return total, vul


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


def main():
    global BBOX
    gu_lines = [l for l in open(f'{ROOT}/biz/data/vworld/gu.txt', encoding='utf-8').read().split('\n') if l]
    gu4326 = {l.split('~')[0]: _dec(l.split('~')[1]) for l in gu_lines}
    BBOX = unary_union(list(gu4326.values())).bounds
    gu = {k: transform(to5186, v) for k, v in gu4326.items()}

    B = buffers(); S = {s['site_id']: s for s in sites()}
    print('공원 경계', len(B), '/ 40')
    total, vul = worldpop(); print('WorldPop 격자', len(total.cells), '칸, 취약연령 밴드', len(vul))
    ex_parks, served, n_ex = existing_service(g for g, _, _ in B.values()); print('기존 공원(OSM)', n_ex)
    water, green, anyriver = axes()

    # D2 대체: 구별 1인당 기존 공원면적 (생활권 표 7-10 수령 전)
    d2 = {k: ex_parks.intersection(g).area / max(total.sum(g), 1) for k, g in gu.items()}
    print('구별 1인당 기존공원(㎡, OSM·WorldPop)', {k: round(v, 2) for k, v in d2.items()})

    rows, wide = [], []
    WP, OS = 'WP-2020', 'OSM-2026-11'
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
        e1 = total.sum(buf)
        e2v = sum(v.sum(buf) for v in vul)
        unserved = buf.difference(served)
        new = total.sum(unserved)
        e2 = e2v / e1 if e1 > 0 else None
        d1 = new / e1 if e1 > 0 else None
        gname = max(gu, key=lambda k: gu[k].intersection(park).area)
        cw, cg = park.distance(water), park.distance(green)
        c1 = min(cw, cg)
        radj = int(park.distance(anyriver) <= EDC_P['river_adjacent_m'])
        add(sid, 'E1', round(e1), '명', WP, '대체자료')
        # WorldPop 연령 밴드는 넓은 행정구역 비율을 그대로 나눠 놓아 공원 간 차이가 없다(전 공원 0.285) → 미산정
        add(sid, 'E2', None, '비율(0~1)', WP, '미산정')
        add(sid, 'D1', None if d1 is None else round(d1, 4), '비율(0~1)', f'{WP};{OS}', '대체자료')
        add(sid, 'D2', round(d2[gname], 2), '㎡/인', f'{WP};{OS}', '대체자료')
        add(sid, 'C1', round(c1), 'm', OS, '대체자료')
        add(sid, 'C1_near', int(c1 <= EDC_P['c1_near_m']), '1/0', OS, '가정')
        add(sid, 'river_adjacent', radj, '1/0', OS, '가정')
        add(sid, 'new_served_pop', round(new), '명', f'{WP};{OS}', '대체자료')
        wide.append({'site_id': sid, 'name': s['name'], 'type': s['type'], 'gu': gname, 'buffer_m': rad,
                     'E1_pop': round(e1), 'E2_vulnerable_wp_uniform': None if e2 is None else round(e2, 3),
                     'D1_unserved': None if d1 is None else round(d1, 3), 'new_served_pop': round(new),
                     'D2_gu_m2_per_cap': round(d2[gname], 2), 'C1_m': round(c1), 'C1_water_m': round(cw), 'C1_green_m': round(cg),
                     'C1_near': int(c1 <= EDC_P['c1_near_m']), 'river_adjacent': radj, 'note': ''})

    write_rows(f'{OUT}/indicators_edc.csv', rows)
    keys = list(dict.fromkeys(k for w in wide for k in w))
    with open(f'{OUT}/edc_wide.csv', 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(wide)

    # 검증: 값 범위, site_id 1~40, D1↔E1 상관
    ok = [w for w in wide if w.get('E1_pop') is not None]
    assert {r['site_id'] for r in rows} == {str(i) for i in range(1, 41)}
    pos = [w for w in ok if w['E1_pop'] > 0]
    assert all(0 <= w['D1_unserved'] <= 1 for w in pos)
    e2s = {w['E2_vulnerable_wp_uniform'] for w in pos}
    print('E2(WorldPop) 서로 다른 값 개수:', len(e2s), '→ 1이면 공원 간 차이 없음, 미산정 유지')
    e1 = np.array([w['E1_pop'] for w in pos], float); d1v = np.array([w['D1_unserved'] for w in pos], float)
    from scipy.stats import spearmanr
    print('행', len(rows), '/ 산정 공원', len(ok), '/ 인구 0 공원', len(ok) - len(pos),
          '/ r(D1,E1) pearson =', round(float(np.corrcoef(e1, d1v)[0, 1]), 3), 'spearman =', round(float(spearmanr(e1, d1v)[0]), 3))
    print('저장:', f'{OUT}/indicators_edc.csv', f'{OUT}/edc_wide.csv')


if __name__ == '__main__':
    main()
