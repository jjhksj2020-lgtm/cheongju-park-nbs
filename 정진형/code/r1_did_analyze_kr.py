"""[전국판] R1-d DiD 결과 정리: 사례별 DiD(구역 ΔLSTa − 대조 ΔLSTa), 분포, 거리 감쇠 적합, 주변 동반녹화 여부별 비교.
입력: data/r1_did_kr_raw.txt (r1_gee_did_read.js 출력 그대로), data/r1_onset_kr.csv
출력: data/r1_did_kr.csv, 화면 요약(→ 08 문서 §3)
"""
import csv, math, statistics as st
Z = ['in', '0_100', '100_200', '200_300', '300_500']
MID = {'0_100': 50, '100_200': 150, '200_300': 250, '300_500': 400}
on = {int(r['idx']): r for r in csv.DictReader(open('data/r1_onset_kr.csv', encoding='utf-8'))}
f = lambda x: None if x == 'na' else float(x)
rows = []
for item in open('data/r1_did_kr_raw.txt').read().strip().split(';'):
    v = item.split(',')
    i, pre, post, ha, npre, npost, ctrl = int(v[0]), v[1], v[2], f(v[3]), int(v[4]), int(v[5]), f(v[6])
    z = dict(zip(Z, map(f, v[7:12]))); ndvi_pre, ndvi_post = f(v[12]), f(v[13])
    if ctrl is None: continue
    o = on[i]
    r = dict(idx=i, name=o['공원명'] if '공원명' in o else o['name'], addr=o['addr'], pre=pre, post=post, patch_ha=ha,
             n_pre=npre, n_post=npost, ctrl=ctrl, ndvi_pre=ndvi_pre, ndvi_post=ndvi_post,
             ring_change=float(o['ring_change']), lat=float(o['lat']), lon=float(o['lon']))
    for k in Z: r['did_' + k] = None if z[k] is None else round(z[k] - ctrl, 3)
    rows.append(r)
