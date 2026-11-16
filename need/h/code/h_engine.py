# -*- coding: utf-8 -*-
"""
H 위해(열환경) 계산 엔진 v2 — 공원 폴리곤 기준, 계수는 청주 전후 실측(energy 파트 gee_change)
실행: python h_engine.py  → H_results_40parks_v2.csv, H_summary_v2.md
"""
import csv, json, os, itertools
HERE = os.path.dirname(os.path.abspath(__file__))
P = {
  "coef": {"green": -2.1411, "loss": -7.0132, "spatial": -10.135},   # ℃/NDVI. green·loss = 2013-16→2023-25 녹지 변화 픽셀 기울기(energy/data/gee/gee_change_output.txt), spatial = 공간 회귀(상한)
  "coef_default": -4.577,                                             # (green+loss)/2 — energy 파트 '기준'과 동일
  "target_ndvi": {"수목형": 0.863, "잔디형": 0.535},
  "weights": {"heat": 0.5, "benefit": 0.5},
  "weight_presets": [(0.5, 0.5), (0.7, 0.3), (0.3, 0.7)],
  "grade_cuts": [0.30, 0.70],
  "heat_field": "lsta_300",   # 현재 더위 = 공원+300m 일대 (사람이 있는 곳); 녹지 증가는 공원 땅 안(ndvi_in)
  "pop_field": "pop300_wp",   # WorldPop 2020 (need/edc E1과 같은 자료)
}
COLS = ["site_id","lsta_in","lsta_300","ndvi_in","pop300_wp","pop300_ghsl","pop2000_wp","slope","bh300","tree_frac","ghi","area_poly"]
gee = {r[0]: dict(zip(COLS, r)) for r in json.load(open(os.path.join(HERE, "..", "data", "gee", "gee_v2_output_20261116.json")))}
meta = {int(r["site_id"]): r for r in csv.DictReader(open(os.path.join(HERE, "..", "data", "park40_geocoded.csv"), encoding="utf-8-sig"))}

def rank_pct(vals):  # 평균 순위 백분위
    order = sorted(range(len(vals)), key=lambda i: vals[i]); out = [0]*len(vals); i = 0
    while i < len(order):
        j = i
        while j+1 < len(order) and vals[order[j+1]] == vals[order[i]]: j += 1
        for k in range(i, j+1): out[order[k]] = ((i+j)/2+1)/len(vals)
        i = j+1
    return out

def quantile(sorted_vals, q):
    pos = (len(sorted_vals)-1)*q; lo = int(pos); hi = min(lo+1, len(sorted_vals)-1)
    return sorted_vals[lo] + (sorted_vals[hi]-sorted_vals[lo])*(pos-lo)

def compute(b=None, scen="수목형", w=None):
    b = P["coef_default"] if b is None else b; w = w or (P["weights"]["heat"], P["weights"]["benefit"])
    t = P["target_ndvi"][scen]; rows = []
    for sid in sorted(gee):
        g = gee[sid]; m = meta[sid]
        dn = max(0, t - g["ndvi_in"]); cool = b*dn; ben = abs(cool)*g[P["pop_field"]]
        rows.append(dict(site_id=sid, type=m["type"], name=m["name"], addr=m["addr_gongo"], expire=m["expire_yr"], area_m2=m["area_m2"],
            lsta_in=round(g["lsta_in"],2), lsta_300=round(g["lsta_300"],2), ndvi_in=round(g["ndvi_in"],3), pop300=round(g[P["pop_field"]]),
            dndvi=round(dn,3), cool=round(cool,2), lst_after=round(g["lsta_in"]+cool,2), benefit=round(ben), _heat=g[P["heat_field"]], _ben=ben))
    n = len(rows); ph = rank_pct([r["_heat"] for r in rows]); pb = rank_pct([r["_ben"] for r in rows])
    for r, a, c in zip(rows, ph, pb): r["H_score"] = round((w[0]*a + w[1]*c)/(w[0]+w[1]), 3)
    srt = sorted(rows, key=lambda r: -r["H_score"])
    for i, r in enumerate(srt): r["H_rank"] = i+1
    hs = sorted(r["H_score"] for r in rows); q7, q3 = quantile(hs, .7), quantile(hs, .3)
    for r in rows: r["grade"] = "상" if r["H_score"] >= q7 else ("중" if r["H_score"] >= q3 else "하")
    heat_sorted = sorted(rows, key=lambda r: -r["_heat"])
    for i, r in enumerate(heat_sorted): r["heat_grade"] = 1 + min(4, int(i/n*5))
    bs = sorted(rows, key=lambda r: -r["_ben"])
    for i, r in enumerate(bs): r["benefit_rank"] = i+1
    for r in rows: r.pop("_heat"); r.pop("_ben")
    return rows

if __name__ == "__main__":
    base = compute()
    # 안정성: 계수 2(green·loss) × 목표 2 × 가중치 3 = 12 시나리오 (+ 공간 회귀는 별도 참고)
    grades = {r["site_id"]: [] for r in base}
    for b, scen, w in itertools.product([P["coef"]["green"], P["coef"]["loss"]], ["수목형", "잔디형"], P["weight_presets"]):
        for r in compute(b, scen, w): grades[r["site_id"]].append(r["grade"])
    for r in base:
        gs = grades[r["site_id"]]; r["n_scen_high"] = gs.count("상")
        r["stability"] = "확정" if len(set(gs)) == 1 else "경계"
    sp = {r["site_id"]: r["grade"] for r in compute(P["coef"]["spatial"])}
    for r in base: r["grade_spatial"] = sp[r["site_id"]]
    out = os.path.join(HERE, "..", "data", "H_results_40parks_v2.csv")
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=base[0].keys()); w.writeheader(); w.writerows(sorted(base, key=lambda r: r["site_id"]))
    top = sorted(base, key=lambda r: r["H_rank"])[:10]
    md = ["# H 위해(열환경) 결과 v2 — 폴리곤·실측 계수 (2026-11-16)", "",
          f"- 계수 기본 {P['coef_default']} ℃/NDVI (전후 실측 green {P['coef']['green']} ~ loss {P['coef']['loss']} 중간), 공간 회귀 {P['coef']['spatial']}는 참고",
          f"- 등급 상 {sum(r['grade']=='상' for r in base)} · 중 {sum(r['grade']=='중' for r in base)} · 하 {sum(r['grade']=='하' for r in base)} · 12 시나리오 모두 같은 등급(확정) {sum(r['stability']=='확정' for r in base)}/40",
          f"- 평균 냉각(수목형) {sum(r['cool'] for r in base)/len(base):.2f} ℃ · 공간 회귀 계수로 바꿔도 상 등급이 같은 공원 {sum(r['grade']==r['grade_spatial'] for r in base)}/40",
          "", "| 순위 | 공원 | 등급 | 안정성 | 일대 ℃ | 공원 NDVI | 냉각 ℃ | 300m 인구 | 편익 |", "|---|---|---|---|---|---|---|---|---|"]
    for r in top: md.append(f"| {r['H_rank']} | {r['name']} | {r['grade']} | {r['stability']} ({r['n_scen_high']}/12 상) | {r['lsta_300']:+.1f} | {r['ndvi_in']:.2f} | {r['cool']} | {r['pop300']:,} | {r['benefit']:,} |")
    open(os.path.join(HERE, "..", "data", "H_summary_v2.md"), "w", encoding="utf-8").write("\n".join(md)+"\n"); print("\n".join(md))
