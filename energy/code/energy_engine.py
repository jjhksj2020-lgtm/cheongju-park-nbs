"""청주 장기미집행 공원 40개소 — 열저감 계산 엔진 (energy 파트, 독립 참고 결과)

질문: 공원을 조성하면(지금 상태 대비) 공원 일대와 주변의 여름 지표온도가 얼마나 내려가나?
원칙: 계수는 모두 청주 위성 실측. 문헌 계수 0개. 전력(kWh)으로는 바꾸지 않는다.

계산 사슬 (공원마다, 시나리오마다)
  ① 녹지 증가 ΔNDVI = max(0, 조성 목표 NDVI − 지금 NDVI)                 지금: Sentinel-2 / 목표: 청주 잔디~수목 중앙값
  ② 공원 일대 지표온도 저감 = 계수 × ΔNDVI × min(1, 공원 면적 ÷ 1ha)       계수: 청주에서 녹지가 실제로 변한 픽셀의 기울기
       (1ha = Landsat 열밴드가 온도를 구분하는 최소 칸. 그보다 작은 공원은 칸 안에서 섞인 만큼만 낮아진다)
  ③ 주변 300m 지표온도 저감 = ② × 퍼짐 비율 (1ha 이상 공원만)          퍼짐: 특례사업지 개발 전후 실측
  ④ 냉각량(°C·ha) = ② × max(면적, 1ha) + ③ × 고리 면적                 순위·등급 기준
3개 계수(목표 NDVI·온도 계수·퍼짐)의 상·하한 8개 시나리오. 모두 같은 등급이면 확정.

입력 (읽기만)
  biz/data/input/sites.csv · biz/data/vworld/{parks,gu,parcels,parcel_attr}.txt · land_own.csv
  energy/data/gee/gee_output.txt          1차 GEE: 공원별 지금 NDVI·인구, 조성 목표 NDVI (CITY|, PARK|)
  energy/data/gee/gee_change_output.txt   2차 GEE: 녹지 변화-온도 변화 계수, 고리 면적 (CHANGE|, RING|)
  energy/data/gee/tukrye_before_after.json  특례사업지 전후 실측
출력 (energy/out/): master_energy.csv · summary.md · energydata.json(지도용)
코드에 기준값 숫자를 쓰지 않는다 — params.yaml만 읽는다.
"""
from __future__ import annotations
import csv, itertools, json, os, yaml

C = os.path.dirname(os.path.abspath(__file__)); E = os.path.dirname(C); ROOT = os.path.dirname(E)
P = yaml.safe_load(open(f'{C}/params.yaml', encoding='utf-8'))
BIZ = f'{ROOT}/biz/data'; GEE = f'{E}/data/gee'; OUT = f'{E}/out'
os.makedirs(OUT, exist_ok=True)
HA = P['units']['m2_per_ha']; CELL = P['thermal_cell_m2']; RING_MIN = P['spillover']['min_park_m2']


def read_lines(path, tags):
    got = {t: [] for t in tags}
    for line in open(path, encoding='utf-8'):
        for t in tags:
            if line.startswith(t + '|'):
                got[t].append(json.loads(line[len(t) + 1:]))
    return got


# ---------- 읽기 ----------
sites = {int(r['site_id']): r for r in csv.DictReader(open(f'{BIZ}/input/sites.csv', encoding='utf-8-sig'))}
g1 = read_lines(f'{GEE}/gee_output.txt', ['CITY', 'PARK'])
g2 = read_lines(f'{GEE}/gee_change_output.txt', ['CHANGE', 'RING'])
city = g1['CITY'][0]; change = g2['CHANGE'][0]
gee = {int(r['id']): r for r in g1['PARK']}
ring_area = {int(r['id']): r['ring_area'] for r in g2['RING']}
own = {int(r['site_id']): r for r in csv.DictReader(open(f'{BIZ}/vworld/land_own.csv', encoding='utf-8-sig'))}
tk = json.load(open(f"{GEE}/{P['spillover']['source_file']}", encoding='utf-8'))
spill = [r['neighbor_300m'] / r['effect'] for r in tk['sites'] if r['site'] in P['spillover']['sites']]

