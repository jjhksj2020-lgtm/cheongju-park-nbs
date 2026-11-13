"""V-World로 청주 장기미집행 공원 40개소의 토지소유·공시지가 수집

실행(로컬 PC):   pip install requests shapely pandas
                 set VWORLD_KEY=...   (Windows)  /  export VWORLD_KEY=...  (mac·linux)
                 python biz/collect_land.py            # 전체
                 python biz/collect_land.py --site 3   # 한 공원만 (점검용)

순서
 1. 공고 지번 → 좌표            /req/address (getcoord, parcel)
 2. 좌표 주변 공원 폴리곤        /req/data  layer lt_c_upisuq153 (도시계획시설 공원·녹지·광장·유원지)
    → 점을 포함하거나 가장 가까운 폴리곤 1개 선택 (면적 비교로 확인)
 3. 폴리곤 안 필지               /req/data  layer lt_c_landinfobasemap → 겹침 50% 이상만
 4. 필지별 소유구분·면적·공시지가   /ned/data/getPossessionAttr (pnu)
 5. 공원별 합산 → data/land_own.csv, data/land_price.csv, data/parcels.csv

응답 원본은 ../data/raw/vworld/ 에 저장(재실행 시 재사용). 호출 도메인은 api.vworld.kr 하나뿐.
엔드포인트·레이어명 출처: V-World 오픈API 문서, supermi41/park-finder(서울 공원 사유지 매핑, 동일 레이어 사용).
"""
from __future__ import annotations
import os, sys, json, time, csv, math, argparse
import requests
from shapely.geometry import shape, Point
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, '..', 'data', 'raw', 'vworld'); os.makedirs(RAW, exist_ok=True)
KEY = os.environ.get('VWORLD_KEY')
if not KEY:
    sys.exit('환경변수 VWORLD_KEY 가 없습니다. 발급받은 인증키를 넣고 다시 실행하세요.')
DOMAIN = 'localhost'
ADDR_URL = 'https://api.vworld.kr/req/address'
DATA_URL = 'https://api.vworld.kr/req/data'
POSS_URL = 'https://api.vworld.kr/ned/data/getPossessionAttr'
PARK_LAYER = 'lt_c_upisuq153'
PARCEL_LAYER = 'lt_c_landinfobasemap'
PUBLIC = ('국유지', '시,도유지', '시도유지', '군유지', '시유지', '도유지', '구유지')
GU = {'상당구': '청주시 상당구', '서원구': '청주시 서원구', '흥덕구': '청주시 흥덕구', '청원구': '청주시 청원구'}


