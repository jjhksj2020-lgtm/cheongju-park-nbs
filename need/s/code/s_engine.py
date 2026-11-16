# -*- coding: utf-8 -*-
"""
S 회복력(에너지 자립) 계산 엔진 — 청주 장기미집행 공원 40개소
실행:  python s_engine.py   (이 폴더에서)  →  ../data/S_results_40parks.csv, ../data/S_summary.md
입력:  params.yaml, ../data/park40_geocoded.csv, ../data/gee/gee_solar_output_20261116.json
"""
import csv, json, math, os, sys
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
P = yaml.safe_load(open(os.path.join(HERE, "params.yaml"), encoding="utf-8"))

parks = {int(r["site_id"]): r for r in csv.DictReader(open(os.path.join(DATA, "park40_geocoded.csv"), encoding="utf-8-sig"))}
gee = {r[0]: dict(zip(["site_id", "ghi", "slope", "aspect", "hs_winter", "shadow_frac", "bh300", "tree_frac", "pop2000", "pop300"], r))
       for r in json.load(open(os.path.join(DATA, "gee", "gee_solar_output_20261116.json")))}

def clamp(v, lo, hi): return max(lo, min(hi, v))

def compute(load_kwh=None):
    pa, y, ev = P["pv_area"], P["yield"], P["evacuation"]
    load_kwh = ev["load_kwh_per_person_day"] if load_kwh is None else load_kwh
    rows = []
    for sid, r in parks.items():
        g = gee[sid]; area = float(r["area_m2"]); typ = r["type"]
        # ① 설치 가능 면적·용량
        f_slope = pa["slope_penalty"] if g["slope"] > pa["slope_limit_deg"] else 1.0
        a_pv = area * pa["facility_share"][typ] * pa["pv_share_of_facility"][typ] * (1 - g["tree_frac"]) * f_slope
        kw_raw = a_pv * pa["kw_per_m2"]
        kw = min(kw_raw, pa["cap_kw"])
        # ② 발전량 보정 계수
        f_ghi = g["ghi"] / y["ghi_ref_kwh_m2"]
        f_terr = 1 - y["terrain_shadow"]
        f_bld = 1 - min(y["building_shade_loss_max"], y["building_shade_loss_per_m"] * g["bh300"])
        yield_kwh_kw = y["base_kwh_per_kw"] * f_ghi * f_terr * f_bld   # pr은 base 1,300에 이미 반영된 실측치로 보고 별도 곱하지 않음
        e_year = kw * yield_kwh_kw                                     # kWh/yr
        e_day_worst = e_year / 365 * y["worst_month_factor"]           # kWh/일 (재난 시 보수적)
        # ③ 피난 부하
        n_demand = g["pop2000"] * ev["evac_rate"]
        n_cap = area / ev["m2_per_person"]
        n_evac = min(n_demand, n_cap)
        load_day = n_evac * load_kwh
        ess_kwh = load_day * ev["autonomy_days"]
        ss = (e_day_worst / load_day) if load_day > 0 else float("nan")
        n_covered = min(n_evac, e_day_worst / load_kwh)                # 필수 전력을 보장할 수 있는 대피 인원
        rows.append(dict(site_id=sid, type=typ, name=r["name"], addr=r["addr_gongo"], area_m2=int(area),
            ghi=round(g["ghi"], 0), slope=round(g["slope"], 1), aspect=round(g["aspect"], 0), hs_winter=round(g["hs_winter"], 2),
            bh300=round(g["bh300"], 1), tree_frac=round(g["tree_frac"], 2), pop2000=round(g["pop2000"]),
            pv_area_m2=round(a_pv), pv_kw=round(kw, 1), capped=int(kw_raw > pa["cap_kw"]),
            f_ghi=round(f_ghi, 3), f_terrain=round(f_terr, 2), f_building=round(f_bld, 2), yield_kwh_kw=round(yield_kwh_kw),
            e_mwh_yr=round(e_year / 1000, 1), e_kwh_day_worst=round(e_day_worst, 1),
            n_evac=round(n_evac), evac_limit=("면적" if n_cap < n_demand else "수요"), load_kwh_day=round(load_day, 1),
            ess_kwh=round(ess_kwh), self_sufficiency=round(min(ss, P["score"]["self_sufficiency_cap"]), 2), n_covered=round(n_covered), ss_raw=min(ss, P["score"]["self_sufficiency_rank_cap"]), nc_raw=n_covered))
    # 순위·등급: 자립률 백분위와 보장 인원 백분위의 가중 평균
    ok = [x for x in rows if not math.isnan(x["ss_raw"])]; n = len(ok)
    def pct(key):   # 평균 순위 백분위 (동점은 같은 값)
        order = sorted(ok, key=lambda x: x[key]); i = 0
        while i < n:
            j = i
            while j + 1 < n and order[j + 1][key] == order[i][key]: j += 1
            for k in range(i, j + 1): order[k]["p_" + key] = ((i + j) / 2 + 1) / n
            i = j + 1
    pct("ss_raw"); pct("nc_raw")
    w = P["score"]["weights"]
    for x in ok: x["S_score"] = round(w["self_sufficiency"] * x["p_ss_raw"] + w["covered_persons"] * x["p_nc_raw"], 3)
    ok.sort(key=lambda x: -x["S_score"])
    lo, hi = P["score"]["grade_cuts"]
    for i, x in enumerate(ok):
        x["S_rank"] = i + 1; x["S_pct"] = round(1 - i / n, 2)
        x["S_grade"] = "상" if x["S_pct"] >= hi else ("중" if x["S_pct"] >= lo else "하")
    for x in rows:
        x.setdefault("S_score", ""); x.setdefault("S_rank", ""); x.setdefault("S_pct", ""); x.setdefault("S_grade", "미산정")
        for k in ("ss_raw", "nc_raw", "p_ss_raw", "p_nc_raw"): x.pop(k, None)
    rows.sort(key=lambda x: x["site_id"])
    return rows