cls_of = {u: c for c, us in P['landuse_class'].items() for u in us}   # 지금 땅 상태 (설명용)
landuse = {}
parcels = [l.split('~') for l in open(f'{BIZ}/vworld/parcels.txt', encoding='utf-8').read().split('\n') if l]
attrs = [l.split('~') for l in open(f'{BIZ}/vworld/parcel_attr.txt', encoding='utf-8').read().split('\n') if l]
for p, a in zip(parcels, attrs):
    assert p[0] == a[0] and p[1] == a[1], (p[:2], a[:2])
    d = landuse.setdefault(int(p[0]), {c: 0.0 for c in P['landuse_class']})
    d[cls_of.get(a[6], P['landuse_other'])] += float(p[2])

# ---------- 계수 (모두 청주 실측) ----------
COEF = {k: abs(change[f'{k}_slope']) for k in ('green', 'loss', 'all')}
TARGET = {'grass': city['ndvi_grass'], 'tree': city['ndvi_tree']}
FACTORS = {
    'target': (TARGET[P['target_ndvi']['low']], TARGET[P['target_ndvi']['high']]),
    'coef': tuple(sorted((COEF[P['coef']['low']], COEF[P['coef']['high']]))),
    'spill': (min(spill), max(spill)),
}
SCEN = [dict(zip(FACTORS, c)) for c in itertools.product(*FACTORS.values())]
BASE = {k: sum(v) / len(v) for k, v in FACTORS.items()}   # 보고용 기준 = 중간값


def chain(g, area, ring_m2, f):
    dndvi = max(P['ndvi_gain_floor'], f['target'] - g['ndvi_s2'])
    d_cell = f['coef'] * dndvi * min(1, area / CELL)
    d_ring = d_cell * f['spill'] if area >= RING_MIN else 0
    amount = d_cell * max(area, CELL) / HA + d_ring * ring_m2 / HA
    return {'dndvi': dndvi, 'd_cell': d_cell, 'd_ring': d_ring, 'amount': amount}


rows, per = [], {}
for sid, s in sites.items():
    g = gee.get(sid); lu = landuse.get(sid) or {}; lt = sum(lu.values())
    row = {'site_id': sid, 'name': s['name'], 'type': s['type'], 'location': s['location'], 'area_m2': int(float(s['area_m2'])),
           'expiry': s['expiry'], **{f'share_{c}': (round(v / lt, 3) if lt else '') for c, v in lu.items()},
           'dominant_landuse': max(lu, key=lu.get) if lt else '미확인', 'boundary': own.get(sid, {}).get('boundary') or '미확인'}
    note = ''
    if g is None:
        note = '공원 경계 없음(V-World 도시계획시설 미등재) → 미산정'
    elif s['type'] in P['excluded_types']:
        note = P['excluded_note']
    if note:
        rows.append({**row, 'kind': '미산정', 'status': '미산정', 'note': note}); continue
    area = g['area_poly']; rm2 = ring_area.get(sid, 0)
    res = [chain(g, area, rm2, f) for f in SCEN]; b = chain(g, area, rm2, BASE); per[sid] = res
    lo = lambda k: min(r[k] for r in res); hi = lambda k: max(r[k] for r in res)
    big = area >= RING_MIN
    row.update({
        'status': '산정', 'kind': '보전형' if g['ndvi_s2'] >= FACTORS['target'][0] else '조성형',
        'ndvi_now': round(g['ndvi_s2'], 3), 'lsta_now': round(g['lsta'], 2) if g.get('lsta') is not None else '',
        'poly_m2': round(area), 'cell_share': round(min(1, area / CELL), 3),
        'ring_applied': '적용' if big else '해당 없음(1ha 미만)', 'ring_ha': round(rm2 / HA, 2) if big else '',
        'pop_300': round(g['pop_300']),
        'dndvi_base': round(b['dndvi'], 3), 'dndvi_low': round(lo('dndvi'), 3), 'dndvi_high': round(hi('dndvi'), 3),
        'dlst_cell_base': round(b['d_cell'], 2), 'dlst_cell_low': round(lo('d_cell'), 2), 'dlst_cell_high': round(hi('d_cell'), 2),
        'dlst_ring_base': round(b['d_ring'], 2), 'dlst_ring_low': round(lo('d_ring'), 2), 'dlst_ring_high': round(hi('d_ring'), 2),
        'cool_base': round(b['amount'], 2), 'cool_low': round(lo('amount'), 2), 'cool_high': round(hi('amount'), 2),
        'note': '' if row['boundary'] in P['boundary_ok'] else f"경계 {row['boundary']} — 사업성 파트 기록대로 청주시 확인 필요"})
    rows.append(row)

