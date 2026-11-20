"""R1-e 계절별 비교: 같은 72곳·같은 전후 기간에서 촬영 월만 바꾼 결과.
입력: data/r1_did_raw.txt(여름 6~9월), data/r1_did_raw_{spring,autumn,winter}.txt  (r1_gee_did_read.js 출력 형식)
값 = 사례 안 대비(구역 ΔLSTa − 300~500m 고리 ΔLSTa) 중앙값
"""
import os, statistics as st
Z = ['in', '0_100', '100_200', '200_300', '300_500']
f = lambda x: None if x == 'na' else float(x)
def q(v, p): v = sorted(v); return v[int((len(v) - 1) * p)]
files = [('봄 3~5월', 'data/r1_did_raw_spring.txt'), ('여름 6~9월', 'data/r1_did_raw.txt'),
         ('가을 10~11월', 'data/r1_did_raw_autumn.txt'), ('겨울 12~2월', 'data/r1_did_raw_winter.txt')]
for lab, p in files:
    if not os.path.exists(p): print(lab, '없음'); continue
    rows = []
    for it in open(p).read().strip().split(';'):
        v = it.split(','); z = dict(zip(Z, map(f, v[7:12])))
        rows.append(dict(id=int(v[0]), npre=int(v[4]), npost=int(v[5]), z=z, ha=f(v[3])))
    ok = [r for r in rows if r['npre'] >= 2 and r['npost'] >= 3 and r['z']['300_500'] is not None]
    out = []
    for k in ['in', '0_100', '100_200']:
        c = [r['z'][k] - r['z']['300_500'] for r in ok if r['z'][k] is not None]
        out.append(f"{k} {st.median(c):+.2f} [{q(c,.25):+.2f}~{q(c,.75):+.2f}] 음수 {sum(x<0 for x in c)}/{len(c)}")
    big = [r['z']['in'] - r['z']['300_500'] for r in ok if r['z']['in'] is not None and r['ha'] >= 1]
    sc = [r['npre'] for r in rows]; sp = [r['npost'] for r in rows]
    print(f"{lab}: 사례 {len(ok)}/{len(rows)}, 장면 전 중앙 {st.median(sc)}·후 {st.median(sp)} | " + ' | '.join(out) + f" | ≥1ha 안 {st.median(big):+.2f} (n={len(big)})")
