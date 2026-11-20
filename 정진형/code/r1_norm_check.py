"""정규화 점검: 장면별 10km 중앙값 정규화를 했을 때(z, LSTa)와 안 했을 때(r, 원 LST)의 결과 비교.
입력: data/r1_norm_check_raw.txt (r1_gee_did_check_read.js 출력), data/r1_did.csv
"""
import csv, statistics as st
f = lambda x: None if x == 'na' else float(x)
Z = ['in', '0_100', '100_200', '200_300', '300_500']
rows = []
for it in open('data/r1_norm_check_raw.txt').read().strip().split(';'):
    v = it.split(','); d = dict(id=int(v[0]), bpre=f(v[1]), bpost=f(v[2]), z_in=f(v[8]), z_out=f(v[9]))
    d.update({'r_' + k: f(x) for k, x in zip(Z, v[3:8])}); rows.append(d)
def q(v, p): v = sorted(v); return v[int((len(v) - 1) * p)]
box = [r['bpost'] - r['bpre'] for r in rows if r['bpre'] is not None and r['bpost'] is not None]
print(f'10km 기준값 변화(후−전): 중앙 {st.median(box):+.2f} °C, IQR {q(box,.25):+.2f}~{q(box,.75):+.2f}, n={len(box)}')
for k in Z:
    v = [r['r_' + k] for r in rows if r['r_' + k] is not None]
    print(f'정규화 없음 ΔLST {k:8s}: 중앙 {st.median(v):+.2f}')
a = [r['r_in'] - r['r_300_500'] for r in rows if r['r_in'] is not None and r['r_300_500'] is not None]
b = [r['z_in'] - r['z_out'] for r in rows if r['z_in'] is not None and r['z_out'] is not None]
print(f'공원 안 − 300~500m: 정규화 없음 {st.median(a):+.2f} [{q(a,.25):+.2f}~{q(a,.75):+.2f}] / 정규화 {st.median(b):+.2f} [{q(b,.25):+.2f}~{q(b,.75):+.2f}] (n={len(a)},{len(b)})')
print(f'공원 안 단독 변화: 정규화 없음 {st.median([r["r_in"] for r in rows if r["r_in"] is not None]):+.2f} / 정규화 {st.median([r["z_in"] for r in rows if r["z_in"] is not None]):+.2f}')
