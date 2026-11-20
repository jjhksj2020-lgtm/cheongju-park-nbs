"""면적별 효과: (공원 안 − 300~500m), (0~100m − 300~500m)를 위성 새녹지 면적·공원 공식면적 구간별로 비교하고 log(면적) 기울기를 구한다.
입력: data/r1_did.csv, data/r1_matched_parks.csv
"""
import csv, math, statistics as st
d = list(csv.DictReader(open('data/r1_did.csv', encoding='utf-8')))
pk = {int(r['idx']): int(r['공원면적_m2']) for r in csv.DictReader(open('data/r1_matched_parks.csv', encoding='utf-8'))}
rows = []
for r in d:
    if not r['did_in'] or not r['did_300_500']: continue
    rows.append(dict(ha=float(r['patch_ha']), park_ha=pk[int(r['idx'])] / 1e4,
                     cin=float(r['did_in']) - float(r['did_300_500']),
                     c100=(float(r['did_0_100']) - float(r['did_300_500'])) if r['did_0_100'] else None))
def q(v, p): v = sorted(v); return v[int((len(v) - 1) * p)]
def bins(key, edges, label):
    print(f'\n[{label}]')
    for a, b in zip(edges[:-1], edges[1:]):
        s = [x for x in rows if a <= x[key] < b]
        if not s: continue
        ci = [x['cin'] for x in s]; c1 = [x['c100'] for x in s if x['c100'] is not None]
        print(f'  {a:>5}~{b:<5}ha n={len(s):2d}  공원안 {st.median(ci):+.2f} [{q(ci,.25):+.2f}~{q(ci,.75):+.2f}]  0~100m {st.median(c1):+.2f}  음수(안) {sum(v<0 for v in ci)}/{len(ci)}')
def slope(key):
    x = [math.log10(r[key]) for r in rows]; y = [r['cin'] for r in rows]
    mx, my = st.mean(x), st.mean(y); b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / sum((a - mx) ** 2 for a in x)
    # 순위상관(스피어만)
    rk = lambda v: {i: k for k, i in enumerate(sorted(range(len(v)), key=lambda j: v[j]))}
    rx, ry = rk(x), rk(y); n = len(x)
    rho = 1 - 6 * sum((rx[i] - ry[i]) ** 2 for i in range(n)) / (n * (n * n - 1))
    print(f'  {key}: 면적 10배당 공원안 효과 {b:+.2f} °C, 스피어만 ρ = {rho:+.2f} (n={n})')
bins('ha', [0.4, 0.6, 1.0, 2.0, 20], '위성 새녹지 덩어리 면적')
bins('park_ha', [0, 2, 5, 10, 30, 100], '공원 공식 면적(목록)')
print('\n[log 면적 기울기]'); slope('ha'); slope('park_ha')