def cached(name, fn):
    p = os.path.join(RAW, name)
    if os.path.exists(p):
        return json.load(open(p, encoding='utf-8'))
    r = fn()
    json.dump(r, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
    return r


def get(url, params, timeout=60):
    for i in range(3):
        try:
            res = requests.get(url, params=dict(params, key=KEY, domain=DOMAIN), timeout=timeout)
            res.raise_for_status(); return res.json()
        except Exception as e:  # noqa
            time.sleep(1.5 * (i + 1)); err = e
    raise RuntimeError(f'{url} 실패: {err}')


def geocode(address):
    j = get(ADDR_URL, {'service': 'address', 'request': 'getcoord', 'version': '2.0', 'crs': 'epsg:4326',
                       'address': address, 'type': 'parcel', 'format': 'json'}, 30)
    if j['response']['status'] != 'OK':
        return None
    p = j['response']['result']['point']; return float(p['x']), float(p['y'])


def features(layer, box, attr=None, max_pages=100):
    out, page = [], 1
    while page <= max_pages:
        params = {'service': 'data', 'request': 'GetFeature', 'data': layer, 'geomFilter': box, 'size': 1000,
                  'page': page, 'format': 'json', 'crs': 'EPSG:4326', 'geometry': 'true', 'attribute': 'true'}
        if attr: params['attrFilter'] = attr
        j = get(DATA_URL, params)
        if j['response']['status'] != 'OK':
            break
        fs = j['response']['result']['featureCollection']['features']; out += fs
        total = int(j['response']['record']['total'])
        if len(fs) < 1000 or len(out) >= total: break
        page += 1; time.sleep(0.05)
    return out


def possession(pnu):
    j = get(POSS_URL, {'pnu': pnu, 'format': 'json', 'numOfRows': 5, 'pageNo': 1}, 15)
    f = (j.get('possessions') or {}).get('field') or []
    return f[0] if f else {}


def box_around(x, y, area_m2, factor=2.0):
    r = max(150, math.sqrt(area_m2) * factor)            # 반경 m
    dy = r / 111320; dx = r / (111320 * math.cos(math.radians(y)))
    return f'BOX({x-dx},{y-dy},{x+dx},{y+dy})'


def jimok_of(jibun):
    # lt_c_landinfobasemap 의 jibun 은 "23-1 임" 처럼 끝에 지목 약자가 붙는다
    t = (jibun or '').strip().split()
    return t[-1] if len(t) > 1 and not t[-1][0].isdigit() else ''


def run(site):
    sid = int(site['site_id']); area = int(site['area_m2'])
    gu = next((GU[g] for g in GU if g in site['location']), '청주시')
    dong = site['location'].replace('상당구', '').replace('서원구', '').replace('흥덕구', '').replace('청원구', '').strip()
    jb = site['jibun'].split('외')[0].strip()                       # "산 23 외 5필지" → "산 23"
    jb = ' '.join(t for t in jb.split() if t[0].isdigit() or t == '산')
    address = f'충청북도 {gu} {dong} {jb}'
    pt = cached(f'{sid:02d}_geocode.json', lambda: {'address': address, 'xy': geocode(address)})['xy']
    if not pt:
        return dict(site_id=sid, status='지오코딩 실패', address=address)
    x, y = pt
    # 2. 공원 폴리곤
    parks = cached(f'{sid:02d}_parks.json', lambda: features(PARK_LAYER, box_around(x, y, area, 2.5), max_pages=20))
    cand = []
    for f in parks:
        g = shape(f['geometry']); props = f.get('properties', {})
        cand.append((g.contains(Point(x, y)), g.distance(Point(x, y)), g, props))
    if not cand:
        return dict(site_id=sid, status='공원 폴리곤 없음', address=address)
    cand.sort(key=lambda c: (not c[0], c[1]))
    poly, props = cand[0][2], cand[0][3]
    # 면적 비교 (EPSG:4326 → 근사 m²)
    def m2(g):
        cy = g.centroid.y; return g.area * 111320 * 111320 * math.cos(math.radians(cy))
    poly_m2 = m2(poly)
    # 3. 필지
    minx, miny, maxx, maxy = poly.bounds
    parcels = cached(f'{sid:02d}_parcels.json', lambda: features(PARCEL_LAYER, f'BOX({minx},{miny},{maxx},{maxy})'))
    rows = []
    for f in parcels:
        g = shape(f['geometry']); p = f.get('properties', {})
        if g.is_empty or not g.intersects(poly): continue
        ratio = g.intersection(poly).area / g.area if g.area else 0
        if ratio < 0.5: continue
        pnu = p.get('pnu');
        if not pnu: continue
        poss = cached(f'p_{pnu}.json', lambda: possession(pnu)); time.sleep(0.03)
        own = poss.get('posesnSeCodeNm', '') ; a = float(poss.get('lndpclAr') or 0) or m2(g)
        rows.append(dict(site_id=sid, pnu=pnu, jibun=p.get('jibun', ''), jimok=jimok_of(p.get('jibun', '')),
                         overlap=round(ratio, 2), area_m2=round(a, 1), owner=own,
                         owner_sub=poss.get('nationInsttSeCodeNm', ''), price_krw_m2=poss.get('pblntfPclnd', ''),
                         public=int(own.startswith(PUBLIC) or own in PUBLIC)))
    tot = sum(r['area_m2'] for r in rows); pub = sum(r['area_m2'] for r in rows if r['public'])
    priv = [r for r in rows if not r['public'] and r['price_krw_m2']]
    pw = sum(r['area_m2'] * float(r['price_krw_m2']) for r in priv); pa = sum(r['area_m2'] for r in priv)
    dae = sum(r['area_m2'] for r in rows if not r['public'] and r['jimok'] == '대')
    return dict(site_id=sid, status='OK', address=address, park_attr=json.dumps(props, ensure_ascii=False)[:120],
                poly_m2=round(poly_m2), notice_m2=area, area_ratio=round(poly_m2 / area, 2) if area else '',
                n_parcels=len(rows), parcel_m2=round(tot), public_share=round(pub / tot, 3) if tot else '',
                priv_price_krw_m2=round(pw / pa) if pa else '', jimok_dae_m2=round(dae), _rows=rows)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--site', type=int); a = ap.parse_args()
    sites = list(csv.DictReader(open(os.path.join(HERE, 'data', 'sites.csv'), encoding='utf-8-sig')))
    if a.site: sites = [s for s in sites if int(s['site_id']) == a.site]
    results, parcels = [], []
    for s in sites:
        try:
            r = run(s)
        except Exception as e:  # noqa
            r = dict(site_id=s['site_id'], status=f'오류: {e}')
        parcels += r.pop('_rows', []); results.append(r)
        print(f"[{r['site_id']}] {s['name']}: {r['status']} 필지 {r.get('n_parcels','')} 국공유 {r.get('public_share','')} 면적비 {r.get('area_ratio','')}")
    D = os.path.join(HERE, 'data')
    with open(os.path.join(D, 'land_collect_log.csv'), 'w', newline='', encoding='utf-8-sig') as f:
        keys = ['site_id', 'status', 'address', 'poly_m2', 'notice_m2', 'area_ratio', 'n_parcels', 'parcel_m2', 'public_share', 'priv_price_krw_m2', 'jimok_dae_m2', 'park_attr']
        w = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore'); w.writeheader(); w.writerows(results)
    with open(os.path.join(D, 'parcels.csv'), 'w', newline='', encoding='utf-8-sig') as f:
        if parcels:
            w = csv.DictWriter(f, fieldnames=list(parcels[0].keys())); w.writeheader(); w.writerows(parcels)
    ok = [r for r in results if r['status'] == 'OK' and r['public_share'] != '']
    if not a.site:
        with open(os.path.join(D, 'land_own.csv'), 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f); w.writerow(['site_id', 'public_share', 'plan_notice', 'source'])
            for r in ok: w.writerow([r['site_id'], r['public_share'], '', 'VW-upis lt_c_landinfobasemap + getPossessionAttr'])
        with open(os.path.join(D, 'land_price.csv'), 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f); w.writerow(['site_id', 'land_price_krw_m2', 'jimok_dae_m2', 'source'])
            for r in ok: w.writerow([r['site_id'], r['priv_price_krw_m2'], r['jimok_dae_m2'], 'VW getPossessionAttr pblntfPclnd (사유지 면적가중)'])
    print(f'완료: {len(ok)}/{len(results)} 공원. 로그 data/land_collect_log.csv — area_ratio 가 0.7~1.3 밖이면 폴리곤 선택을 확인하세요.')


if __name__ == '__main__':
    main()
