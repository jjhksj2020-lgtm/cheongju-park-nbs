"""[전국판] R1-b3 연도별 여름 NDVI(위성 실측)로 공원 녹지 정착 연도와 주변 동반변화를 판정하고 DiD 사례를 고른다.
입력: data/r1_yearly_ndvi_kr_raw.txt (GEE r1_gee_years.js 출력 그대로), data/r1_matched_parks_kr.csv
출력: data/r1_onset_kr.csv, data/r1_cases_kr.json
규칙(사전에 정한 것, 결과를 보고 바꾸지 않음):
  - 착공 전·공사 상태 = 2013~2018 중 2년 이동평균 최저(trough)
  - 성숙 상태 = 2022~2024 평균
  - 정착 연도 = trough 이후 처음으로 NDVI가 trough + 0.5×(성숙−trough) 이상이 되고 다음 해도 (임계−0.05) 이상인 해
  - 주변 동반변화 = 100~300m 고리 NDVI의 (2022~24 평균 − 2013~15 평균)
  - DiD 기간: 전 = trough−1 ~ trough+1(2013 이상, 정착 전), 후 = 2022~2024
  - DiD 사례: 정착 2016~2022, 상승폭 ≥ 0.25, 덩어리 ≥ 0.4ha, 초대형(>100ha 공원) 제외, 같은 공원 중복 제거
"""
import csv, json, statistics as st
Y = list(range(2013, 2026))
raw = open('data/r1_yearly_ndvi_kr_raw.txt').read().strip()
parks = {int(r['idx']): r for r in csv.DictReader(open('data/r1_matched_parks_kr.csv', encoding='utf-8'))}
f = lambda x: None if x == 'na' else float(x)
def mean(v):
    v = [x for x in v if x is not None]
    return st.mean(v) if v else None
rows = []
for item in raw.split(';'):
    i, ha, s = item.split(':')
    i = int(i); ha = float(ha)
    pr = [tuple(map(f, x.split('/'))) for x in s.split(',')]
    p = dict(zip(Y, [a for a, _ in pr])); r = dict(zip(Y, [b for _, b in pr]))
    # trough
    best = None
    for y in range(2013, 2018):
        m = mean([p[y], p[y + 1]])
        if m is not None and (best is None or m < best[1]): best = (y, m)
    ty, tv = best
    mat = mean([p[2022], p[2023], p[2024]])
    thr = tv + 0.5 * (mat - tv)
    onset = None
    for y in range(ty + 1, 2025):
        if p[y] is not None and p[y] >= thr and (p.get(y + 1) is None or p[y + 1] >= thr - 0.05):
            onset = y; break
    ring_d = mean([r[2022], r[2023], r[2024]]) - mean([r[2013], r[2014], r[2015]])
    k = parks[i]
    rows.append(dict(idx=i, name=k['공원명'], addr=k['소재지'], park_m2=int(k['공원면적_m2']), notice=k['지정고시일'],
                     lat=float(k['덩어리_위도']), lon=float(k['덩어리_경도']), patch_ha=ha,
                     trough_year=ty, trough=round(tv, 3), mature=round(mat, 3), rise=round(mat - tv, 3),
                     onset=onset, ring_change=round(ring_d, 3)))
with open('data/r1_onset_kr.csv', 'w', newline='', encoding='utf-8') as fo:
    w = csv.DictWriter(fo, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
seen = set(); cases = []
for x in sorted(rows, key=lambda x: (-x['patch_ha'])):
    key = (x['name'], round(x['lat'], 2), round(x['lon'], 2))
    if x['park_m2'] > 1_000_000 or key in seen: continue
    if x['onset'] is None or not (2016 <= x['onset'] <= 2022): continue
    if x['rise'] < 0.25 or x['patch_ha'] < 0.4: continue
    seen.add(key); seen.add((x['name'],))
    cases.append(x)
# 이름이 같은 공원(노을공원, 청라호수공원 등)은 큰 덩어리 하나만
uniq, names = [], set()
for x in cases:
    if x['name'] in names: continue
    names.add(x['name']); uniq.append(x)
# DiD 기간: 전 = trough 전후(2013 이상, 정착 연도 전까지), 후 = 2022~2024(성숙 NDVI와 같은 기간)
json.dump([[x['idx'], x['name'], max(2013, x['trough_year'] - 1), min(x['trough_year'] + 1, x['onset'] - 1), 2022, 2024, x['lat'], x['lon']]
           for x in uniq], open('data/r1_cases_kr.json', 'w'), ensure_ascii=False)
print('전체', len(rows), '사례', len(uniq))
import collections
print('정착연도', collections.Counter(x['onset'] for x in rows))
for x in uniq:
    print(x['idx'], x['name'], x['onset'], x['patch_ha'], x['rise'], x['ring_change'], x['addr'][:20])
