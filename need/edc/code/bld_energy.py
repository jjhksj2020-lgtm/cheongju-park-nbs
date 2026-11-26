"""청주 아파트(200세대 이상) 단지별 월 전기 사용량 → 세대당 냉방 전력 계수
1) V-World 법정동·리 경계 속성 → 청주 법정동코드 목록
2) 건축HUB 건축물대장 표제부(getBrTitleInfo) → 주용도 아파트, 지번별 세대수 합 (≥ min_hhld)
3) 건축HUB 건물에너지(getBeElctyUsgInfo) → 지번별 월 전기 사용량
4) 청주 ASOS 월 냉방도일과 회귀 → CDD 100당 세대 월 전력 증가(kWh)
키: 저장소 .env 의 VWORLD_KEY, BLD_ENERGY_KEY (화면·파일에 남기지 않음). 받은 원자료는 data/raw/building_energy/ 에 캐시.
실행: need/edc/code 에서  python bld_energy.py [codes|titles|energy|fit]"""
import json, os, sys, time, urllib.parse, urllib.request
from common import EDC_P, OUT, RAW, ROOT

B = EDC_P['priority']['energy']['bld']
D = f'{RAW}/building_energy'; os.makedirs(D, exist_ok=True)
ENV = {l.split('=', 1)[0]: l.split('=', 1)[1].strip() for l in open(f'{ROOT}/.env', encoding='utf-8') if '=' in l}


def get(url, params, key):
    q = url + '?serviceKey=' + urllib.parse.quote(ENV[key], safe='') + '&' + urllib.parse.urlencode(params)
    for i in range(8):
        try:
            r = json.loads(urllib.request.urlopen(q, timeout=40).read().decode('utf-8'))
            time.sleep(B.get('pause_s', 0.2))
            return r
        except Exception as e:
            err = str(e).replace(ENV[key], '<KEY>')
            time.sleep((15 if '429' in err else 3) * (i + 1))   # 너무 많은 요청(429)이면 길게 쉬고 다시
    raise RuntimeError(err)


