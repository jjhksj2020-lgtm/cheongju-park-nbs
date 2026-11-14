"""biz/data/vworld/*.txt·csv(V-World 수집분) + biz/out/master_biz.csv(계산 결과) → biz/out/mapdata.json (지도 데이터)
좌표 형식: 정수(경위도×1e5) 누적차분. 다각형 ';', 링 '|' 구분."""
import csv, json, os
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # biz/
V = f'{R}/data/vworld'; M = f'{R}/data/map'; O = f'{R}/out'; os.makedirs(O, exist_ok=True)
def dec(s):
    polys = []
    for p in s.split(';'):
        rings = []
        for r in p.split('|'):
            v = list(map(int, r.split(','))); x = y = 0; ring = []
            for i in range(0, len(v), 2):
                x += v[i]; y += v[i+1]; ring.append([x/1e5, y/1e5])
            if ring[0] != ring[-1]: ring.append(ring[0])
            rings.append(ring)
        polys.append(rings)
    return polys
def cen(polys):
    pts = [p for poly in polys for p in poly[0]]
    return [round(sum(p[0] for p in pts)/len(pts), 5), round(sum(p[1] for p in pts)/len(pts), 5)]
rd = lambda f: list(csv.DictReader(open(f, encoding='utf-8-sig')))
mb = {r['site_id']: r for r in rd(f'{O}/master_biz.csv')}
own = {r['site_id']: r for r in rd(f'{V}/land_own.csv')}
pr = {r['site_id']: r for r in rd(f'{V}/land_price.csv')}
gu = [{'name': l.split('~')[0], 'poly': dec(l.split('~')[1])} for l in open(f'{V}/gu.txt', encoding='utf-8').read().split('\n') if l]
geo = {l.split('~')[0]: dec(l.split('~')[1]) for l in open(f'{V}/parks.txt', encoding='utf-8').read().split('\n') if l}
f = lambda v: float(v) if v not in ('', None) else None
parks = []
for sid, m in mb.items():
    o = own.get(sid, {}); p = pr.get(sid, {})
    poly = geo.get(sid)
    parks.append({'id': int(sid), 'name': m['name'], 'type': m['type'], 'loc': m['location'], 'expiry': int(m['expiry']),
        'area': f(m['area_m2']), 'notice': m['notice_stage'], 'stage': m['stage_base'], 'reasons': m['stage_reasons'],
        'pub': f(o.get('public_share')), 'tag': m['private_share_tag'], 'boundary': o.get('boundary') or '미확인', 'ratio': f(o.get('boundary_ratio')),
        'maxH': f(m['city_max_high_krw']), 'maxL': f(m['city_max_low_krw']), 'minH': f(m['city_min_high_krw']), 'minL': f(m['city_min_low_krw']),
        'comp': f(m['comp_high_krw']), 'cons': f(m['cons_high_krw']), 'special': m['special_ok'] == '1',
        'price': f(p.get('land_price_krw_m2')), 'dae': f(p.get('jimok_dae_m2')), 'urban': f(p.get('urban_private_m2')), 'gb': f(p.get('greenbelt_m2')),
        'poly': poly, 'c': cen(poly) if poly else None})
parcels = []
attr = [l.split('~') for l in open(f'{V}/parcel_attr.txt', encoding='utf-8').read().split('\n') if l]
for l, a in zip([l for l in open(f'{V}/parcels.txt', encoding='utf-8').read().split('\n') if l], attr):
    sid, jb, inm, ow, jm, jg, g = l.split('~')
    assert a[0] == sid and a[1] == jb, (a, sid, jb)
    parcels.append({'s': int(sid), 'jb': jb, 'in': int(inm), 'own': a[2], 'jm': jm, 'jiga': int(a[3]) if a[3] else None,
                    'zone': a[4], 'gb': a[5] == '1', 'use': a[6], 'poly': dec(g)})
import yaml
P = yaml.safe_load(open(f'{R}/code/params.yaml', encoding='utf-8'))
cu = P['compensation_unit_krw_m2']; ku = P['construction_unit_krw_m2']
rule = {'low': cu['low'], 'high': cu['high'], 'rr': cu['land_price_rule']['realization_rate'], 'klow': ku['low'], 'khigh': ku['high']}
bm = json.load(open(f'{M}/img/manifest.json', encoding='utf-8')) if os.path.exists(f'{M}/img/manifest.json') else {}
dem = json.load(open(f'{M}/dem/manifest.json', encoding='utf-8')) if os.path.exists(f'{M}/dem/manifest.json') else {}
json.dump({'dem': dem, 'rule': rule, 'basemap': bm, 'gu': gu, 'parks': parks, 'parcels': parcels, 'asof': '2026-11-13'}, open(f'{O}/mapdata.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(len(parks), len(parcels), os.path.getsize(f'{O}/mapdata.json'))
