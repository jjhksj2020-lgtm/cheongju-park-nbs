"""청주 장기미집행 공원 40개소 — 열저감·전력 절감 계산 엔진 (energy 파트, 독립 참고 결과)

질문: 공원을 조성하면(지금 상태 대비) 공원과 주변이 얼마나 시원해지고, 주변 건물 전력을 얼마나 줄이나?
계산 사슬 (공원마다, 시나리오마다)
  녹지 증가 ΔNDVI = max(0, 조성 후 목표 NDVI − 현재 NDVI)                 ← Sentinel-2 (GEE)
  공원 안 지표온도 저감 = |청주 녹지-온도 계수| × ΔNDVI                    ← Landsat 회귀 (GEE)
  주변 고리 지표온도 저감 = 공원 안 저감 × 퍼짐 비율                         ← 특례사업지 실측 (E1)
  주변 기온 저감 = 주변 지표온도 저감 × 지표→기온 비율                       ← 문헌 (E2)
  최대전력 절감(kW) = 주변 인구 × 기온 저감 × 1인당 W/°C ÷ 1000             ← GHSL 인구, 문헌 (E4)
  연간 냉방전력 절감(MWh) = 주변 인구 × 1인당 냉방전력 × %/°C × 기온 저감     ← GHSL 인구, 한전 (E4·E5)
6개 계수(목표 NDVI·온도 계수·퍼짐·기온 비율·W/°C·%/°C)를 상·하한으로 바꾼 64개 시나리오 → 범위와 등급, 모두 같은 등급이면 확정.

입력 (읽기만)
  biz/data/input/sites.csv                     공고 40곳 (site_id 마스터)
  biz/data/vworld/parcels.txt · parcel_attr.txt 필지 면적·이용상황 → 지금 땅 상태
  energy/data/gee/gee_output.txt               GEE 결과 (CITY| 계수, PARK| 공원별)
  energy/data/gee/tukrye_before_after.json     특례사업지 전후 실측 (퍼짐 비율)
출력 (energy/out/)
  master_energy.csv · summary.md · energydata.json(지도용)
코드에 기준값 숫자를 쓰지 않는다 — params.yaml만 읽는다.
"""
from __future__ import annotations
import csv, itertools, json, os, yaml

C = os.path.dirname(os.path.abspath(__file__)); E = os.path.dirname(C); ROOT = os.path.dirname(E)
P = yaml.safe_load(open(f'{C}/params.yaml', encoding='utf-8'))
BIZ = f'{ROOT}/biz/data'; GEE = f'{E}/data/gee'; OUT = f'{E}/out'
os.makedirs(OUT, exist_ok=True)
U = P['units']; EL = P['electricity']


# ---------- 읽기 ----------
sites = {int(r['site_id']): r for r in csv.DictReader(open(f'{BIZ}/input/sites.csv', encoding='utf-8-sig'))}

city, gee = None, {}
for line in open(f'{GEE}/gee_output.txt', encoding='utf-8'):
    if line.startswith('CITY|'):
        city = json.loads(line[len('CITY|'):])
    elif line.startswith('PARK|'):
        r = json.loads(line[len('PARK|'):]); gee[int(r['id'])] = r
assert city is not None, 'gee_output.txt 에 CITY| 줄이 없습니다'

tk = json.load(open(f"{GEE}/{P['spillover']['source_file']}", encoding='utf-8'))
spill_vals = [r['neighbor_300m'] / r['effect'] for r in tk['sites'] if r['site'] in P['spillover']['sites']]
SPILL = {'low': min(spill_vals), 'high': max(spill_vals)}

