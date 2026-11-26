"""열 핫스팟 정리 → need/out/hotspot_map.json  (build_priority_page.py가 함께 읽는다)

① 생활권 순위  P = 0.5·D + 0.5·E
   D(수요, 0~100) = 평균(공원 부족 = (법정 6㎡ − 1인당 조성면적)/6㎡, 서비스권 밖 인구 비율)   ← 지금 자료로 계산
   E(환경, 0~100) = 평균((ndvi_ref − NDVI)/ndvi_span, (LST − lst_ref)/lst_span), 0~1로 자름   ← GEE 결과 필요
② 핫스팟 픽셀 등급, ④ 공원 경계+150m 안 등급 2·3 면적 비율 → 공원 핫스팟 등급(params hot_share_levels)                                                   ← GEE 결과 필요
③ 공원 공백 등급 = D1(서비스권 밖 인구 비율) 구간                                            ← 지금 자료로 계산
★ 최우선 = 핫스팟 등급 ≥ 2 ∧ 공백 등급 ≥ 2
GEE 결과: data/raw/hotspot/cheongju_hotspot_sites*.csv, cheongju_hotspot_grade*.tif (gee/hotspot_gee.js 실행 후 Drive에서 받음).
없으면 GEE 칸은 '미산정'으로 둔다.
"""
import csv, glob, json, os, sys
from shapely.ops import transform, unary_union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_edc as be
from build_hotspot_gee import zones_5186
from common import EDC_P, OUT, RAW, ROOT, _dec, buffers, to5186

H = EDC_P['hotspot']; LZ = EDC_P['living_zone_park']
clip = lambda v: max(0.0, min(1.0, v))


def gee_sites():
    f = sorted(glob.glob(f'{RAW}/hotspot/cheongju_hotspot_sites*.csv'))
    return list(csv.DictReader(open(f[-1], encoding='utf-8-sig'))) if f else None


def grade_polys():
    """등급 GeoTIFF → 등급별 다각형(4326). 화면용으로 단순화."""
    f = sorted(glob.glob(f'{RAW}/hotspot/cheongju_hotspot_grade*.tif'))
    if not f:
        return None
    import rasterio
    from rasterio.features import shapes
    from shapely.geometry import shape
    with rasterio.open(f[-1]) as r:
        a = r.read(1); t = r.transform
    out = {}
    for geom, v in shapes(a, mask=a > 0, transform=t):
        out.setdefault(int(v), []).append(shape(geom))
    return {g: be._geo(transform(to5186, unary_union(v)), 15) for g, v in out.items()}   # 4326 → 5186에서 15m 단순화


def main():
    gu = [l for l in open(f'{ROOT}/biz/data/vworld/gu.txt', encoding='utf-8').read().split('\n') if l]
    be.BBOX = unary_union([_dec(l.split('~')[1]) for l in gu]).bounds
    B = buffers()
    pop = be.sgis()
    _, served, _ = be.existing_service(g for g, _, _ in B.values())
    zones = zones_5186()
    G = gee_sites(); gz = {r['id']: r for r in G if r['kind'] == 'zone'} if G else {}
    gp = {r['id']: r for r in G if r['kind'] == 'park'} if G else {}

    Z = []
    for k, g in zones.items():
        tot = pop.sum(g); uns = pop.sum(g.difference(served)) / tot if tot else None
        lack = clip((H['park_std_m2_per_cap'] - LZ['per_cap_built'][k]) / H['park_std_m2_per_cap'])
        D = 100 * (lack + uns) / 2
        z = {'zone': k, 'pop': round(tot), 'per_cap_built': LZ['per_cap_built'][k], 'park_lack': round(lack, 3),
             'unserved': round(uns, 3), 'D': round(D, 1), 'geo': be._geo(g, 30)}
        if k in gz:
            r = gz[k]; nd, ls = float(r['ndvi_mean']), float(r['lst_mean'])
            E = 100 * (clip((H['ndvi_ref'] - nd) / H['ndvi_span']) + clip((ls - H['lst_ref']) / H['lst_span'])) / 2
            z.update(ndvi=round(nd, 3), lst=round(ls, 2), E=round(E, 1), P=round(0.5 * D + 0.5 * E, 1))
        Z.append(z)
    Z.sort(key=lambda z: -(z.get('P') if 'P' in z else z['D']))

    edc = {s['site_id']: s for s in json.load(open(f'{OUT}/edc_map.json', encoding='utf-8'))['sites']}
    lv = H['gap_levels']; T = H['top']
    S = {}
    for sid, e in edc.items():
        d1 = e.get('D1_unserved')
        gap = None if d1 is None else sum(d1 >= x for x in lv)
        s = {'unserved': d1, 'gap': gap}
        r = gp.get(sid)
        if r and r.get('grade_max') not in (None, ''):
            gmax = int(float(r['grade_max'])); sh = float(r['hot2_share'] or 0)
            gr = 0 if sh <= 0 else 1 + sum(sh >= x for x in H['hot_share_levels'])   # 면적 비율 기준 등급
            s.update(grade=gr, grade_max=gmax, comb=round(float(r['comb_mean']), 3), lst=round(float(r['lst_mean']), 2),
                     ndvi=round(float(r['ndvi_mean']), 3), urban_share=round(float(r['urban_share']), 3),
                     hot2_share=round(sh, 3),
                     )
        S[sid] = s

    # 민감도: 핫스팟 면적 비율 기준별 '핫스팟 ∧ 공백 2등급' 공원 (+ 인천 최고 1칸 규칙)
    sens = []
    if G:
        g2 = [k for k, v in S.items() if (v['gap'] or 0) >= T['gap_min'] and 'hot2_share' in v]
        sens.append({'rule': '인천(경계+150m 최고 1칸 등급 ≥ 2)', 'ids': [k for k in g2 if S[k]['grade_max'] >= T['grade_min']]})
        for t in H['sensitivity_shares']:
            sens.append({'rule': f'등급 2·3 면적 ≥ {round(t * 100)}%', 'share': t, 'ids': [k for k in g2 if S[k]['hot2_share'] >= t]})
    meta = {'gee': G is not None, 'params': {k: H[k] for k in ('years', 'months', 'ndvi_ref', 'ndvi_span', 'lst_ref', 'lst_span',
                                                            'percentiles', 'sample_buffer_m', 'hot_share_levels', 'gap_levels', 'top', 'sensitivity_shares', 'park_std_m2_per_cap')}}
    if G:
        r0 = G[0]; meta.update(p70=float(r0['p70']), p80=float(r0['p80']), p90=float(r0['p90']), nscene=int(float(r0['nscene'])))
    d = {'meta': meta, 'zones': Z, 'sites': S, 'sens': sens, 'grade_geo': grade_polys()}
    json.dump(d, open(f'{OUT}/hotspot_map.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('GEE 결과', '있음' if G else '없음 → 핫스팟 등급·E·P 미산정')
    for z in Z:
        print(f"  {z['zone']:<6} D {z['D']:>5} (공원부족 {z['park_lack']}, 서비스권 밖 {z['unserved']})", f"E {z.get('E')} P {z.get('P')}" if 'P' in z else '')
    from collections import Counter
    print('공백 등급', Counter(s['gap'] for s in S.values()))
    for r in sens:
        print(f"  {r['rule']}: {len(r['ids'])}곳", [edc[k]['name'] for k in r['ids']])
    print('저장:', f'{OUT}/hotspot_map.json', os.path.getsize(f'{OUT}/hotspot_map.json') // 1024, 'KB')


if __name__ == '__main__':
    main()
