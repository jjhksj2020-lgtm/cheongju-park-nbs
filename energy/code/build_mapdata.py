"""energy/out/master_energy.csv(계산 결과) + biz/data/vworld·map(경계·필지·위성사진·지형, 읽기만) → energy/out/mapdata.json (지도 데이터)
사업성 지도(biz/사업성_지도.html)와 같은 형식·같은 배경 자료를 쓴다.
순서: energy_engine.py → build_mapdata.py → build_page.py"""
import csv, json, os, yaml
C = os.path.dirname(os.path.abspath(__file__)); E = os.path.dirname(C); ROOT = os.path.dirname(E)
V = f'{ROOT}/biz/data/vworld'; M = f'{ROOT}/biz/data/map'; O = f'{E}/out'
P = yaml.safe_load(open(f'{C}/params.yaml', encoding='utf-8'))
SC = P['coord_scale']


def dec(s):
    polys = []
    for p in s.split(';'):
        rings = []
        for r in p.split('|'):
            v = list(map(int, r.split(','))); x = y = 0; ring = []
            for i in range(0, len(v), 2):
                x += v[i]; y += v[i + 1]; ring.append([x / SC, y / SC])
            if ring[0] != ring[-1]:
                ring.append(ring[0])
            rings.append(ring)
        polys.append(rings)
    return polys


def cen(polys):
    pts = [p for poly in polys for p in poly[0]]
    return [sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)]


num = lambda v: float(v) if v not in ('', None) else None
gu = [{'name': l.split('~')[0], 'poly': dec(l.split('~')[1])} for l in open(f'{V}/gu.txt', encoding='utf-8').read().split('\n') if l]
geo = {int(l.split('~')[0]): dec(l.split('~')[1]) for l in open(f'{V}/parks.txt', encoding='utf-8').read().split('\n') if l}
TEXT = {'name', 'type', 'location', 'kind', 'dominant_landuse', 'boundary', 'status', 'ring_applied', 'note', 'grade', 'grade_stable', 'grade_range', 'expiry'}
parks = []
for r in csv.DictReader(open(f'{O}/master_energy.csv', encoding='utf-8-sig')):
    sid = int(r['site_id']); poly = geo.get(sid)
    d = {k: (v if k in TEXT else num(v)) for k, v in r.items() if k != 'site_id'}
    d.update({'id': sid, 'poly': poly, 'c': cen(poly) if poly else None})
    parks.append(d)
parcels = []
attr = [l.split('~') for l in open(f'{V}/parcel_attr.txt', encoding='utf-8').read().split('\n') if l]
for l, a in zip([l for l in open(f'{V}/parcels.txt', encoding='utf-8').read().split('\n') if l], attr):
    sid, jb, inm, ow, jm, jg, g = l.split('~')
    assert a[0] == sid and a[1] == jb, (a, sid, jb)
    parcels.append({'s': int(sid), 'jb': jb, 'in': int(inm), 'jm': jm, 'use': a[6], 'poly': dec(g)})
ed = json.load(open(f'{O}/energydata.json', encoding='utf-8'))
bm = json.load(open(f'{M}/img/manifest.json', encoding='utf-8')) if os.path.exists(f'{M}/img/manifest.json') else {}
dem = json.load(open(f'{M}/dem/manifest.json', encoding='utf-8')) if os.path.exists(f'{M}/dem/manifest.json') else {}
meta = {k: ed[k] for k in ('asof', 'change', 'city', 'coef', 'target', 'factors', 'base', 'n_scen', 'cell_m2', 'ring_m', 'min_ring_park_m2', 'min_change', 'periods', 'spill_sites')}
json.dump({**meta, 'landuse_class': P['landuse_class'], 'dem': dem, 'basemap': bm, 'gu': gu, 'parks': parks, 'parcels': parcels},
          open(f'{O}/mapdata.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('energy/out/mapdata.json', len(parks), '공원', len(parcels), '필지')
