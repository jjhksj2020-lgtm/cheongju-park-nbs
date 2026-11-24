"""면적 구간별 거리 프로필: (구역 − 300~500m) 중앙값, 감쇠 길이 L, 효과가 사라지는 거리(중앙값 > −0.1 °C 되는 첫 고리).
입력: data/r1_did.csv (여름)"""
import csv, math, statistics as st
d = [r for r in csv.DictReader(open('data/r1_did.csv', encoding='utf-8')) if r['did_300_500']]
Z = [('in', 0), ('0_100', 50), ('100_200', 150), ('200_300', 250)]
def prof(sub):
    out = {}
    for k, m in Z:
        v = [float(r['did_' + k]) - float(r['did_300_500']) for r in sub if r['did_' + k]]
        out[k] = (st.median(v), len(v), sum(x < 0 for x in v))
    return out
for lab, a, b in [('0.4~0.6ha', 0.4, 0.6), ('0.6~1ha', 0.6, 1.0), ('1~2ha', 1.0, 2.0), ('2ha 이상', 2.0, 99), ('1ha 미만', 0, 1), ('1ha 이상', 1, 99)]:
    sub = [r for r in d if a <= float(r['patch_ha']) < b]
    p = prof(sub); A = p['in'][0]
    pts = [(m, math.log(p[k][0] / A)) for k, m in Z[1:] if A < 0 and p[k][0] / A > 0]
    L = -sum(x * x for x, _ in pts) / sum(x * y for x, y in pts) if pts and sum(x * y for x, y in pts) < 0 else float('nan')
    ext = next((m for k, m in Z[1:] if p[k][0] > -0.1), '>300')
    print(f"{lab:9s} n={len(sub):2d} | " + ' | '.join(f"{k} {p[k][0]:+.2f} ({p[k][2]}/{p[k][1]})" for k, _ in Z) + f" | L≈{L:.0f}m | 사라지는 고리 중앙 {ext}m")
