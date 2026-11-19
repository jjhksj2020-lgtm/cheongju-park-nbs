"""D 결핍 · C 연결 · F 실행 계산 엔진 (순수 함수).

전략 문서(대시보드 개발 전략 — 사업성 파트)의 규약을 따른다.
- 모든 함수는 V(value, status, src_keys)를 돌려준다. 튜플처럼 풀어 쓸 수 있다.
- status는 '확정' < '가정' < '미산정' 순으로 약해지고, 결과는 가장 약한 입력을 따른다.
- 모르는 값은 None + '미산정'. 평균이나 0으로 채우지 않는다.
- 숫자 상수는 params_dcf.yaml에서만 온다.
- D·C는 필요성 파트의 입력이다(판정은 여기서 내지 않는다). F는 사업성 파트(engine.py) 옆에 붙는다.

입력 표(전처리 prep/ 스크립트가 만든다)
- grid_reach  : grid_id, pop, pop_status, served_by_built(bool), reach_sites(';'로 이은 site_id)
- site_admin  : site_id, admin_code
- admin_park  : admin_code, pop, pop_status, built_park_area_m2
- patches     : patch_id, area_m2, site_id(없으면 빈칸)
- patch_dist  : a, b, dist_m (가장자리 사이 거리)
- site_axis   : site_id, axis_dist_m, axis_status
- park_parcel : site_id, pnu, jimok, in_area_m2, owner_class, owner_count(공유지연명, 없으면 빈칸)
- master_d0   : site_id, park_type, area_m2, lapse_year(또는 lapse_date)
"""
from __future__ import annotations

import datetime as _dt
import math
from typing import Iterable, NamedTuple

import numpy as np
import pandas as pd
import yaml
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

STATUS_ORDER = {"확정": 0, "가정": 1, "미산정": 2}
BANNED_WORDS = ("해제",)


class V(NamedTuple):
    value: object
    status: str
    src_keys: tuple


# ---------------------------------------------------------------- 공통

