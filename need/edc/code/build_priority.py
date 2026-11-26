"""우선순위 시험판 데이터 → need/out/priority_map.json  (다음: build_priority_page.py)

① 현황·유형  : 정진형 R1-f 유형(조성형/보전형) + 토지피복지도 2025 공원 안 비율, 복원 가능 면적
② 냉각 효과  : 정진형 R1(조성)·R1-h(숲 개발) 실측 계수를 유형·면적 구간별로 적용, 범위 링
③ 수혜 주민  : 범위 안 SGIS 2024 격자 인구, 아동·고령 비율
④ 에너지·탄소: 전력 계수(R3)가 아직 없어 kWh는 미산정. 대신 '열 노출 변화(인·°C) = Σ 구간 인구 × 구간 온도 변화'
계수·범위는 params.yaml priority 에서만 읽는다. 정진형/ 파일은 읽기만 한다.
실행: need/edc/code 에서  python build_priority.py   (build_edc.py를 먼저 실행해 edc_map.json이 있어야 함)
"""
import csv, glob, json, os, struct, sys, zipfile
from shapely.geometry import box
from shapely.ops import transform, unary_union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_edc as be
import landcover
from common import EDC_P, OUT, RAW, ROOT, _dec, parks_5186, sites, to4326, to5186

P = EDC_P['priority']


def landcover_shares(parks):
    """공원마다 {묶음: 면적㎡}. 공원 범위와 겹치는 도형만 읽는다."""
    grp = {str(c): g for g, cs in P['landcover_groups'].items() for c in cs}
    bb = {sid: g.bounds for sid, g in parks.items()}
    allb = unary_union([box(*b) for b in bb.values()])
    out = {sid: {} for sid in parks}
    for f in sorted(glob.glob(f"{RAW}/{EDC_P['landcover']['dir']}/*.zip")):
        with zipfile.ZipFile(f) as z:
            base = [n for n in z.namelist() if n.endswith('.shp')][0][:-4]
            for code, body in landcover._records(z, base):
                x0, y0, x1, y1 = struct.unpack('<4d', body[4:36])
                rb = box(x0, y0, x1, y1)
                if code not in grp or not rb.intersects(allb):
                    continue
                poly = None
                for sid, b in bb.items():
                    if not (x0 > b[2] or x1 < b[0] or y0 > b[3] or y1 < b[1]):
                        poly = poly or landcover._polygon(body)
                        a = poly.intersection(parks[sid]).area
                        if a > 0:
                            out[sid][grp[code]] = out[sid].get(grp[code], 0) + a
    return out


def range_m(ha):
    r = None
    for lo, m in P['range_by_ha']:
        if ha >= lo:
            r = m
    return r


def build_class(ha):
    return 'lt04' if ha < 0.4 else '04_06' if ha < 0.6 else '06_1' if ha < 1 else 'ge1'


def main():
    gu = [l for l in open(f'{ROOT}/biz/data/vworld/gu.txt', encoding='utf-8').read().split('\n') if l]
    be.BBOX = unary_union([_dec(l.split('~')[1]) for l in gu]).bounds
    parks = parks_5186()
    prof = {r['sid']: r for r in csv.DictReader(open(f"{ROOT}/{P['profile_csv']}", encoding='utf-8-sig'))}
    edc = {s['site_id']: s for s in json.load(open(f'{OUT}/edc_map.json', encoding='utf-8'))['sites']}

    print('토지피복 비율 계산 …')
    lc = landcover_shares(parks)
    print('인구 격자 읽기 …')
    pop = be.sgis(); dgeo, dratio, _ = be.dongs(); pop.set_ratio(dgeo, dratio)

    out, geo = [], {}
    for s in sites():
        sid = s['site_id']; pr = prof.get(sid, {}); g = parks.get(sid)
        row = {'site_id': sid, 'name': s['name'], 'type': s['type']}
        if g is None or pr.get('kind') in (None, '', '미산정'):
            row.update(kind=pr.get('kind') or '미산정', status='미산정',
                       note='공원 경계 없음' if g is None else f"{pr.get('land')} · 정진형 R1-f에서 유형 미산정(초대형 기반시설)")
            if g is not None:
                row['ha'] = round(g.area / 1e4, 2)
                geo[sid] = {'park': be._geo(g, 2)}
            out.append(row); continue
        ha = g.area / 1e4
        shares = {k: v / g.area for k, v in lc[sid].items()}
        rest = sum(lc[sid].get(k, 0) for k in P['restorable']) / 1e4
        kind = pr['kind']; rng = range_m(ha)
        if kind == '조성형':
            c = P['build'][build_class(ha)]; t_in, bands, basis = c['in'], c['bands'], c['note']
        else:
            c = P['keep']; t_in, bands, basis = c['in'], c['bands'], c['note']
        # 거리 구간별 인구 × 온도 변화
        prev, pin, expo, bd = 0, 0.0, 0.0, []
        for end, dt in bands:
            e = min(end, rng)
            if e <= prev:
                break
            ring = g.buffer(e).difference(g.buffer(prev) if prev else g)
            n = pop.sum(ring); pin += n; expo += n * dt
            bd.append({'from': prev, 'to': e, 'dt': dt, 'pop': round(n)})
            prev = e
        reach = g.buffer(rng).difference(g)
        vul = pop.ratio(reach)
        e = edc.get(sid, {})
        row.update(status='산정', kind=kind, land=pr['land'], ha=round(ha, 2), ndvi_in=float(pr['ndvi_in']),
                   lc={k: round(v, 3) for k, v in sorted(shares.items(), key=lambda kv: -kv[1])},
                   restorable_ha=round(rest, 2), restorable_share=round(rest * 1e4 / g.area, 3),
                   range_m=rng, t_in=t_in, t_edge=bands[0][1], basis=basis, bands=bd,
                   pop_in_range=round(pin), vulnerable=None if vul is None else round(vul, 3),
                   vulnerable_pop=None if vul is None else round(pin * vul),
                   exposure=round(expo, 1),
                   unserved=e.get('D1_unserved'), new_served=e.get('new_served_pop'),
                   now_in=float(pr['in_all']) if pr['in_all'] else None, now_ext_m=int(pr['ext_m'] or 0),
                   now_profile=[[k[2:].replace('_', '~'), float(v)] for k, v in pr.items() if k.startswith('d_') and v != ''])
        geo[sid] = {'park': be._geo(g, 2), 'reach': be._geo(g.buffer(rng), 4)}
        out.append(row)

    d = {'asof': '2026-11-26', 'sites': out, 'geo': geo,
         'coef': {'build': P['build'], 'keep': P['keep'], 'range_by_ha': P['range_by_ha'],
                  'restorable': P['restorable'], 'ef': P['emission_factor_t_per_mwh']}}
    json.dump(d, open(f'{OUT}/priority_map.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

    ok = [r for r in out if r['status'] == '산정']
    from collections import Counter
    print('산정', len(ok), '/ 40 ·', Counter(r['kind'] for r in ok))
    for r in sorted(ok, key=lambda r: -abs(r['exposure']))[:8]:
        print(f"  {r['name']:<10} {r['kind']} {r['ha']:>6}ha 범위 {r['range_m']}m 인구 {r['pop_in_range']:>5} "
              f"경계밖 {r['t_edge']:+.2f}°C 노출 {r['exposure']:+.0f}인·°C 복원가능 {r['restorable_ha']}ha")
    print('저장:', f'{OUT}/priority_map.json', os.path.getsize(f'{OUT}/priority_map.json') // 1024, 'KB')


if __name__ == '__main__':
    main()
