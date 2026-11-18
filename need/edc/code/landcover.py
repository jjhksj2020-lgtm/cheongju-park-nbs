"""환경부 토지피복지도(중분류, 1:25,000) 읽기 — data/raw/egis/SG04_*.zip (받은 파일 그대로).
shp 좌표계는 EPSG:5186(Korea 2000 Central Belt 2010)이라 변환하지 않는다. 속성은 L2_CODE(분류 코드)만 쓴다.
외부 라이브러리 없이 shp/dbf를 직접 읽는다(Polygon, shape type 5)."""
import glob, struct, zipfile
from shapely.geometry import LinearRing, Polygon
from shapely.ops import unary_union
from common import EDC_P, RAW


def _records(z, base):
    dbf = z.read(base + '.dbf'); shp = z.read(base + '.shp')
    nrec, hlen, rlen = struct.unpack('<IHH', dbf[4:12])
    o, r = 100, 0
    while o < len(shp) and r < nrec:
        _, clen = struct.unpack('>ii', shp[o:o + 8]); body = shp[o + 8:o + 8 + clen * 2]; o += 8 + clen * 2
        code = dbf[hlen + r * rlen + 1:hlen + r * rlen + 4].decode('ascii'); r += 1
        if struct.unpack('<i', body[:4])[0] != 5:
            continue
        yield code, body


def _polygon(body):
    nparts, npts = struct.unpack('<ii', body[36:44])
    parts = list(struct.unpack(f'<{nparts}i', body[44:44 + 4 * nparts])) + [npts]
    xy = struct.unpack(f'<{2 * npts}d', body[44 + 4 * nparts:44 + 4 * nparts + 16 * npts])
    pts = list(zip(xy[0::2], xy[1::2]))
    outers, holes = [], []
    for a, b in zip(parts[:-1], parts[1:]):
        ring = pts[a:b]
        if len(ring) < 4:
            continue
        (holes if LinearRing(ring).is_ccw else outers).append(ring)   # shp: 바깥 고리는 시계방향
    polys = []
    for ring in outers:
        p = Polygon(ring)
        polys.append(Polygon(ring, [h for h in holes if p.contains(Polygon(h).representative_point())]))
    return unary_union([p if p.is_valid else p.buffer(0) for p in polys])


def classes(groups):
    """groups = {이름: [코드, ...]} → {이름: 합친 도형(5186)}. 도엽 경계에서 잘린 조각도 합쳐진다."""
    want = {c: k for k, cs in groups.items() for c in map(str, cs)}
    out = {k: [] for k in groups}
    for f in sorted(glob.glob(f"{RAW}/{EDC_P['landcover']['dir']}/*.zip")):
        with zipfile.ZipFile(f) as z:
            base = [n for n in z.namelist() if n.endswith('.shp')][0][:-4]
            for code, body in _records(z, base):
                if code in want:
                    out[want[code]].append(_polygon(body))
    return {k: unary_union(v) for k, v in out.items()}