# ---------- 등급 ----------
ids = list(per); grades = {i: [] for i in ids}
n_top = round(len(ids) * P['grade']['top_share']); n_mid = round(len(ids) * P['grade']['mid_share'])
for k in range(len(SCEN)):
    order = sorted(ids, key=lambda i: per[i][k]['amount'], reverse=True)
    for rank, i in enumerate(order):
        v = per[i][k]['amount']
        grades[i].append('하' if v <= P['ndvi_gain_floor'] else '상' if rank < n_top else '중' if rank < n_mid else '하')
ORDER = ['상', '중', '하']
for row in rows:
    gs = grades.get(row['site_id'])
    if gs:
        u = sorted(set(gs), key=ORDER.index)
        row.update({'grade': max(set(gs), key=gs.count), 'grade_stable': '확정' if len(u) == 1 else '경계',
                    'grade_range': u[0] if len(u) == 1 else f'{u[0]}~{u[-1]}'})
    else:
        row.update({'grade': '', 'grade_stable': '', 'grade_range': ''})

cols = list(dict.fromkeys(k for r in rows for k in r))
with open(f'{OUT}/master_energy.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

# ---------- 요약 ----------
ok = [r for r in rows if r['status'] == '산정']
tot = lambda k, rs=ok: sum(r[k] for r in rs)
kinds = {k: [r for r in ok if r['kind'] == k] for k in ('조성형', '보전형')}
top = sorted(ok, key=lambda r: r['cool_base'], reverse=True)
share = lambda rs: tot('cool_base', rs) / tot('cool_base') if tot('cool_base') else 0
L = ['# 에너지(열저감) 파트 요약 — 독립 참고 결과', '',
     f"기준: 조성 vs 지금 그대로. 계수는 모두 청주 위성 실측(문헌 계수 0개). 시나리오 {len(SCEN)}개. 산정 {len(ok)}개소 / 미산정 {len(rows) - len(ok)}개소.", '',
     '## 청주 계수 (GEE)',
     f"- 녹지 변화 → 지표온도 변화 ({P['change']['before'][0][:4]}–{P['change']['before'][1][:4]} → {P['change']['after'][0][:4]}–{P['change']['after'][1][:4]} 여름, NDVI가 {P['change']['min_change']} 이상 변한 픽셀):",
     f"  - 녹지가 늘어난 곳 {change['green_n']:,}픽셀: NDVI 1당 {change['green_slope']:.2f}°C",
     f"  - 녹지가 줄어든 곳 {change['loss_n']:,}픽셀: NDVI 1당 {change['loss_slope']:.2f}°C",
     f"  - 전체 {change['all_n']:,}픽셀: NDVI 1당 {change['all_slope']:.2f}°C (참고)",
     f"  - 참고: 한 시기 공간 비교 회귀(1차 실행)는 {city['b_controlled']:.2f} ~ {city['b_simple']:.2f}°C — 변화가 아니라 장소 차이라 쓰지 않음",
     f"- 조성 목표 NDVI: 잔디·초지 {TARGET['grass']:.3f} ~ 수목 {TARGET['tree']:.3f} (Sentinel-2 여름 {city['s2_scenes']}장)",
     f"- 주변 {P['change']['ring_m']}m 퍼짐: {FACTORS['spill'][0]:.2f} ~ {FACTORS['spill'][1]:.2f} ({', '.join(P['spillover']['sites'])} 실측), 1ha 이상 공원만", '',
     '## 합계',
     f"- 냉각량: {tot('cool_low'):,.1f} ~ {tot('cool_high'):,.1f} °C·ha (기준 {tot('cool_base'):,.1f})",
     ] + [f"- {k} {len(rs)}곳: 기준 {tot('cool_base', rs):,.1f} °C·ha ({share(rs):.0%})" for k, rs in kinds.items()] + [
     '', '## 냉각량 상위 10 (기준 시나리오)', '',
     '| 순위 | 공원 | 성격 | 면적㎡ | 지금 NDVI | 공원 일대 저감°C | 주변 300m 저감°C | 냉각량 °C·ha (범위) | 주변 인구 | 등급 |',
     '|---|---|---|---|---|---|---|---|---|---|'] + [
    f"| {i} | {r['name']} | {r['kind']} | {r['area_m2']:,} | {r['ndvi_now']} | {r['dlst_cell_base']} | {r['dlst_ring_base'] if r['ring_applied'] == '적용' else '—'} | {r['cool_base']} ({r['cool_low']}~{r['cool_high']}) | {r['pop_300']:,} | {r['grade_range']} {r['grade_stable']} |"
    for i, r in enumerate(top[:10], 1)] + [
     '', '## 미산정', ''] + [f"- {r['name']}: {r['note']}" for r in rows if r['status'] != '산정'] + [
     '', '## 검증',
     f"- 시나리오 {len(SCEN)}개 모두 계산: {all(len(v) == len(SCEN) for v in per.values())}",
     f"- 등급 확정 {sum(r['grade_stable'] == '확정' for r in ok)}개소 / 경계 {sum(r['grade_stable'] == '경계' for r in ok)}개소",
     '- 코드에 기준값 숫자 없음: params.yaml만 읽음', '',
     '## 한계',
     '- 지표온도(땅 표면)이며 기온이 아니다. 전력 절감으로 바꾸지 않는다(국지 기온–전력 관계의 근거 부족, evidence E5).',
     '- 1ha 미만 공원은 위성 칸(1ha) 안에서 섞인 만큼만 반영한 "공원 일대" 저감이다. 공원 안 그늘 같은 체감 효과는 따로 보지 않는다.',
     '- 주변 퍼짐 비율은 숲→개발(가열)에서 잰 값을 조성(냉각)에 쓴 것이고, 비슷한 규모(1ha 이상)에만 적용했다.', '']
open(f'{OUT}/summary.md', 'w', encoding='utf-8').write('\n'.join(L))


# ---------- 지도용 ----------
def decode(s):
    sc = P['coord_scale']; polys = []
    for p in s.split(';'):
        rings = []
        for r in p.split('|'):
            v = list(map(int, r.split(','))); x = y = 0; ring = []
            for i in range(0, len(v), 2):
                x += v[i]; y += v[i + 1]; ring.append([x / sc, y / sc])
            rings.append(ring)
        polys.append(rings)
    return polys


geo = {int(l.split('~')[0]): decode(l.split('~', 1)[1]) for l in open(f'{BIZ}/vworld/parks.txt', encoding='utf-8').read().split('\n') if l}
gu = [{'name': l.split('~')[0], 'poly': decode(l.split('~', 1)[1])} for l in open(f'{BIZ}/vworld/gu.txt', encoding='utf-8').read().split('\n') if l]
for r in rows:
    r['poly'] = geo.get(r['site_id'])
json.dump({'asof': P['asof'], 'change': change, 'city': city, 'coef': COEF, 'target': TARGET, 'factors': {k: list(v) for k, v in FACTORS.items()},
           'base': BASE, 'n_scen': len(SCEN), 'cell_m2': CELL, 'ring_m': P['change']['ring_m'], 'min_ring_park_m2': RING_MIN,
           'min_change': P['change']['min_change'], 'periods': {'before': P['change']['before'], 'after': P['change']['after']},
           'spill_sites': P['spillover']['sites'], 'gu': gu, 'parks': rows},
          open(f'{OUT}/energydata.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('\n'.join(L))
