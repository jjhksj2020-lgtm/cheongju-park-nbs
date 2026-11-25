"""R1-f 40개 공원 주변 시가지 지표온도 거리 프로필 정리.
입력: data/r1_profile40_raw.txt (r1_gee_profile40_read.js 출력), ../energy/out/master_energy.csv
값: 고리 시가지 픽셀 평균 LSTa − 기준(600~1500m) 시가지 평균 LSTa  (음수 = 공원 가까운 시가지가 더 시원)
퍼짐 거리: 경계에서부터 연속으로 −0.2 °C 이하인 마지막 고리의 바깥 거리 (시가지 픽셀 20개 이상 고리만)
"""
import csv, statistics as st
ZS = ['0_30', '30_60', '60_90', '90_120', '120_150', '150_210', '210_300', '300_420', '420_600']
OUT = {z: int(z.split('_')[1]) for z in ZS}
m = {int(r['site_id']): r for r in csv.DictReader(open('../energy/out/master_energy.csv', encoding='utf-8-sig'))}
f = lambda x: None if x == 'na' else float(x)
D = {}
for it in open('data/r1_profile40_raw.txt').read().strip().split(';'):
    sid, z, a, b, n, nd, bf = it.split(',')
    D.setdefault(int(sid), {})[z] = dict(all=f(a), bld=f(b), n=int(n), ndvi=f(nd), bf=f(bf))
rows = []
for sid, d in sorted(D.items()):
    base = d['base']['bld']; r = m[sid]; ha = float(r['area_m2']) / 1e4
    prof = {z: (d[z]['bld'] - base if d[z]['bld'] is not None and d[z]['n'] >= 20 and base is not None else None) for z in ZS}
    ext = 0
    for z in ZS:
        if prof[z] is None: continue
        if prof[z] <= -0.2: ext = OUT[z]
        else: break
    rows.append(dict(sid=sid, name=r['name'], ha=round(ha, 2), kind=r['kind'], land=r['dominant_landuse'],
                     in_all=round(d['in']['all'] - d['base']['all'], 2) if d['in']['all'] is not None else None,
                     ndvi_in=d['in']['ndvi'], ext_m=ext, **{'d_' + z: (round(v, 2) if v is not None else None) for z, v in prof.items()}))
with open('data/r1_profile40.csv', 'w', newline='', encoding='utf-8') as fo:
    w = csv.DictWriter(fo, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
def grp(lab, sub):
    if not sub: return
    line = []
    for z in ZS:
        v = [r['d_' + z] for r in sub if r['d_' + z] is not None]
        line.append(f"{OUT[z]}m {st.median(v):+.2f}" if v else f"{OUT[z]}m na")
    ex = [r['ext_m'] for r in sub]
    print(f"{lab} n={len(sub)} | 공원안(전체픽셀) {st.median([r['in_all'] for r in sub if r['in_all'] is not None]):+.2f} | 퍼짐거리 중앙 {st.median(ex):.0f}m (범위 {min(ex)}~{max(ex)}) | " + ' '.join(line))
for kind in ['보전형', '조성형']:
    print(f'\n== {kind} ==')
    for lab, a, b in [('0.2ha 미만', 0, 0.2), ('0.2~0.5ha', 0.2, 0.5), ('0.5~1ha', 0.5, 1), ('1~5ha', 1, 5), ('5ha 이상', 5, 1e9)]:
        grp(lab, [r for r in rows if r['kind'] == kind and a <= r['ha'] < b])
print('\n== 공원별 ==')
for r in sorted(rows, key=lambda r: -r['ha']):
    print(r['sid'], r['name'], r['ha'], r['kind'], r['land'], 'ndvi', r['ndvi_in'], '안', r['in_all'], '퍼짐', r['ext_m'], [r['d_' + z] for z in ZS])