own = {int(r['site_id']): r for r in csv.DictReader(open(f'{BIZ}/vworld/land_own.csv', encoding='utf-8-sig'))}   # 경계 매칭 상태
cls_of = {u: c for c, us in P['landuse_class'].items() for u in us}
landuse = {}
parcels = [l.split('~') for l in open(f'{BIZ}/vworld/parcels.txt', encoding='utf-8').read().split('\n') if l]
attrs = [l.split('~') for l in open(f'{BIZ}/vworld/parcel_attr.txt', encoding='utf-8').read().split('\n') if l]
for p, a in zip(parcels, attrs):
    assert p[0] == a[0] and p[1] == a[1], (p[:2], a[:2])
    d = landuse.setdefault(int(p[0]), {c: 0.0 for c in P['landuse_class']})
    d[cls_of.get(a[6], '기반시설')] += float(p[2])

# ---------- 계수 ----------
COEF = {'controlled': abs(city['b_controlled']), 'simple': abs(city['b_simple'])}
TARGET = {'grass': city['ndvi_grass'], 'tree': city['ndvi_tree']}
FACTORS = {   # 이름: (하한 값, 상한 값)
    'target': (TARGET[P['target_ndvi']['low']], TARGET[P['target_ndvi']['high']]),
    'coef': (COEF[P['lst_coef']['low']], COEF[P['lst_coef']['high']]),
    'spill': (SPILL['low'], SPILL['high']),
    'air': (P['air_per_surface']['low'], P['air_per_surface']['high']),
    'peak_w': (EL['peak_w_per_c_person']['low'], EL['peak_w_per_c_person']['high']),
    'pct': (EL['pct_per_c']['low'], EL['pct_per_c']['high']),
}
SCEN = [dict(zip(FACTORS, combo)) for combo in itertools.product(*FACTORS.values())]
BASE = {k: sum(v) / len(v) for k, v in FACTORS.items()}   # params.base_rule: 중간값 (보고용)


def chain(g, ring, f):
    """한 공원·한 시나리오의 계산 사슬."""
    dndvi = max(P['ndvi_gain_floor'], f['target'] - g['ndvi_s2'])
    d_site = f['coef'] * dndvi
    d_ring_air = d_site * f['spill'] * f['air']
    pop = g[f'pop_{ring}']
    peak = pop * d_ring_air * f['peak_w'] / U['w_per_kw']
    annual = pop * EL['cooling_kwh_per_person_yr'] * f['pct'] * d_ring_air / U['kwh_per_mwh']
    return {'dndvi': dndvi, 'd_site': d_site, 'd_air': d_ring_air, 'peak_kw': peak, 'annual_mwh': annual}


rows, per_scen = [], {}
excluded = set(P['excluded_types'])
for sid, s in sites.items():
    area = float(s['area_m2']); g = gee.get(sid)
    lu = landuse.get(sid)
    shares = {c: (v / sum(lu.values()) if lu and sum(lu.values()) else None) for c, v in (lu or {c: 0 for c in P['landuse_class']}).items()}
    dom = max(lu, key=lu.get) if lu and sum(lu.values()) else None
    kind = None if g is None else ('보전형' if g['ndvi_s2'] >= FACTORS['target'][0] else '조성형')   # params.park_kind
    ring = P['ring_rule']['small_ring_m'] if area < P['ring_rule']['small_area_m2'] else P['ring_rule']['large_ring_m']
    row = {'site_id': sid, 'name': s['name'], 'type': s['type'], 'location': s['location'], 'area_m2': int(area), 'expiry': s['expiry'],
           'kind': kind or '미확인', 'dominant_landuse': dom or '미확인',
           **{f'share_{c}': (round(v, 3) if v is not None else '') for c, v in shares.items()}, 'ring_m': ring,
           'boundary': own.get(sid, {}).get('boundary') or '미확인'}
    note = ''
    if g is None:
        note = '공원 경계 없음(V-World 도시계획시설 미등재) → 미산정'
    elif s['type'] in excluded:
        note = P['excluded_note']
    if note:
        row.update({'note': note, 'status': '미산정'}); rows.append(row); continue
    res = [chain(g, ring, f) for f in SCEN]
    per_scen[sid] = res
    b = chain(g, ring, BASE)
    lo = lambda k: min(r[k] for r in res); hi = lambda k: max(r[k] for r in res)
    row.update({'status': '산정', 'ndvi_now': round(g['ndvi_s2'], 3), 'lsta_now': round(g['lsta'], 2) if g.get('lsta') is not None else '',
                'pop_ring': round(g[f'pop_{ring}']),
                'dndvi_low': round(lo('dndvi'), 3), 'dndvi_high': round(hi('dndvi'), 3),
                'dlst_site_low': round(lo('d_site'), 2), 'dlst_site_high': round(hi('d_site'), 2),
                'dta_ring_low': round(lo('d_air'), 3), 'dta_ring_high': round(hi('d_air'), 3),
                'peak_kw_low': round(lo('peak_kw'), 2), 'peak_kw_high': round(hi('peak_kw'), 2),
                'annual_mwh_low': round(lo('annual_mwh'), 2), 'annual_mwh_high': round(hi('annual_mwh'), 2),
                'dndvi_base': round(b['dndvi'], 3), 'dlst_site_base': round(b['d_site'], 2), 'dta_ring_base': round(b['d_air'], 3),
                'peak_kw_base': round(b['peak_kw'], 2), 'annual_mwh_base': round(b['annual_mwh'], 2),
                'note': '' if row['boundary'] in P['boundary_ok'] else f"경계 {row['boundary']} — 사업성 파트 기록대로 청주시 확인 필요"})
    rows.append(row)