with open('data/r1_did_kr.csv', 'w', newline='', encoding='utf-8') as fo:
    w = csv.DictWriter(fo, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def q(v, p):
    v = sorted(v); k = (len(v) - 1) * p; a = math.floor(k); b = math.ceil(k)
    return v[a] + (v[b] - v[a]) * (k - a)
def summ(sub, label):
    print(f'\n[{label}] n={len(sub)}')
    for k in Z:
        v = [r['did_' + k] for r in sub if r['did_' + k] is not None]
        if not v: continue
        neg = sum(x < 0 for x in v)
        print(f'  {k:8s} 중앙 {st.median(v):+.2f}  평균 {st.mean(v):+.2f}  IQR {q(v,.25):+.2f}~{q(v,.75):+.2f}  음수 {neg}/{len(v)}')
ok = [r for r in rows if r['n_pre'] >= 3 and r['n_post'] >= 3]
print('전체', len(rows), '장면 충분(전·후 ≥3)', len(ok))
summ(ok, '전체')
summ([r for r in ok if r['ring_change'] < 0.10], '주변 NDVI 변화 < 0.10 (주변 동반녹화 적음)')
summ([r for r in ok if r['ring_change'] >= 0.10], '주변 NDVI 변화 ≥ 0.10 (신도시 동반녹화)')
summ([r for r in ok if r['patch_ha'] >= 1.0], '덩어리 ≥ 1ha')
# 거리 감쇠: 고리 중앙값을 안쪽 중앙값으로 나눈 비 → ln(ratio) = −d/L, 원점 지나는 최소제곱
inn = st.median([r['did_in'] for r in ok if r['did_in'] is not None])
pts = []
for k, d in MID.items():
    m = st.median([r['did_' + k] for r in ok if r['did_' + k] is not None])
    print(f'  고리 {k}: 중앙 {m:+.2f} (안쪽 대비 {m/inn:.2f})')
    if m / inn > 0: pts.append((d, math.log(m / inn)))
if pts:
    L = -sum(d * d for d, _ in pts) / sum(d * y for d, y in pts)
    print(f'거리감쇠 L ≈ {L:.0f} m (안쪽 {inn:+.2f} °C 기준, 점 {len(pts)}개)')
# NDVI 상승폭 대비 효과(°C per 0.1 NDVI)
sl = [r['did_in'] / ((r['ndvi_post'] - r['ndvi_pre']) * 10) for r in ok if r['did_in'] is not None and r['ndvi_post'] and r['ndvi_pre'] is not None and r['ndvi_post'] - r['ndvi_pre'] > 0.1]
print(f'안쪽 효과 / NDVI 0.1 상승: 중앙 {st.median(sl):+.2f} °C, IQR {q(sl,.25):+.2f}~{q(sl,.75):+.2f} (n={len(sl)})')

# ── 사례 안 대비: 같은 시기 함께 개발된 300~500m 고리를 기준으로(신도시 동반 개발 효과를 상쇄)
print('\n[사례 안 대비: 구역 − 300~500m 고리]')
for lab, sub in [('전체', ok), ('주변 녹화 <0.10', [r for r in ok if r['ring_change'] < 0.10]),
                 ('주변 녹화 ≥0.10', [r for r in ok if r['ring_change'] >= 0.10]), ('덩어리 ≥1ha', [r for r in ok if r['patch_ha'] >= 1])]:
    out = []
    for k in ['in', '0_100', '100_200', '200_300']:
        v = [r['did_' + k] - r['did_300_500'] for r in ok if r in sub and r['did_' + k] is not None and r['did_300_500'] is not None]
        out.append(f"{k} {st.median(v):+.2f} [{q(v,.25):+.2f}~{q(v,.75):+.2f}] 음수 {sum(x<0 for x in v)}/{len(v)}")
    print(f'  {lab} (n={len(sub)}): ' + ' | '.join(out))
# 사례별 거리감쇠: (구역 − 300~500) = A·exp(−d/L), 안쪽 d=0, 고리 중앙 거리 — 중앙값 프로필로 적합
prof = {}
for k, d in [('in', 0), ('0_100', 50), ('100_200', 150), ('200_300', 250)]:
    prof[d] = st.median([r['did_' + k] - r['did_300_500'] for r in ok if r['did_' + k] is not None and r['did_300_500'] is not None])
A = prof[0]; pts = [(d, math.log(v / A)) for d, v in prof.items() if d > 0 and v / A > 0]
if pts:
    L = -sum(d * d for d, _ in pts) / sum(d * y for d, y in pts)
    print(f'중앙 프로필 {prof} → A {A:+.2f} °C, L ≈ {L:.0f} m (점 {len(pts)})')

# ── 면적 구간 (사례 안 대비)
print('\n[면적 구간: 공원 안 / 0~100m (− 300~500m)]')
for a, b in [(0.4, 0.6), (0.6, 1.0), (1.0, 2.0), (2.0, 99)]:
    sub = [r for r in ok if a <= r['patch_ha'] < b and r['did_in'] is not None]
    if not sub: continue
    ci = [r['did_in'] - r['did_300_500'] for r in sub]
    c1 = [r['did_0_100'] - r['did_300_500'] for r in sub if r['did_0_100'] is not None]
    print(f"  {a}~{b}ha n={len(sub)} 안 {st.median(ci):+.2f} 0~100 {st.median(c1):+.2f} 음수(안) {sum(x<0 for x in ci)}/{len(ci)}")
# ── 지역: 중부권 vs 그 밖
cen = lambda r: 36.0 <= r['lat'] <= 37.75 and 126.6 <= r['lon'] <= 127.9
print()
summ([r for r in ok if cen(r)], '중부권(기존 탐지 범위)')
summ([r for r in ok if not cen(r)], '중부권 밖(이번에 추가)')
for lab, sub in [('중부권', [r for r in ok if cen(r)]), ('중부권 밖', [r for r in ok if not cen(r)])]:
    v = [r['did_in'] - r['did_300_500'] for r in sub if r['did_in'] is not None]
    w = [r['did_0_100'] - r['did_300_500'] for r in sub if r['did_0_100'] is not None]
    print(f"  {lab} 사례 안 대비: 공원 안 {st.median(v):+.2f} (n={len(v)}), 0~100m {st.median(w):+.2f}")
