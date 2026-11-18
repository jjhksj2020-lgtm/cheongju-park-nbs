# -*- coding: utf-8 -*-
"""
S 회복력 v3 — 자립형 태양광 공원등(분산 ESS) + 충전 허브(집중 ESS)
실행: python s_engine_v3.py → S_results_40parks_v3.csv, S_summary_v3.md
입력: params_s3.yaml, park40_geocoded.csv, gee_v2_output_20261116.json (폴리곤 기준 수목·인구)
"""
import csv, json, os, math, itertools, yaml
HERE = os.path.dirname(os.path.abspath(__file__))
P = yaml.safe_load(open(os.path.join(HERE, "params_v3.yaml"), encoding="utf-8"))
parks = {int(r["site_id"]): r for r in csv.DictReader(open(os.path.join(HERE, "..", "data", "park40_geocoded.csv"), encoding="utf-8-sig"))}
COLS = ["site_id","lsta_in","lsta_300","ndvi_in","pop300_wp","pop300_ghsl","pop2000","slope","bh300","tree_frac","ghi","area_poly"]
gee = {r[0]: dict(zip(COLS, r)) for r in json.load(open(os.path.join(HERE, "..", "..", "h", "data", "gee", "gee_v2_output_20261116.json")))}

def rank_pct(vals):
    order = sorted(range(len(vals)), key=lambda i: vals[i]); out = [0]*len(vals); i = 0
    while i < len(order):
        j = i
        while j+1 < len(order) and vals[order[j+1]] == vals[order[i]]: j += 1
        for k in range(i, j+1): out[order[k]] = ((i+j)/2+1)/len(vals)
        i = j+1
    return out

def compute(coverage=None, phones=None, w_cov=None, hub_on=True):
    L, H, E = P["lamp"], P["hub"], P["evacuation"]
    coverage = L["coverage_m2"] if coverage is None else coverage
    phones = L["phones_per_port_night"] if phones is None else phones
    w_cov = P["score"]["weights"]["covered_persons"] if w_cov is None else w_cov
    rows = []
    for sid in sorted(parks):
        r = parks[sid]; g = gee[sid]; area = float(r["area_m2"]); typ = r["type"]
        fac = area * P["facility_share"][typ]
        lamps = min(L["max_lamps"], max(L["min_lamps"], math.floor(fac / coverage)))
        ess_wh = lamps * L["battery_wh"]
        lit_m2 = lamps * coverage
        lit_cap = lit_m2 / E["m2_per_person"]                      # 조명 아래 수용 인원
        phones_lamp = lamps * L["usb_ports"] * phones
        hub = 1 if (hub_on and typ in H["types"]) else 0
        phones_hub = hub * H["ess_kwh"] * 1000 * H["usable"] / H["phone_wh"]
        n_dem = g["pop2000"] * E["evac_rate"]; n_cap = area / E["m2_per_person"]; n_evac = min(n_dem, n_cap)
        covered = min(n_evac, lit_cap)
        light_ratio = min(1.0, lit_cap / n_evac) if n_evac > 0 else 1.0
        charge_ratio = min(1.0, (phones_lamp + phones_hub) / n_evac) if n_evac > 0 else 1.0
        rows.append(dict(site_id=sid, type=typ, name=r["name"], addr=r["addr_gongo"], area_m2=int(area), facility_m2=round(fac),
            tree_frac=round(g["tree_frac"], 2), shade_flag=("수목 음영 주의" if g["tree_frac"] > 0.5 else ""),
            lamps=lamps, ess_kwh=round(ess_wh/1000, 2), lit_m2=round(lit_m2), lit_capacity=round(lit_cap), hub=hub, hub_ess_kwh=hub*H["ess_kwh"],
            phones_per_night=round(phones_lamp + phones_hub), pop2000=round(g["pop2000"]), n_evac=round(n_evac),
            evac_limit=("면적" if n_cap < n_dem else "수요"), covered=round(covered), light_ratio=round(light_ratio, 2), charge_ratio=round(charge_ratio, 2),
            _c=covered, _l=light_ratio))
    n = len(rows); pc = rank_pct([x["_c"] for x in rows]); pl = rank_pct([x["_l"] for x in rows])
    for x, a, b in zip(rows, pc, pl): x["S_score"] = round(w_cov*a + (1-w_cov)*b, 3)
    srt = sorted(rows, key=lambda x: -x["S_score"])
    lo, hi = P["score"]["grade_cuts"]
    for i, x in enumerate(srt):
        x["S_rank"] = i+1; pct = 1 - i/n; x["S_grade"] = "상" if pct >= hi else ("중" if pct >= lo else "하")
    for x in rows: x.pop("_c"); x.pop("_l")
    return rows

if __name__ == "__main__":
    base = compute()
    grades = {x["site_id"]: [] for x in base}
    for cov, ph, w, hub in itertools.product(P["lamp"]["coverage_sensitivity"], P["lamp"]["phones_sensitivity"], [0.4, 0.6, 0.8], [True, False]):
        for x in compute(cov, ph, w, hub): grades[x["site_id"]].append(x["S_grade"])
    for x in base:
        gs = grades[x["site_id"]]; x["n_scen_high"] = gs.count("상"); x["stability"] = "확정" if len(set(gs)) == 1 else "경계"
    with open(os.path.join(HERE, "..", "data", "S_results_40parks_v3.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=base[0].keys()); w.writeheader(); w.writerows(base)
    top = sorted(base, key=lambda x: x["S_rank"])[:10]
    md = [f"# S 회복력 v3 — 태양광 공원등 + 충전 허브 ({P['asof']})", "",
          f"- 가로등 합계 {sum(x['lamps'] for x in base):,}기 · 분산 ESS {sum(x['ess_kwh'] for x in base):.1f} kWh · 허브 {sum(x['hub'] for x in base)}기(각 5 kWh)",
          f"- 등급 상 {sum(x['S_grade']=='상' for x in base)} · 중 {sum(x['S_grade']=='중' for x in base)} · 하 {sum(x['S_grade']=='하' for x in base)} · 24 시나리오(담당면적 2×충전 2×가중치 3×허브 2) 확정 {sum(x['stability']=='확정' for x in base)}/40",
          "", "| 순위 | 공원 | 가로등 | ESS kWh | 허브 | 대피 인원 | 조명 수용 | 충전/밤 | 조명 자립률 | 등급 | 안정성 |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for x in top: md.append(f"| {x['S_rank']} | {x['name']} | {x['lamps']} | {x['ess_kwh']} | {x['hub']} | {x['n_evac']:,} | {x['lit_capacity']:,} | {x['phones_per_night']:,} | {x['light_ratio']} | {x['S_grade']} | {x['stability']} ({x['n_scen_high']}/24) |")
    open(os.path.join(HERE, "..", "data", "S_summary_v3.md"), "w", encoding="utf-8").write("\n".join(md)+"\n"); print("\n".join(md))
