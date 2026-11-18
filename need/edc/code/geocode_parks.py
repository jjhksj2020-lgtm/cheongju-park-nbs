"""청주시 도시공원정보(표준데이터)의 좌표가 틀린 공원을 V-World 주소 검색(지번 → 좌표)으로 다시 찾는다.
결과는 data/raw/parks_city/geocoded_vworld.csv 에 남긴다(키는 들어가지 않음). 이미 찾은 관리번호는 다시 묻지 않는다.

인증키: 저장소 맨 위 .env 파일(커밋 안 됨)에  VWORLD_KEY=키  한 줄. 팀 개발키는 도메인 localhost.
실행: need/edc/code 에서  python geocode_parks.py
"""
import csv, json, os, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import RAW, ROOT
import parks_city

OUTF = f'{RAW}/parks_city/geocoded_vworld.csv'
API = 'https://api.vworld.kr/req/address'


def key():
    k = os.environ.get('VWORLD_KEY')
    if not k and os.path.exists(f'{ROOT}/.env'):
        for l in open(f'{ROOT}/.env', encoding='utf-8'):
            if l.strip().startswith('VWORLD_KEY='):
                k = l.split('=', 1)[1].strip().strip('"\'')
    if not k or k.startswith('여기에'):
        sys.exit(f'{ROOT}/.env 에 VWORLD_KEY=인증키 를 넣으세요')
    return k


def getcoord(addr, typ, k):
    q = {'service': 'address', 'request': 'getcoord', 'version': '2.0', 'crs': 'epsg:4326', 'address': addr,
         'refine': 'true', 'simple': 'false', 'format': 'json', 'type': typ, 'key': k, 'domain': 'localhost'}
    with urllib.request.urlopen(f'{API}?{urllib.parse.urlencode(q)}', timeout=20) as r:
        d = json.load(r)['response']
    if d.get('status') == 'OK':
        p = d['result']['point']; return float(p['x']), float(p['y']), d['refined']['text']
    if d.get('status') == 'ERROR':
        raise RuntimeError(d.get('error'))
    return None


def variants(addr):
    """옛 주소를 지금 주소로 고친 후보들. 2014 통합·분구와 읍 승격으로 바뀐 이름, 붙어 쓴 번지를 고친다."""
    import re
    a = addr.strip()
    for old, new in [('오창면', '오창읍'), ('강외면', '오송읍'), ('주중동1024', '주중동 1024')]:
        a = a.replace(old, new)
    out = [a]
    for d in ('모충동', '사창동', '성화동', '수곡동', '분평동', '산남동', '개신동'):   # 2014 흥덕구 → 서원구로 옮긴 동
        if d in a and '흥덕구' in a:
            out.append(a.replace('흥덕구', '서원구'))
    m = re.search(r'(\d{6,})$', a)                                                   # 766767 → 766 (붙어 쓴 두 번지)
    if m:
        out.append(a[:m.start()] + m.group(1)[:len(m.group(1)) // 2])
    return list(dict.fromkeys(out))


def main():
    k = key()
    done = {r['관리번호']: r for r in csv.DictReader(open(OUTF, encoding='utf-8-sig'))} if os.path.exists(OUTF) else {}
    todo = [r for r in parks_city.bad_coords() if r['관리번호'] not in done or done[r['관리번호']]['status'] != 'OK']
    print('다시 찾을 공원', len(todo))
    for i, r in enumerate(todo):
        res, how = None, ''
        cands = [(v, 'parcel') for v in variants(r['소재지지번주소']) if v] + [(r['소재지도로명주소'].strip(), 'road')]
        for addr, typ in cands:
            if addr:
                res = getcoord(addr, typ, k); how = typ
                time.sleep(0.2)
                if res:
                    break
        done[r['관리번호']] = {'관리번호': r['관리번호'], '공원명': r['공원명'], '주소': r['소재지지번주소'] or r['소재지도로명주소'],
                            'lon': res[0] if res else '', 'lat': res[1] if res else '', 'matched': res[2] if res else '',
                            'type': how if res else '', 'status': 'OK' if res else 'NOT_FOUND'}
        if i % 20 == 0:
            print(i, r['공원명'], done[r['관리번호']]['status'])
    with open(OUTF, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['관리번호', '공원명', '주소', 'lon', 'lat', 'matched', 'type', 'status'])
        w.writeheader(); w.writerows(done.values())
    print('저장', OUTF, '/ 찾음', sum(v['status'] == 'OK' for v in done.values()), '/ 못 찾음', sum(v['status'] != 'OK' for v in done.values()))


if __name__ == '__main__':
    main()
