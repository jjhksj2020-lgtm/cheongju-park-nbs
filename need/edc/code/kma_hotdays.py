"""청주 ASOS 시간 기온(data/raw/kma/OBS_ASOS_TIM_*.csv, 기상자료개방포털) → 여름 냉방도일 기준 초과일수 → need/out/kma_summary.json
일평균기온 = 그날 24개 시간 기온의 평균. 초과일수 = 6~9월 중 일평균 > cdd_base_c 인 날. 냉방도일(CDD) = Σ(일평균 − 기준, 양수만)
연도별 초과일수의 최소·평균·최대를 발표판 ③의 hot_days(최소·기준·최대)로 쓴다(build_total.py가 params 가정값을 대신함).
실행: need/edc/code 에서  python kma_hotdays.py"""
import csv, glob, io, json, os, statistics as st
from collections import defaultdict
from common import EDC_P, OUT, RAW

K = EDC_P['priority']['energy']['kma']
rows = []
for f in sorted(glob.glob(f'{RAW}/kma/OBS_ASOS_TIM_*.csv')):
    for r in csv.reader(io.StringIO(open(f, 'rb').read().decode('cp949'))):
        if not r or not r[0].isdigit() or int(r[0]) != K['station'] or r[3] == '':
            continue
        rows.append((r[2][:10], float(r[3]), float(r[4]) if r[4] else None))
day = defaultdict(list)
for d, ta, _ in rows:
    if K['months'][0] <= int(d[5:7]) <= K['months'][1]:
        day[d].append(ta)
years = defaultdict(lambda: {'days': 0, 'cdd': 0.0, 'n': 0})
for d, v in day.items():
    if len(v) < 20:          # 시간 자료가 너무 빠진 날은 뺀다
        continue
    m = sum(v) / len(v); y = years[d[:4]]; y['n'] += 1
    if m > K['cdd_base_c']:
        y['days'] += 1; y['cdd'] += m - K['cdd_base_c']
Y = {k: {'days': v['days'], 'cdd': round(v['cdd'], 1), 'n_days': v['n']} for k, v in sorted(years.items())}
ds = [v['days'] for v in Y.values()]
out = {'station': K['station'], 'base_c': K['cdd_base_c'], 'years': Y,
       'hot_days': [min(ds), round(st.mean(ds)), max(ds)], 'source': '기상청 기상자료개방포털 ASOS 시간자료(청주 131)'}
json.dump(out, open(f'{OUT}/kma_summary.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for k, v in Y.items():
    print(k, f"24°C 초과 {v['days']}일 · CDD {v['cdd']} · 자료 {v['n_days']}일")
print('hot_days [최소, 평균, 최대] =', out['hot_days'])