def load_params(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def weakest(statuses: Iterable[str]) -> str:
    statuses = list(statuses)
    if not statuses:
        return "미산정"
    for s in statuses:
        if s not in STATUS_ORDER:
            raise ValueError(f"알 수 없는 status: {s}")
    return max(statuses, key=STATUS_ORDER.__getitem__)


def merge_src(*groups: Iterable[str]) -> tuple:
    out: list[str] = []
    for g in groups:
        for k in ([g] if isinstance(g, str) else g):
            if k and k not in out:
                out.append(k)
    return tuple(out)


def missing(src: Iterable[str]) -> V:
    return V(None, "미산정", merge_src(src))


def to_columns(name: str, v: V) -> dict:
    """V 하나를 판정표 CSV의 세 열(값, __status, __src)로 바꾼다."""
    return {name: v.value, f"{name}__status": v.status, f"{name}__src": "+".join(v.src_keys)}


def _p(item: dict) -> V:
    """params의 {value, status, src} 항목을 V로."""
    return V(item["value"], item["status"], merge_src(item["src"]))


# ---------------------------------------------------------------- D 결핍

def _site_grids(grid_reach: pd.DataFrame, site_id: str) -> pd.DataFrame:
    sites = grid_reach["reach_sites"].fillna("").astype(str).str.split(";")
    return grid_reach[sites.apply(lambda xs: site_id in xs)]


def service_distance(park_type: str, params: dict) -> V:
    table = params["need_d"]["service_distance_m"]
    if park_type not in table:
        return missing(["L6"])
    return _p(table[park_type])


def d_irreplaceable_pop(site_id: str, grid_reach: pd.DataFrame, params: dict,
                        pop_src: str = "D5", extra_src: tuple = ("D4", "D6", "D7", "L6")) -> V:
    """대체 불가 인구: 이 공원의 유치거리 안이면서 조성 공원 어느 곳의 유치거리에도 들지 않는 인구."""
    g = _site_grids(grid_reach, site_id)
    src = merge_src([pop_src], extra_src)
    g = g[~g["served_by_built"].astype(bool)]
    if g.empty:
        return V(0, weakest([params["need_d"]["network_status"]]), src)
    if g["pop"].isna().any():
        return missing(src)
    status = weakest(list(g["pop_status"]) + [params["need_d"]["network_status"]])
    return V(int(g["pop"].sum()), status, src)


def d_shared_pop(site_id: str, grid_reach: pd.DataFrame, params: dict) -> V:
    """대체 불가 인구 중 다른 미집행 공원과 나눠 맡는 인구(둘 중 하나만 있어도 되는 사람)."""
    g = _site_grids(grid_reach, site_id)
    g = g[~g["served_by_built"].astype(bool)]
    g = g[g["reach_sites"].astype(str).str.split(";").apply(lambda xs: len([x for x in xs if x]) >= 2)]
    src = merge_src(["D5", "D4", "D6", "D7"])
    if g["pop"].isna().any():
        return missing(src)
    return V(int(g["pop"].sum()), weakest(list(g["pop_status"]) + [params["need_d"]["network_status"]]), src)


def d_unserved_share(site_id: str, grid_reach: pd.DataFrame, params: dict) -> V:
    """서비스권 밖 인구 비율(지도 표시용): 대체 불가 인구 ÷ 이 공원 유치권 전체 인구."""
    g = _site_grids(grid_reach, site_id)
    irr = d_irreplaceable_pop(site_id, grid_reach, params)
    if irr.value is None or g["pop"].isna().any():
        return missing(irr.src_keys)
    total = g["pop"].sum()
    if total == 0:
        return missing(irr.src_keys)
    return V(float(irr.value) / float(total), irr.status, irr.src_keys)


def d_area_gap(site_id: str, site_admin: pd.DataFrame, admin_park: pd.DataFrame, params: dict) -> V:
    """생활권(행정동) 1인당 공원면적 부족분(㎡/인) = max(0, 법정 기준 − 조성 공원 면적 ÷ 인구)."""
    std = _p(params["need_d"]["per_capita_std_m2"][params["need_d"]["per_capita_std_use"]])
    src = merge_src(["D6", "D8"], std.src_keys)
    row = site_admin[site_admin["site_id"] == site_id]
    if row.empty:
        return missing(src)
    adm = admin_park[admin_park["admin_code"] == row.iloc[0]["admin_code"]]
    if adm.empty or pd.isna(adm.iloc[0]["pop"]) or pd.isna(adm.iloc[0]["built_park_area_m2"]):
        return missing(src)
    pop = float(adm.iloc[0]["pop"])
    if pop <= 0:
        return missing(src)
    per_capita = float(adm.iloc[0]["built_park_area_m2"]) / pop
    return V(max(0.0, float(std.value) - per_capita), weakest([adm.iloc[0]["pop_status"], std.status]), src)


# ---------------------------------------------------------------- C 연결

def _pc_numerator(area: np.ndarray, dist: csr_matrix, theta: float) -> float:
    """PC의 분자 Σ_i Σ_j a_i a_j p*_ij. p*_ij = exp(−θ·최단경로거리) (최대 곱 확률 경로와 같다)."""
    if len(area) == 0:
        return 0.0
    sp = dijkstra(dist, directed=False)
    p = np.exp(-theta * sp)          # 연결 안 됨(inf) → 0
    return float(area @ p @ area)


def _build_graph(patches: pd.DataFrame, patch_dist: pd.DataFrame, keep: np.ndarray,
                 theta: float, floor: float) -> tuple[np.ndarray, csr_matrix]:
    ids = patches["patch_id"].to_numpy()[keep]
    index = {pid: i for i, pid in enumerate(ids)}
    max_d = -math.log(floor) / theta
    e = patch_dist[(patch_dist["dist_m"] <= max_d)
                   & patch_dist["a"].isin(index) & patch_dist["b"].isin(index)]
    rows = e["a"].map(index).to_numpy()
    cols = e["b"].map(index).to_numpy()
    # 거리 0(맞닿은 패치)은 희소행렬에서 사라지므로 아주 작은 양수로 둔다
    w = np.maximum(e["dist_m"].to_numpy(dtype=float), 1e-9)
    g = csr_matrix((w, (rows, cols)), shape=(len(ids), len(ids)))
    return patches["area_m2"].to_numpy(dtype=float)[keep], g


def c_dpc_by_distance(patches: pd.DataFrame, patch_dist: pd.DataFrame, params: dict) -> pd.DataFrame:
    """공원마다, 이동거리마다 dPC(%) = (PC_현재 − PC_공원 제거) ÷ PC_현재 × 100.

    제거 시나리오: 실효 후 개발되어 그 공원의 패치가 빠지는 경우. 징검다리 효과도 함께 빠진다.
    공원 면적 계산에 쓰는 A_L(경관 면적)은 비율에서 약분되므로 필요 없다.
    """
    c = params["need_c"]
    patches = patches[patches["area_m2"] >= c["min_patch_m2"]].reset_index(drop=True)
    sites = sorted(s for s in patches["site_id"].dropna().unique() if str(s))
    out = []
    for d in c["dispersal_m"]:
        theta = -math.log(c["p_at_dispersal"]) / d
        all_keep = np.ones(len(patches), dtype=bool)
        a, g = _build_graph(patches, patch_dist, all_keep, theta, c["prob_floor"])
        base = _pc_numerator(a, g, theta)
        for s in sites:
            keep = (patches["site_id"] != s).to_numpy()
            a2, g2 = _build_graph(patches, patch_dist, keep, theta, c["prob_floor"])
            dpc = (base - _pc_numerator(a2, g2, theta)) / base * 100 if base > 0 else float("nan")
            out.append({"site_id": s, "dispersal_m": d, "dpc": dpc})
    return pd.DataFrame(out)


def c_dpc_summary(dpc_long: pd.DataFrame, params: dict, all_sites: Iterable[str]) -> dict[str, dict]:
    """거리별 dPC → 공원별 중앙값, 순위 폭, '가정 의존' 표시."""
    c = params["need_c"]
    src = merge_src(c["src"])
    res: dict[str, dict] = {}
    if dpc_long.empty:
        return {s: {"c_dpc_median": missing(src), "c_rank_spread": missing(src),
                    "c_assumption_dependent": missing(src)} for s in all_sites}
    wide = dpc_long.pivot(index="site_id", columns="dispersal_m", values="dpc")
    ranks = wide.rank(ascending=False, method="min")
    spread = ranks.max(axis=1) - ranks.min(axis=1)
    for s in all_sites:
        if s not in wide.index or wide.loc[s].isna().any():
            res[s] = {"c_dpc_median": missing(src), "c_rank_spread": missing(src),
                      "c_assumption_dependent": missing(src)}
            continue
        res[s] = {
            "c_dpc_median": V(float(wide.loc[s].median()), c["status"], src),
            "c_rank_spread": V(int(spread.loc[s]), c["status"], src),
            "c_assumption_dependent": V(bool(spread.loc[s] >= c["rank_spread_flag"]), c["status"], src),
        }
        for d in wide.columns:
            res[s][f"c_dpc_d{int(d)}"] = V(float(wide.loc[s, d]), c["status"], src)
    return res


def c_axis_dist(site_id: str, site_axis: pd.DataFrame) -> V:
    """녹지축·수변축까지 최단거리(m). 축 도면이 그림에서 옮긴 것이면 axis_status=가정."""
    row = site_axis[site_axis["site_id"] == site_id]
    src = merge_src(["C3"])
    if row.empty or pd.isna(row.iloc[0]["axis_dist_m"]):
        return missing(src)
    return V(float(row.iloc[0]["axis_dist_m"]), row.iloc[0]["axis_status"], src)


# ---------------------------------------------------------------- F 실행 (engine.py 사업성 함수 옆에 붙는 항목)

def _parcels(site_id: str, park_parcel: pd.DataFrame) -> pd.DataFrame:
    return park_parcel[park_parcel["site_id"] == site_id]


def f_public_ratio(site_id: str, park_parcel: pd.DataFrame, params: dict) -> V:
    """F1 국공유지 비율 = 국·공유 필지의 공원 안 면적 ÷ 공원 안 필지 면적 합."""
    p = _parcels(site_id, park_parcel)
    src = merge_src(["D1", "D3"])
    total = p["in_area_m2"].sum()
    if p.empty or total <= 0:
        return missing(src)
    miss = p.loc[p["owner_class"].isna(), "in_area_m2"].sum() / total
    if miss > params["exec_f"]["owner_missing_tolerance"]:
        return missing(src)
    pub = p.loc[p["owner_class"].isin(params["exec_f"]["public_owner_classes"]), "in_area_m2"].sum()
    return V(float(pub / total), "확정", src)


def f_private_owners(site_id: str, park_parcel: pd.DataFrame, params: dict) -> V:
    """F6 소유 분산도 = 사유 필지별 소유자 수의 합(같은 사람이 여러 필지를 가지면 중복 → 상한값)."""
    p = _parcels(site_id, park_parcel)
    p = p[~p["owner_class"].isin(params["exec_f"]["public_owner_classes"]) & p["owner_class"].notna()]
    src = merge_src(["D3", "D12"])
    if p.empty:
        return V(0, "확정", src)
    if p["owner_count"].isna().any():
        return missing(src)
    return V(int(p["owner_count"].sum()), "확정", src)


def f_high_value_ratio(site_id: str, park_parcel: pd.DataFrame, params: dict) -> V:
    """F7 고가 지목 비율 = 사유지 중 대·잡종지 면적 비율."""
    p = _parcels(site_id, park_parcel)
    src = merge_src(["D1", "D3"])
    priv = p[p["owner_class"] == "사유"]
    if p["owner_class"].isna().any() or p["jimok"].isna().any():
        return missing(src)
    tot = priv["in_area_m2"].sum()
    if tot <= 0:
        return V(0.0, "확정", src)
    hv = priv.loc[priv["jimok"].isin(params["exec_f"]["high_value_jimok"]), "in_area_m2"].sum()
    return V(float(hv / tot), "확정", src)


def f_review_grade(total_cost: V, params: dict) -> V:
    """F4 투자심사 등급. total_cost는 engine.py의 L + K 결과(V)를 그대로 받는다."""
    th = params["exec_f"]["review_thresholds_won"]
    central, feas = _p(th["central"]), _p(th["feasibility"])
    src = merge_src(total_cost.src_keys, central.src_keys)
    if total_cost.value is None:
        return missing(src)
    x = float(total_cost.value)
    if x >= feas.value:
        grade, st = "타당성조사", weakest([total_cost.status, feas.status])
    elif x >= central.value:
        grade, st = "중앙", weakest([total_cost.status, central.status, feas.status])
    else:
        grade, st = "자체", weakest([total_cost.status, central.status])
    return V(grade, st, src)


def _lapse_date(row: pd.Series, params: dict) -> V:
    if "lapse_date" in row and pd.notna(row.get("lapse_date")):
        return V(_dt.date.fromisoformat(str(row["lapse_date"])[:10]), "확정", ("D0",))
    if pd.notna(row.get("lapse_year")):
        if params["exec_f"]["lapse_date_rule"] != "year_start":
            raise ValueError("지원하지 않는 lapse_date_rule")
        return V(_dt.date(int(row["lapse_year"]), 1, 1), "가정", ("D0",))
    return missing(["D0"])


def _months_between(a: _dt.date, b: _dt.date) -> int:
    return (b.year - a.year) * 12 + (b.month - a.month) - (1 if b.day < a.day else 0)


def f_start_margin(site_id: str, master: pd.DataFrame, base_date: _dt.date, params: dict,
                   review_grade: V | None = None) -> dict[str, V]:
    """F5 착수 여유(개월) = 실효일 − 기준일 − 수단별 리드타임 − 심사 기간. 수단마다 하나씩."""
    row = master[master["site_id"] == site_id]
    out: dict[str, V] = {}
    lead = params["exec_f"]["lead_time_months"]
    if row.empty:
        return {m: missing(["D0"]) for m in lead}
    lapse = _lapse_date(row.iloc[0], params)
    extra = V(0, "확정", ())
    if review_grade is not None:
        if review_grade.value is None:
            extra = missing(review_grade.src_keys)
        else:
            extra = _p(params["exec_f"]["review_extra_months"][review_grade.value])
    for means, item in lead.items():
        lt = _p(item)
        src = merge_src(lapse.src_keys, lt.src_keys, extra.src_keys)
        if lapse.value is None or extra.value is None:
            out[means] = missing(src)
            continue
        m = _months_between(base_date, lapse.value) - int(lt.value) - int(extra.value)
        out[means] = V(m, weakest([lapse.status, lt.status, extra.status]), src)
    return out


def f_prior_investment(site_id: str, prior: pd.DataFrame | None) -> dict[str, V]:
    """F8 기투자: 시 자료(C1)를 그대로 옮긴다. 없으면 미산정."""
    keys = ("f_paid_area_ratio", "f_spent_won")
    if prior is None:
        return {k: missing(["C1"]) for k in keys}
    row = prior[prior["site_id"] == site_id]
    if row.empty:
        return {k: missing(["C1"]) for k in keys}
    r = row.iloc[0]
    return {
        "f_paid_area_ratio": V(float(r["paid_area_ratio"]), "확정", ("C1",)) if pd.notna(r["paid_area_ratio"]) else missing(["C1"]),
        "f_spent_won": V(float(r["spent_won"]), "확정", ("C1",)) if pd.notna(r["spent_won"]) else missing(["C1"]),
    }


# ---------------------------------------------------------------- 표 만들기

def build_need_dc_table(master: pd.DataFrame, grid_reach: pd.DataFrame, site_admin: pd.DataFrame,
                        admin_park: pd.DataFrame, patches: pd.DataFrame, patch_dist: pd.DataFrame,
                        site_axis: pd.DataFrame, params: dict) -> pd.DataFrame:
    """필요성 파트로 넘기는 D·C 표(data/need_dc.csv). 판정은 넣지 않는다."""
    sites = list(master["site_id"])
    dpc = c_dpc_summary(c_dpc_by_distance(patches, patch_dist, params), params, sites)
    rows = []
    for _, m in master.iterrows():
        s = m["site_id"]
        row = {"site_id": s}
        if service_distance(m["park_type"], params).value is None:
            for k in ("d_irreplaceable_pop", "d_shared_pop", "d_unserved_share"):
                row.update(to_columns(k, missing(["L6"])))
        else:
            row.update(to_columns("d_irreplaceable_pop", d_irreplaceable_pop(s, grid_reach, params)))
            row.update(to_columns("d_shared_pop", d_shared_pop(s, grid_reach, params)))
            row.update(to_columns("d_unserved_share", d_unserved_share(s, grid_reach, params)))
        row.update(to_columns("d_area_gap_m2pc", d_area_gap(s, site_admin, admin_park, params)))
        for k, v in dpc[s].items():
            row.update(to_columns(k, v))
        row.update(to_columns("c_axis_dist_m", c_axis_dist(s, site_axis)))
        rows.append(row)
    return pd.DataFrame(rows)


def build_exec_f_table(master: pd.DataFrame, park_parcel: pd.DataFrame, total_cost: dict[str, V],
                       base_date: _dt.date, params: dict, prior: pd.DataFrame | None = None) -> pd.DataFrame:
    """사업성 판정표에 붙일 F 확장 열. total_cost는 site_id → engine.py의 (L + K) V."""
    rows = []
    for s in master["site_id"]:
        row = {"site_id": s}
        row.update(to_columns("f_public_ratio", f_public_ratio(s, park_parcel, params)))
        row.update(to_columns("f_private_owners", f_private_owners(s, park_parcel, params)))
        row.update(to_columns("f_high_value_ratio", f_high_value_ratio(s, park_parcel, params)))
        grade = f_review_grade(total_cost.get(s, missing(["D1", "D2", "D3", "R1"])), params)
        row.update(to_columns("f_review_grade", grade))
        lead = params["exec_f"]["lead_time_months"]
        for means, v in f_start_margin(s, master, base_date, params, grade).items():
            row.update(to_columns(f"f_margin_{lead[means]['col']}", v))
        for k, v in f_prior_investment(s, prior).items():
            row.update(to_columns(k, v))
        rows.append(row)
    return pd.DataFrame(rows)


def assert_no_banned_words(df: pd.DataFrame) -> None:
    text = " ".join(map(str, df.columns)) + " " + " ".join(str(x) for x in df.to_numpy().ravel())
    for w in BANNED_WORDS:
        if w in text:
            raise AssertionError(f"금지어 포함: {w}")