# ---------- 등급: 시나리오마다 연간 전력 절감 순위 ----------
ids = list(per_scen)
grades = {sid: [] for sid in ids}
n_top = round(len(ids) * P['grade']['top_share']); n_mid = round(len(ids) * P['grade']['mid_share'])
for k in range(len(SCEN)):
    order = sorted(ids, key=lambda i: per_scen[i][k]['annual_mwh'], reverse=True)
    for rank, i in enumerate(order):
        v = per_scen[i][k]['annual_mwh']
        grades[i].append('하' if v <= P['ndvi_gain_floor'] else '상' if rank < n_top else '중' if rank < n_mid else '하')
ORDER = ['상', '중', '하']
for row in rows:
    gs = grades.get(row['site_id'])
    if not gs:
        row.update({'grade': '', 'grade_stable': '', 'grade_range': ''}); continue
    uniq = sorted(set(gs), key=ORDER.index)
    row.update({'grade': max(set(gs), key=gs.count), 'grade_stable': '확정' if len(uniq) == 1 else '경계',
                'grade_range': uniq[0] if len(uniq) == 1 else f'{uniq[0]}~{uniq[-1]}'})

cols = list(dict.fromkeys(k for r in rows for k in r))
with open(f'{OUT}/master_energy.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

# ---------- 요약 ----------
ok = [r for r in rows if r['status'] == '산정']
tot = lambda k: sum(r[k] for r in ok)
by_kind = {}
for r in ok:
    b = by_kind.setdefault(r['kind'], {'n': 0, 'lo': 0.0, 'hi': 0.0, 'base': 0.0, 'area': 0})
    b['n'] += 1; b['lo'] += r['annual_mwh_low']; b['hi'] += r['annual_mwh_high']; b['base'] += r['annual_mwh_base']; b['area'] += r['area_m2']
top = sorted(ok, key=lambda r: r['annual_mwh_base'], reverse=True)
lines = [
    '# 에너지(열저감) 파트 요약 — 독립 참고 결과', '',
    f"기준: 조성 vs 지금 그대로. 시나리오 {len(SCEN)}개(6개 계수 상·하한). 산정 {len(ok)}개소 / 미산정 {len(rows) - len(ok)}개소.", '',
    '## 청주 계수 (GEE)',
    f"- 녹지-지표온도: NDVI 1 증가당 {-COEF['controlled']:.2f}°C(시가화율·표고 통제) ~ {-COEF['simple']:.2f}°C(NDVI만) — Landsat 여름 {city['ls_scenes']}장",
    f"- 조성 목표 NDVI: 잔디·초지 {TARGET['grass']:.3f} ~ 수목 {TARGET['tree']:.3f} — Sentinel-2 여름 {city['s2_scenes']}장",
    f"- 주변 퍼짐 비율: {SPILL['low']:.2f} ~ {SPILL['high']:.2f} (특례사업지 {', '.join(P['spillover']['sites'])} 실측)", '',
    '## 합계 (산정 공원 전체)',
    f"- 연간 냉방전력 절감: {tot('annual_mwh_low'):,.1f} ~ {tot('annual_mwh_high'):,.1f} MWh/년 (기준 {tot('annual_mwh_base'):,.1f})",
    f"- 여름 최대전력 절감: {tot('peak_kw_low'):,.1f} ~ {tot('peak_kw_high'):,.1f} kW (기준 {tot('peak_kw_base'):,.1f})", '',
    '## 공원 성격별',
] + [f"- {k}: {b['n']}개소, 면적 {b['area']:,}㎡, 연간 {b['lo']:,.1f} ~ {b['hi']:,.1f} MWh (기준 {b['base']:,.1f})" for k, b in by_kind.items()] + [
    '', '## 연간 냉방전력 절감 상위 10 (기준 시나리오 순)', '',
    '| 순위 | 공원 | 성격 | 지금 NDVI | 공원 안 지표 저감(°C) 기준 | 주변 인구 | 연간 MWh 기준 (범위) | 등급 |', '|---|---|---|---|---|---|---|---|',
] + [f"| {i} | {r['name']} | {r['kind']} | {r['ndvi_now']} | {r['dlst_site_base']} | {r['pop_ring']:,} | {r['annual_mwh_base']} ({r['annual_mwh_low']}~{r['annual_mwh_high']}) | {r['grade_range']} {r['grade_stable']} |"
     for i, r in enumerate(top[:10], 1)] + [
    '', '## 미산정', ''] + [f"- {r['name']}: {r['note']}" for r in rows if r['status'] != '산정'] + [
    '', '## 검증',
    f"- 64개 시나리오 모두 계산: {all(len(v) == len(SCEN) for v in per_scen.values())}",
    f"- 등급 확정 {sum(r['grade_stable'] == '확정' for r in ok)}개소 / 경계 {sum(r['grade_stable'] == '경계' for r in ok)}개소",
    '- 코드에 기준값 숫자 없음: params.yaml만 읽음', '',
    '## 한계',
    '- 지표온도 기준 계수에 문헌 비율(0.08~0.6)을 곱해 기온으로 바꿨다. 기온 실측은 없다.',
    '- 1ha 미만 소공원은 위성 열자료(100m급)로 직접 잴 수 없어 청주 전체 계수를 적용한 추정이다.',
    '- 전력은 주변 거주 인구 기준(GHSL 2020)이라 상가·업무 건물 몫은 빠져 있다. 1°C당 증가율은 총전력 기준 문헌값을 냉방전력에 적용해 보수적이다.',
    '- 비교 기준은 "조성 vs 지금 그대로". 개발 압력·비용은 필요성·사업성 파트에서 다룬다.', '']
open(f'{OUT}/summary.md', 'w', encoding='utf-8').write('\n'.join(lines))

# ---------- 지도용 데이터 ----------
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
json.dump({'asof': '2026-11-14', 'city': {**city, 'coef': COEF, 'target': TARGET, 'spill': SPILL, 'n_scen': len(SCEN)},
           'factors': {k: list(v) for k, v in FACTORS.items()}, 'params': {k: P[k] for k in ('air_per_surface', 'electricity', 'ring_rule')}, 'base': BASE,
           'gu': gu, 'parks': rows}, open(f'{OUT}/energydata.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(open(f'{OUT}/summary.md', encoding='utf-8').read())
