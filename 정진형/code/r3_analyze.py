"""R1-h 숲 일부 개발 사례 정리.
(A) 숲 → 개발: 개발부·주변 고리의 (구역 − 300~500m 고리) 전후 변화 = 숲을 잃으면 그 자리와 주변이 얼마나 더워지나
(B) 개발 후(2022~24) 새 단지 안에서 남은 숲까지 거리별 LSTa (0~60m 기준 대비) = 남은 숲이 새 단지를 몇 m까지 식히나
입력: data/r3_did_raw.txt"""
import statistics as st
K = ['px', 'forest_ring', 'area_ha', 'n_pre', 'n_post', 'ndvi_pre', 'ndvi_post', 'd_in', 'd_0_100', 'd_100_200', 'd_200_300', 'd_300_500', 'f_0_60', 'f_60_120', 'f_120_240', 'f_240_600']
f = lambda x: None if x in ('na', '') else float(x)
rows = [dict(zip(K, map(f, it.split(',')))) for it in open('data/r3_did_raw.txt').read().strip().split(';')]
ok = [r for r in rows if r['n_pre'] and r['n_post'] and r['n_pre'] >= 3 and r['n_post'] >= 5 and r['d_300_500'] is not None]
def q(v, p): v = sorted(v); return v[int((len(v) - 1) * p)]
def show(lab, sub):
    if not sub: return
    out = []
    for k in ['d_in', 'd_0_100', 'd_100_200', 'd_200_300']:
        v = [r[k] - r['d_300_500'] for r in sub if r[k] is not None]
        out.append(f"{k[2:]} {st.median(v):+.2f} [{q(v,.25):+.2f}~{q(v,.75):+.2f}] 양수 {sum(x>0 for x in v)}/{len(v)}")
    nd = [r['ndvi_pre'] - r['ndvi_post'] for r in sub if r['ndvi_pre'] is not None and r['ndvi_post'] is not None]
    print(f"[A {lab}] n={len(sub)} NDVI 감소 중앙 {st.median(nd):.2f} | " + ' | '.join(out))
print('전체', len(rows), '사용', len(ok))
show('전체', ok)
for a, b in [(2, 3), (3, 5), (5, 20)]:
    show(f'개발부 {a}~{b}ha', [r for r in ok if a <= r['area_ha'] < b])
for a, b in [(0.3, 0.45), (0.45, 1.1)]:
    show(f'남은숲비율 {a}~{b}', [r for r in ok if a <= r['forest_ring'] < b])
# 감쇠: NDVI 1.0당
sl = [(r['d_in'] - r['d_300_500']) / (r['ndvi_pre'] - r['ndvi_post']) for r in ok if r['d_in'] is not None and r['ndvi_pre'] - r['ndvi_post'] > 0.2]
print(f"숲 손실 NDVI 1.0당 개발부 온도 상승: 중앙 {st.median(sl):+.2f} °C/NDVI [{q(sl,.25):+.2f}~{q(sl,.75):+.2f}] n={len(sl)}")
# (B)
B = [r for r in ok if r['f_0_60'] is not None]
for k in ['f_60_120', 'f_120_240', 'f_240_600']:
    v = [r[k] - r['f_0_60'] for r in B if r[k] is not None]
    if v: print(f"[B] 남은 숲에서 {k[2:]}m 떨어진 개발부 − 0~60m: 중앙 {st.median(v):+.2f} [{q(v,.25):+.2f}~{q(v,.75):+.2f}] 양수 {sum(x>0 for x in v)}/{len(v)}")
