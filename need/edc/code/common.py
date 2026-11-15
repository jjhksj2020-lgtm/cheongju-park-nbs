"""E·D·C 공통: 공원 40개소 경계(biz/data/vworld/parks.txt, 읽기 전용)를 EPSG:5186으로 바꾸고 유치거리 버퍼를 만든다.
상수(버퍼 반경)는 need/presets.yaml 에서만 읽는다."""
import csv, os
import yaml
from pyproj import Transformer
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import transform

EDC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # need/edc/
NEED = os.path.dirname(EDC)                                         # need/
ROOT = os.path.dirname(NEED)
RAW = f'{EDC}/data/raw'
OUT = f'{NEED}/out'
os.makedirs(OUT, exist_ok=True)

PRESETS = yaml.safe_load(open(f'{NEED}/presets.yaml', encoding='utf-8'))
EDC_P = yaml.safe_load(open(f'{EDC}/code/params.yaml', encoding='utf-8'))

to5186 = Transformer.from_crs('EPSG:4326', 'EPSG:5186', always_xy=True).transform
to4326 = Transformer.from_crs('EPSG:5186', 'EPSG:4326', always_xy=True).transform


def _dec(s):
    """biz/code/build_mapdata.py 와 같은 형식: 정수(경위도×1e5) 누적차분, 다각형 ';', 링 '|'."""
    polys = []
    for p in s.split(';'):
        rings = []
        for r in p.split('|'):
            v = list(map(int, r.split(','))); x = y = 0; ring = []
            for i in range(0, len(v), 2):
                x += v[i]; y += v[i + 1]; ring.append((x / 1e5, y / 1e5))
            rings.append(ring)
        polys.append(Polygon(rings[0], rings[1:]).buffer(0))
    return MultiPolygon([g for p in polys for g in (p.geoms if hasattr(p, 'geoms') else [p])])


def sites():
    return list(csv.DictReader(open(f'{ROOT}/biz/data/input/sites.csv', encoding='utf-8-sig')))


def parks_5186():
    """site_id(str) -> 공원 경계 (EPSG:5186). 경계가 없는 공원(5 어린이공원152)은 빠진다."""
    lines = open(f'{ROOT}/biz/data/vworld/parks.txt', encoding='utf-8').read().split('\n')
    return {l.split('~')[0]: transform(to5186, _dec(l.split('~')[1])) for l in lines if l}


def buffers():
    """site_id -> (공원 경계, 버퍼 = 경계 + 유치거리, 반경 m)."""
    geo = parks_5186(); r = PRESETS['buffer_m']; out = {}
    for s in sites():
        g = geo.get(s['site_id'])
        if g is None:
            continue
        d = r[s['type']]
        out[s['site_id']] = (g, g.buffer(d), d)
    return out


def write_rows(path, rows):
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['site_id', 'indicator', 'value', 'unit', 'source_key', 'tag'])
        w.writeheader(); w.writerows(rows)
