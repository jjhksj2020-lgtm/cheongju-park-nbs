"""① 녹지 → 지표온도 단계의 규모 상관관계 (학습 데이터로부터 적합)
- 효과 크기 A(a): 공원 안 지표온도 변화(사례 안 대비). 학습 = D1 나대지→공원 107곳만 (조성 방향, 과대 방지)
    A(a) = A_max · (1 − exp(−a / a0))     a = 새 녹지 면적(ha)
- 퍼짐 길이 L(a): 경계 밖 ΔT(d) = A · exp(−d / L). 학습 = D1 107곳 + D2 숲 개발 547곳 (방향 무관하게 '모양'만, 비율로 정규화)
    L(a) = L0 · a^b
- 검증 = D3 우리 40개 공원 현재 분포(근린공원165 10.6ha L≈130m, 생태공원3 258ha 600m 이상)
입력: data/r1_did_kr_raw.txt + data/r1_onset_kr.csv (D1), data/r3_cases_contrast.txt (D2)
출력: data/size_model.json, 화면 표
"""
import csv, json, math, statistics as st
f = lambda x: None if x == 'na' else float(x)
# ---------- D1 사례별 (공원 안·고리 − 300~500m)
on = {int(r['idx']): r for r in csv.DictReader(open('data/r1_onset_kr.csv', encoding='utf-8'))}
D1 = []
for it in open('data/r1_did_kr_raw.txt').read().strip().split(';'):
    v = it.split(','); z = list(map(f, v[7:12]))
    if z[4] is None or z[0] is None: continue
    D1.append(dict(a=float(on[int(v[0])]['patch_ha']), i=z[0] - z[4],
                   r50=None if z[1] is None else z[1] - z[4], r150=None if z[2] is None else z[2] - z[4], r250=None if z[3] is None else z[3] - z[4]))
# ---------- D2 사례별 (부호 반대: 녹지 감소 → 더워짐. 모양만 쓰므로 그대로)
D2 = []
for it in open('data/r3_cases_contrast.txt').read().split('\n')[1].split(';'):
    a, dn, i, r50, r150, r250 = map(f, it.split(','))
    D2.append(dict(a=a, i=i, r50=r50, r150=r150, r250=r250))

def med(v): v = [x for x in v if x is not None]; return st.median(v) if v else None
def bin_stats(D, edges):
    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        s = [x for x in D if lo <= x['a'] < hi]
        if len(s) < 8: continue
        A = med([x['i'] for x in s]); prof = {d: med([x[k] for x in s]) for d, k in [(50, 'r50'), (150, 'r150'), (250, 'r250')]}
        pts = [(d, math.log(p / A)) for d, p in prof.items() if p is not None and A and p / A > 0.02]
        L = -sum(d * d for d, _ in pts) / sum(d * y for d, y in pts) if pts and sum(d * y for d, y in pts) < 0 else None
        out.append(dict(lo=lo, hi=hi, n=len(s), a=med([x['a'] for x in s]), A=A, r50=prof[50], r150=prof[150], r250=prof[250], L=L))
    return out
B1 = bin_stats(D1, [0.4, 0.55, 0.75, 1.0, 1.5, 2.5, 20])
B2 = bin_stats(D2, [1.5, 1.8, 2.1, 2.5, 3.0, 4.0, 6.0, 20])
print('[D1 나대지→공원 107곳] 면적구간 | n | 중앙면적 | 공원안 A | 0~100 | 100~200 | 200~300 | L(m)')
for b in B1: print(f"  {b['lo']}~{b['hi']} | {b['n']} | {b['a']:.2f} | {b['A']:+.2f} | {b['r50']:+.2f} | {b['r150']:+.2f} | {b['r250']:+.2f} | {b['L'] and round(b['L'])}")
print('[D2 숲→개발 547곳]')
for b in B2: print(f"  {b['lo']}~{b['hi']} | {b['n']} | {b['a']:.2f} | {b['A']:+.2f} | {b['r50']:+.2f} | {b['r150']:+.2f} | {b['r250']:+.2f} | {b['L'] and round(b['L'])}")

# ---------- A(a) 적합 (D1, 사례 수 가중 최소제곱, 격자 탐색)
best = None
for Amax in [x / 100 for x in range(-300, -49)]:
    for a0 in [x / 100 for x in range(10, 400)]:
        sse = sum(b['n'] * (b['A'] - Amax * (1 - math.exp(-b['a'] / a0))) ** 2 for b in B1)
        if best is None or sse < best[0]: best = (sse, Amax, a0)
_, Amax, a0 = best
# ---------- L(a) 적합 (D1+D2 구간, log-log 가중 회귀)
P = [(b['a'], b['L'], b['n']) for b in B1 + B2 if b['L']]
W = sum(n for _, _, n in P); mx = sum(n * math.log(a) for a, _, n in P) / W; my = sum(n * math.log(L) for _, L, n in P) / W
b_ = sum(n * (math.log(a) - mx) * (math.log(L) - my) for a, L, n in P) / sum(n * (math.log(a) - mx) ** 2 for a, _, n in P)
L0 = math.exp(my - b_ * mx)
print(f"\nA(a) = {Amax:+.2f} × (1 − exp(−a/{a0:.2f}))   [D1 {len(D1)}곳]")
print(f"L(a) = {L0:.1f} × a^{b_:.3f} m          [D1+D2 구간 {len(P)}개]")
print(f"검증 D3: 10.6ha → L {L0*10.6**b_:.0f}m (현재 분포 실측 약 130m) · 258ha → L {L0*258**b_:.0f}m, 10% 지점 {L0*258**b_*math.log(10):.0f}m (실측 600m 이상)")
print('\n면적(ha) | 공원 안 | 경계 0m | 50m | 100m | 200m | L(m) | 효과 10%로 줄어드는 거리(m)')
tab = []
for a in [0.05, 0.1, 0.2, 0.3, 0.5, 1, 2, 4, 10, 30, 100]:
    A = Amax * (1 - math.exp(-a / a0)); L = L0 * a ** b_
    # 경계 밖은 R1 실측 비율(0~100m 중앙 ≈ 공원 안의 0.45)을 경계값으로: ΔT(d) = A·k_edge·exp(−d/L)
    row = dict(a=a, A=A, L=L, d10=L * math.log(10))
    tab.append(row)
    print(f"  {a:>6} | {A:+.2f} | {A:+.2f} | {A*math.exp(-50/L):+.2f} | {A*math.exp(-100/L):+.2f} | {A*math.exp(-200/L):+.2f} | {L:.0f} | {L*math.log(10):.0f}")
json.dump(dict(A=dict(form='Amax*(1-exp(-a/a0))', Amax=Amax, a0=a0, source='D1 나대지→공원 전국 107곳'),
               L=dict(form='L0*a^b', L0=L0, b=b_, source='D1 107곳 + D2 숲→개발 547곳 (모양만)'),
               bins_D1=B1, bins_D2=B2, table=tab, note='a=새 녹지 면적(ha), 여름(6~9월) 지표온도, d=공원 경계 밖 거리(m)'),
          open('data/size_model.json', 'w'), ensure_ascii=False, indent=1)
