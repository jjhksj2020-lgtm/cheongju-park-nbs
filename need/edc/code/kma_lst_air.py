"""지표온도 → 기온 비율의 청주 실측 → need/out/kma_lst_air.json
입력: data/raw/kma/cheongju_station_lst*.csv(GEE kma_lst_gee.js 결과), OBS_ASOS_TIM_*·OBS_AWS_TIM_*(시간 기온), stations.csv
방법: 촬영 장면마다 관측소 간 차이를 본다 — 지표온도 편차(관측소 − 장면 평균)와 같은 날 hour_kst 시 기온 편차(고도 보정).
     모든 장면의 편차를 모아 원점 통과 회귀 기울기 = 기온 변화 / 지표온도 변화. 장면별 기울기의 사분위도 함께 낸다.
실행: need/edc/code 에서  python kma_lst_air.py"""
import csv, glob, io, json, statistics as st
from collections import defaultdict
from common import EDC_P, OUT, RAW

A = EDC_P['priority']['energy']['lst_air']
stn = list(csv.DictReader(open(f'{RAW}/kma/stations.csv', encoding='utf-8')))
def elev(s, d):
    for r in stn:
        if int(r['stn']) == s and r['start'] <= d < (r['end'] or '2100-01-01'):
            return float(r['elev_m'])
ta = {}
for f in glob.glob(f'{RAW}/kma/OBS_A*_TIM_*.csv'):
    for r in csv.reader(io.StringIO(open(f, 'rb').read().decode('cp949'))):
        if r and r[0].isdigit() and r[3] != '' and int(r[2][11:13]) == A['hour_kst']:
            ta[(int(r[0]), r[2][:10])] = float(r[3])
scene = defaultdict(list)
for f in glob.glob(f'{RAW}/kma/cheongju_station_lst*.csv'):
    for r in csv.DictReader(open(f, encoding='utf-8-sig')):
        d = r['t'][:10]
        if r['mean'] in ('', None) or not (r['start'] <= d < r['end']) or (int(r['stn']), d) not in ta:
            continue
        s = int(r['stn']); z = elev(s, d)
        scene[d].append((s, float(r['mean']), ta[(s, d)], z))
xs, ys, per = [], [], []
for d, v in sorted(scene.items()):
    if len(v) < A['min_stations']:
        continue
    zl = st.mean(x[3] for x in v); ml = st.mean(x[1] for x in v)
    tc = [x[2] + A['lapse_c_per_m'] * (x[3] - zl) for x in v]; mt = st.mean(tc)   # 기온을 평균 고도로 보정
    dx = [x[1] - ml for x in v]; dy = [t - mt for t in tc]
    xs += dx; ys += dy
    sxx = sum(a * a for a in dx)
    if sxx > 1:
        per.append(sum(a * b for a, b in zip(dx, dy)) / sxx)
slope = sum(a * b for a, b in zip(xs, ys)) / sum(a * a for a in xs)
q = st.quantiles(per, n=4) if len(per) >= 4 else [None] * 3
out = {'scenes': len([d for d in scene if len(scene[d]) >= A['min_stations']]), 'pairs': len(xs), 'ratio_pooled': round(slope, 3),
       'ratio_scene_q': [round(x, 3) if x is not None else None for x in q], 'hour_kst': A['hour_kst']}
json.dump(out, open(f'{OUT}/kma_lst_air.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(out)