def codes():
    out = []
    for layer, f, fld in [('LT_C_ADEMD_INFO', 'emd_cd:like:4311', 'emd_cd'), ('LT_C_ADRI_INFO', 'li_cd:like:4311', 'li_cd')]:
        p = dict(service='data', request='GetFeature', data=layer, key=ENV['VWORLD_KEY'], domain='localhost', attrFilter=f,
                 geometry='false', attribute='true', size='1000', page='1', format='json')
        d = json.loads(urllib.request.urlopen('https://api.vworld.kr/req/data?' + urllib.parse.urlencode(p), timeout=40).read().decode())
        for ft in d['response']['result']['featureCollection']['features']:
            c = ft['properties'][fld]; nm = ft['properties']['full_nm']
            if fld == 'emd_cd':
                if nm.endswith(('읍', '면')):
                    continue                      # 읍면은 리 코드로 조회
                out.append({'sigunguCd': c[:5], 'bjdongCd': c[5:8] + '00', 'name': nm})
            else:
                out.append({'sigunguCd': c[:5], 'bjdongCd': c[5:10], 'name': nm})
    json.dump(out, open(f'{D}/bjd_codes.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('법정동·리', len(out))


def _titles_one(c):
    apt = {}; page = 1
    while True:
        d = get(B['title_url'], dict(sigunguCd=c['sigunguCd'], bjdongCd=c['bjdongCd'], numOfRows=str(B['rows']), pageNo=str(page), _type='json'), 'BLD_ENERGY_KEY')
        body = d['response']['body']; it = (body.get('items') or {}).get('item') or []
        it = it if isinstance(it, list) else [it]
        for r in it:
            use = (r.get('mainPurpsCdNm') or '') + ' ' + (r.get('etcPurps') or '')   # 주용도 '공동주택' + 기타용도 '아파트'
            if '아파트' in use and int(r.get('hhldCnt') or 0) > 0:
                k = f"{r['sigunguCd']}-{r['bjdongCd']}-{r['bun']}-{r['ji']}"
                a = apt.setdefault(k, {'addr': r.get('platPlc'), 'hhld': 0, 'bld': 0, 'name': (r.get('bldNm') or '').strip()})
                a['hhld'] += int(r['hhldCnt']); a['bld'] += 1
        if page * B['rows'] >= int(body.get('totalCount') or 0):
            return apt
        page += 1


def titles():
    """법정동별 결과를 data/raw/building_energy/titles_cache.json 에 쌓아, 끊겨도 이어서 한다."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading
    C = json.load(open(f'{D}/bjd_codes.json', encoding='utf-8'))
    cf = f'{D}/titles_cache.json'
    cache = json.load(open(cf, encoding='utf-8')) if os.path.exists(cf) else {}
    todo = [c for c in C if f"{c['sigunguCd']}-{c['bjdongCd']}" not in cache]
    lock = threading.Lock()
    with ThreadPoolExecutor(B.get('workers', 2)) as ex:
        fut = {ex.submit(_titles_one, c): c for c in todo}
        for i, f in enumerate(as_completed(fut)):
            c = fut[f]
            with lock:
                cache[f"{c['sigunguCd']}-{c['bjdongCd']}"] = f.result()
                if i % 10 == 0:
                    json.dump(cache, open(cf, 'w', encoding='utf-8'), ensure_ascii=False)
                    print(len(cache), '/', len(C), flush=True)
    json.dump(cache, open(cf, 'w', encoding='utf-8'), ensure_ascii=False)
    apt = {k: v for part in cache.values() for k, v in part.items()}
    json.dump(apt, open(f'{D}/apt_lots.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    big = {k: v for k, v in apt.items() if v['hhld'] >= B['min_hhld']}
    print('아파트 지번', len(apt), '/', B['min_hhld'], '세대 이상', len(big), '/ 세대 합', sum(v['hhld'] for v in big.values()))


def months():
    K = EDC_P['priority']['energy']['kma']; Y = EDC_P['priority']['energy']['lst_air']['years']
    L = B.get('lag_months', 0)   # 고지 월은 전달 사용분을 주로 반영 → 냉방도일 월 + lag 까지 받는다
    return [f'{y}{m:02d}' for y in range(Y[0], Y[1] + 1) for m in range(K['months'][0], K['months'][1] + 1 + L)]


def energy():
    """표본 단지(params sample_n, seed 고정)의 지번 × 월 전기 사용량. elec_monthly.json 에 쌓아 이어서 한다."""
    import random, threading
    from concurrent.futures import ThreadPoolExecutor, as_completed
    apt = json.load(open(f'{D}/apt_lots.json', encoding='utf-8'))
    big = sorted(k for k, v in apt.items() if v['hhld'] >= B['min_hhld'])
    random.Random(B['seed']).shuffle(big); big = big[:B['sample_n']]
    f = f'{D}/elec_monthly.json'
    got = json.load(open(f, encoding='utf-8')) if os.path.exists(f) else {}
    jobs = [(k, ym) for k in big for ym in months() if f'{k}|{ym}' not in got]
    print('표본 단지', len(big), '· 남은 조회', len(jobs), flush=True)
    def one(job):
        k, ym = job; sg, bj, bun, ji = k.split('-')
        d = get(B['energy_url'], dict(sigunguCd=sg, bjdongCd=bj, bun=bun, ji=ji, useYm=ym, numOfRows='10', pageNo='1', _type='json'), 'BLD_ENERGY_KEY')
        it = ((d.get('response', {}).get('body', {}).get('items') or {}).get('item')) or []
        it = it if isinstance(it, list) else [it]
        return job, (sum(float(r.get('useQty') or 0) for r in it) if it else None)
    lock = threading.Lock()
    with ThreadPoolExecutor(B.get('workers', 2)) as ex:
        for i, fu in enumerate(as_completed([ex.submit(one, j) for j in jobs])):
            (k, ym), v = fu.result()
            with lock:
                got[f'{k}|{ym}'] = v
                if i % 100 == 0:
                    json.dump(got, open(f, 'w', encoding='utf-8')); print(i, '/', len(jobs), flush=True)
    json.dump(got, open(f, 'w', encoding='utf-8'))
    print('완료 · 지번×월', len(got), '· 값 있음', sum(v is not None for v in got.values()))


def fit():
    """지번별 고정효과 회귀: 세대당 월 전력(kWh) = a_지번 + b × 월 냉방도일. b × 100 = CDD 100당 세대 월 전력."""
    import csv, glob, io, statistics as st
    from collections import defaultdict
    K = EDC_P['priority']['energy']['kma']
    day = defaultdict(list)
    for fn in glob.glob(f'{RAW}/kma/OBS_ASOS_TIM_*.csv'):
        for r in csv.reader(io.StringIO(open(fn, 'rb').read().decode('cp949'))):
            if r and r[0].isdigit() and int(r[0]) == K['station'] and r[3] != '':
                day[r[2][:10]].append(float(r[3]))
    cdd = defaultdict(float)
    for d, v in day.items():
        if len(v) >= 20:
            cdd[d[:4] + d[5:7]] += max(0.0, sum(v) / len(v) - K['cdd_base_c'])
    apt = json.load(open(f'{D}/apt_lots.json', encoding='utf-8'))
    got = json.load(open(f'{D}/elec_monthly.json', encoding='utf-8'))
    lots = defaultdict(list)
    L = B.get('lag_months', 0)
    def back(ym):                 # 고지 월 → 사용(냉방도일) 월
        y, m = int(ym[:4]), int(ym[4:]) - L
        return f'{y}{m:02d}'
    for kk, q in got.items():
        k, ym = kk.split('|')
        if q and back(ym) in cdd:
            lots[k].append((cdd[back(ym)], q / apt[k]['hhld']))
    xs, ys, per = [], [], []
    for k, v in lots.items():
        if len(v) < B.get('min_months', 12):
            continue
        mx = st.mean(a for a, _ in v); my = st.mean(b for _, b in v)
        dx = [a - mx for a, _ in v]; dy = [b - my for _, b in v]
        xs += dx; ys += dy
        sxx = sum(a * a for a in dx)
        if sxx > 0:
            per.append(sum(a * b for a, b in zip(dx, dy)) / sxx)
    b = sum(a * c for a, c in zip(xs, ys)) / sum(a * a for a in xs)
    q = st.quantiles(per, n=4)
    base = st.mean(v for vv in lots.values() for _, v in vv)
    out = {'lag_months': L, 'lots': len(per), 'obs': len(xs), 'kwh_per_hh_per_cdd': round(b, 4), 'kwh_per_100cdd': round(b * 100, 2),
           'lot_q_per_100cdd': [round(x * 100, 2) for x in q], 'mean_kwh_per_hh_month': round(base, 1),
           'cdd_month': {k: round(v, 1) for k, v in sorted(cdd.items())}}
    json.dump(out, open(f'{OUT}/bld_energy_coef.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print({k: v for k, v in out.items() if k != 'cdd_month'})


if __name__ == '__main__':
    {'codes': codes, 'titles': titles, 'energy': energy, 'fit': fit}[sys.argv[1]]()
