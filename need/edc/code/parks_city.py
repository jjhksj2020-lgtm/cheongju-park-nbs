"""청주시 공식 공원 목록 → D1 '기존 공원'.
- data/raw/parks_city/cheongju_parks_std_20251120.csv : 청주시 도시공원정보(전국도시공원정보표준데이터), 433곳, 위경도·면적
- data/raw/parks_city/cheongju_unbuilt_parks_20260929.csv : 청주시 미조성공원 현황 → '미조성'은 기존 공원에서 뺀다(부분조성은 남긴다)
- 표준데이터 좌표 중 일부는 실제 위치에서 수십 km 어긋나 있다. 주소의 구 경계 밖에 찍힌 좌표는 틀린 것으로 보고
  geocoded_vworld.csv(geocode_parks.py, V-World 주소 검색) 좌표로 바꾼다. 거기서도 못 찾으면 쓰지 않는다.
공원은 점 위치만 있으므로 면적이 같은 원으로 본다(형상 가정)."""
import csv, math, os
from shapely.geometry import Point
from shapely.ops import transform
from common import RAW, ROOT, _dec, to5186

D = f'{RAW}/parks_city'


def _read(name):
    return list(csv.DictReader(open(f'{D}/{name}', encoding='utf-8-sig')))


def _gu():
    L = [l for l in open(f'{ROOT}/biz/data/vworld/gu.txt', encoding='utf-8').read().split('\n') if l]
    return {l.split('~')[0]: transform(to5186, _dec(l.split('~')[1])) for l in L}


def _pt(lon, lat):
    return transform(to5186, Point(float(lon), float(lat)))


def _coord_ok(r, gu):
    addr = r['소재지지번주소'] + r['소재지도로명주소']
    g = [k for k in gu if k in addr]
    return bool(g) and gu[g[0]].buffer(100).contains(_pt(r['경도'], r['위도']))


def std():
    return _read('cheongju_parks_std_20251120.csv')


def unbuilt_names():
    return {r['공원명'].strip() for r in _read('cheongju_unbuilt_parks_20260929.csv') if r['조성여부'].strip() == '미조성'}


def bad_coords():
    gu, ub = _gu(), unbuilt_names()
    return [r for r in std() if r['공원명'].strip() not in ub and not _coord_ok(r, gu)]


def existing():
    """[(공원명, 공원구분, 면적㎡, 원 도형 5186, 위치 출처)] 와 집계."""
    gu, ub = _gu(), unbuilt_names()
    geo = {r['관리번호']: r for r in _read('geocoded_vworld.csv')} if os.path.exists(f'{D}/geocoded_vworld.csv') else {}
    import osm
    O = {}
    for t, g in osm.areas('parks'):
        if t.get('name'):
            O.setdefault(t['name'].replace(' ', ''), []).append(g)
    out, n, miss = [], {'표준데이터': 0, '미조성 제외': 0, '좌표 그대로': 0, 'V-World 주소 검색': 0, 'OSM 같은 이름': 0, '위치 못 찾음': 0}, []
    for r in std():
        n['표준데이터'] += 1
        name = r['공원명'].strip(); a = float(r['공원면적'] or 0)
        if name in ub:
            n['미조성 제외'] += 1; continue
        if _coord_ok(r, gu):
            p, how = _pt(r['경도'], r['위도']), '좌표 그대로'
        elif geo.get(r['관리번호'], {}).get('status') == 'OK':
            p, how = _pt(geo[r['관리번호']]['lon'], geo[r['관리번호']]['lat']), 'V-World 주소 검색'
        elif len(O.get(name.replace(' ', ''), [])) == 1:         # 마지막 수단: OSM에 같은 이름 공원이 하나뿐이면 그 도형
            n['OSM 같은 이름'] += 1
            out.append((name, r['공원구분'].strip(), a, O[name.replace(' ', '')][0], 'OSM 같은 이름')); continue
        else:
            n['위치 못 찾음'] += 1; miss.append(name); continue
        n[how] += 1
        out.append((name, r['공원구분'].strip(), a, p.buffer(math.sqrt(a / math.pi) if a > 0 else 1), how))
    n['못 찾은 공원'] = miss
    return out, n
