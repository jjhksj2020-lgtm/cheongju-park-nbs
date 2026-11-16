"""data/raw/osm/*.json (Overpass 'out geom') → shapely 도형 (EPSG:5186)."""
import json
from shapely.geometry import LineString, Polygon
from shapely.ops import linemerge, polygonize, transform, unary_union
from common import RAW, to5186


def _load(name):
    return json.load(open(f'{RAW}/osm/{name}.json', encoding='utf-8'))['elements']


def _line(geom):
    return LineString([(p['lon'], p['lat']) for p in geom])


def _area(el):
    """닫힌 way 또는 multipolygon relation → Polygon/MultiPolygon (경위도). 실패하면 None."""
    if el['type'] == 'way':
        pts = [(p['lon'], p['lat']) for p in el.get('geometry', [])]
        if len(pts) < 4 or pts[0] != pts[-1]:
            return None
        return Polygon(pts).buffer(0)
    outer = [_line(m['geometry']) for m in el.get('members', []) if m.get('role') == 'outer' and m.get('geometry')]
    inner = [_line(m['geometry']) for m in el.get('members', []) if m.get('role') == 'inner' and m.get('geometry')]
    if not outer:
        return None
    o = unary_union(list(polygonize(linemerge(outer))))
    if inner:
        o = o.difference(unary_union(list(polygonize(linemerge(inner)))))
    return o.buffer(0) if not o.is_empty else None


def areas(name):
    """[(tags, 도형 5186)]"""
    out = []
    for el in _load(name):
        g = _area(el)
        if g is not None and not g.is_empty:
            out.append((el.get('tags', {}), transform(to5186, g)))
    return out


def waterways():
    return [(el.get('tags', {}), transform(to5186, _line(el['geometry']))) for el in _load('waterways') if el.get('geometry')]