if __name__ == "__main__":
    rows = compute()
    out = os.path.join(DATA, "S_results_40parks.csv")
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    # 민감도: 1인 부하 하한·상한에서 등급이 바뀌는 공원
    lo, hi = P["evacuation"]["load_sensitivity"]
    g_lo = {x["site_id"]: x["S_grade"] for x in compute(lo)}
    g_hi = {x["site_id"]: x["S_grade"] for x in compute(hi)}
    stable = [x for x in rows if g_lo[x["site_id"]] == x["S_grade"] == g_hi[x["site_id"]]]
    top = sorted(rows, key=lambda x: (x["S_rank"] == "", x["S_rank"]))[:10]
    md = ["# S 회복력(에너지 자립) 결과 — " + P["asof"], "",
          f"- 산정 {len([x for x in rows if x['S_grade']!='미산정'])}/40 · 등급 상 {sum(x['S_grade']=='상' for x in rows)} · 중 {sum(x['S_grade']=='중' for x in rows)} · 하 {sum(x['S_grade']=='하' for x in rows)}",
          f"- 1인 부하 {lo}~{hi} kWh/일 사이에서 등급이 안 바뀌는 공원(확정): {len(stable)}/40",
          f"- 설치 용량 합계 {sum(x['pv_kw'] for x in rows):,.0f} kW · 연 발전량 합계 {sum(x['e_mwh_yr'] for x in rows):,.0f} MWh",
          "", "| 순위 | 공원 | 용량 kW | 발전 MWh/yr | 대피 인원 | 부하 kWh/일 | 자립률 | 보장 인원 | 등급 |", "|---|---|---|---|---|---|---|---|---|"]
    for x in top:
        md.append(f"| {x['S_rank']} | {x['name']} | {x['pv_kw']} | {x['e_mwh_yr']} | {x['n_evac']:,} | {x['load_kwh_day']} | {x['self_sufficiency']} | {x['n_covered']:,} | {x['S_grade']} |")
    open(os.path.join(DATA, "S_summary.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))
