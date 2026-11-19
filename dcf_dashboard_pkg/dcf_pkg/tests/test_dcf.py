"""D·C·F 엔진 테스트. 합성 데이터만 쓴다(실데이터 골든 파일은 12주차에 추가)."""
import datetime as dt
import math
import pathlib
import re

import pandas as pd
import pytest

import engine_dcf as E

ROOT = pathlib.Path(__file__).resolve().parents[1]
P = E.load_params(ROOT / "params_dcf.yaml")


# ------------------------------------------------------------------ 공통 규약

def test_weakest_status():
    assert E.weakest(["확정", "가정"]) == "가정"
    assert E.weakest(["확정", "미산정", "가정"]) == "미산정"
    with pytest.raises(ValueError):
        E.weakest(["모름"])


def test_to_columns_shape():
    cols = E.to_columns("x", E.V(3, "가정", ("D5", "L6")))
    assert cols == {"x": 3, "x__status": "가정", "x__src": "D5+L6"}


def test_engine_source_rules():
    """전략 문서 검증 5: fillna(0), random, score, 금지어가 엔진에 없다."""
    src = (ROOT / "engine_dcf.py").read_text(encoding="utf-8")
    code = "\n".join(l for l in src.splitlines() if not l.strip().startswith("#"))
    assert "fillna(0)" not in code
    assert not re.search(r"\brandom\b", code)
    assert "score" not in code.lower()


# ------------------------------------------------------------------ D 결핍

@pytest.fixture
def grid():
    return pd.DataFrame({
        "grid_id": ["g1", "g2", "g3", "g4"],
        "pop":     [100, 50, 30, 999],
        "pop_status": ["확정"] * 4,
        "served_by_built": [False, True, False, False],
        "reach_sites": ["S1", "S1", "S1;S2", "S3"],
    })


def test_irreplaceable_excludes_served(grid):
    v = E.d_irreplaceable_pop("S1", grid, P)
    assert v.value == 130            # g1 + g3, g2는 이미 조성 공원이 맡는다
    assert v.status == "확정"
    assert "D5" in v.src_keys and "L6" in v.src_keys


def test_shared_pop(grid):
    assert E.d_shared_pop("S1", grid, P).value == 30
    assert E.d_shared_pop("S2", grid, P).value == 30


def test_unserved_share(grid):
    assert E.d_unserved_share("S1", grid, P).value == pytest.approx(130 / 180)


def test_missing_pop_is_not_zero(grid):
    grid.loc[0, "pop"] = float("nan")
    v = E.d_irreplaceable_pop("S1", grid, P)
    assert v.value is None and v.status == "미산정"


def test_site_with_no_reach_is_zero(grid):
    assert E.d_irreplaceable_pop("S9", grid, P).value == 0


def test_unknown_park_type_is_missing():
    assert E.service_distance("주제공원", P).status == "미산정"
    assert E.service_distance("어린이공원", P).value == 250


def test_area_gap():
    sa = pd.DataFrame({"site_id": ["S1", "S2"], "admin_code": ["A", "B"]})
    ap = pd.DataFrame({"admin_code": ["A", "B"], "pop": [1000, 1000], "pop_status": ["확정", "확정"],
                       "built_park_area_m2": [4000, 7000]})
    assert E.d_area_gap("S1", sa, ap, P).value == pytest.approx(2.0)   # 6 − 4
    assert E.d_area_gap("S2", sa, ap, P).value == 0.0                  # 기준 충족


# ------------------------------------------------------------------ C 연결

def _patches(rows):
    return pd.DataFrame(rows, columns=["patch_id", "area_m2", "site_id"])


def test_two_patch_pc_analytic():
    """두 패치 PC 분자 = a1² + a2² + 2·a1·a2·p, p = 0.5^(d/D)."""
    pt = _patches([("A", 1000, None), ("B", 1000, "S1")])
    pdist = pd.DataFrame({"a": ["A"], "b": ["B"], "dist_m": [100.0]})
    res = E.c_dpc_by_distance(pt, pdist, P)
    r = res[(res.site_id == "S1") & (res.dispersal_m == 100)].iloc[0]
    p = 0.5
    base = 1000**2 * 2 + 2 * 1000 * 1000 * p
    expected = (base - 1000**2) / base * 100
    assert r.dpc == pytest.approx(expected)


def test_isolated_patch_equals_area_term():
    pt = _patches([("A", 5000, None), ("S", 1000, "S1")])
    pdist = pd.DataFrame({"a": ["A"], "b": ["S"], "dist_m": [1e6]})   # 사실상 단절
    r = E.c_dpc_by_distance(pt, pdist, P).query("dispersal_m == 100").iloc[0]
    assert r.dpc == pytest.approx(1000**2 / (5000**2 + 1000**2) * 100)


def test_stepping_stone_beats_area_share():
    """작은 징검다리 S가 큰 A·B를 이을 때, dPC(S)는 S 면적 몫보다 훨씬 크다."""
    pt = _patches([("A", 10000, None), ("S", 400, "S1"), ("B", 10000, None)])
    pdist = pd.DataFrame({"a": ["A", "S", "A"], "b": ["S", "B", "B"], "dist_m": [100.0, 100.0, 600.0]})
    r = E.c_dpc_by_distance(pt, pdist, P).query("dispersal_m == 300").iloc[0]
    area_only = 400**2 / (10000**2 * 2 + 400**2) * 100
    assert r.dpc > 10 * area_only


def test_small_patches_dropped():
    pt = _patches([("A", 299, "S1"), ("B", 5000, None)])
    pdist = pd.DataFrame({"a": ["A"], "b": ["B"], "dist_m": [10.0]})
    assert E.c_dpc_by_distance(pt, pdist, P).empty


def test_dpc_summary_flags_and_status():
    pt = _patches([("A", 10000, None), ("S", 400, "S1"), ("B", 10000, None), ("T", 3000, "S2")])
    pdist = pd.DataFrame({"a": ["A", "S", "B"], "b": ["S", "B", "T"], "dist_m": [150.0, 150.0, 650.0]})
    summ = E.c_dpc_summary(E.c_dpc_by_distance(pt, pdist, P), P, ["S1", "S2", "S3"])
    assert summ["S1"]["c_dpc_median"].status == "가정"
    assert "c_dpc_d100" in summ["S1"] and "c_dpc_d700" in summ["S1"]
    assert summ["S3"]["c_dpc_median"].status == "미산정"     # 패치가 없는 공원


# ------------------------------------------------------------------ F 실행

@pytest.fixture
def parcels():
    return pd.DataFrame({
        "site_id": ["S1"] * 4,
        "pnu": ["1", "2", "3", "4"],
        "jimok": ["임", "대", "전", "임"],
        "in_area_m2": [600.0, 100.0, 100.0, 200.0],
        "owner_class": ["국유", "사유", "사유", "공유"],
        "owner_count": [None, 3, 1, None],
    })


def test_public_ratio(parcels):
    assert E.f_public_ratio("S1", parcels, P).value == pytest.approx(0.8)


def test_public_ratio_missing_owner(parcels):
    parcels.loc[1, "owner_class"] = None
    v = E.f_public_ratio("S1", parcels, P)
    assert v.value is None and v.status == "미산정"


def test_private_owners_and_high_value(parcels):
    assert E.f_private_owners("S1", parcels, P).value == 4
    assert E.f_high_value_ratio("S1", parcels, P).value == pytest.approx(0.5)


@pytest.mark.parametrize("won,grade", [
    (9_999_999_999, "자체"), (10_000_000_000, "중앙"),
    (49_999_999_999, "중앙"), (50_000_000_000, "타당성조사"),
])
def test_review_grade_boundaries(won, grade):
    assert E.f_review_grade(E.V(won, "확정", ("D2",)), P).value == grade


def test_review_grade_missing_cost():
    assert E.f_review_grade(E.V(None, "미산정", ("R1",)), P).status == "미산정"


def test_start_margin():
    m = pd.DataFrame({"site_id": ["S1"], "lapse_year": [2030]})
    out = E.f_start_margin("S1", m, dt.date(2027, 1, 1), P, E.V("중앙", "가정", ("L8",)))
    # 2027-01 → 2030-01 = 36개월, 조성계획 12, 중앙 심사 6
    assert out["조성계획"].value == 18
    assert out["민간특례"].value == 36 - 48 - 6
    assert out["조성계획"].status == "가정"      # 연도만 있는 실효일은 가정


def test_start_margin_exact_date():
    m = pd.DataFrame({"site_id": ["S1"], "lapse_year": [2030], "lapse_date": ["2030-07-01"]})
    out = E.f_start_margin("S1", m, dt.date(2027, 1, 1), P)
    assert out["직접조성"].value == 42 - 30


def test_tables_have_status_for_every_value(grid, parcels):
    master = pd.DataFrame({"site_id": ["S1", "S2"], "park_type": ["근린공원", "주제공원"],
                           "area_m2": [1000, 500], "lapse_year": [2030, 2031]})
    sa = pd.DataFrame({"site_id": ["S1"], "admin_code": ["A"]})
    ap = pd.DataFrame({"admin_code": ["A"], "pop": [1000], "pop_status": ["확정"], "built_park_area_m2": [4000]})
    pt = _patches([("A", 10000, None), ("P1", 3000, "S1"), ("P2", 2000, "S2")])
    pdist = pd.DataFrame({"a": ["A", "A"], "b": ["P1", "P2"], "dist_m": [50.0, 400.0]})
    axis = pd.DataFrame({"site_id": ["S1"], "axis_dist_m": [120.0], "axis_status": ["가정"]})
    need = E.build_need_dc_table(master, grid, sa, ap, pt, pdist, axis, P)
    fx = E.build_exec_f_table(master, parcels, {"S1": E.V(12_000_000_000, "가정", ("D2", "R1"))},
                              dt.date(2027, 1, 1), P)
    for df in (need, fx):
        value_cols = [c for c in df.columns if c != "site_id" and "__" not in c]
        for c in value_cols:
            assert f"{c}__status" in df.columns and f"{c}__src" in df.columns
        E.assert_no_banned_words(df)
    s2 = need.set_index("site_id").loc["S2"]
    assert s2["d_irreplaceable_pop__status"] == "미산정"     # 유치거리 없는 유형
    assert fx.set_index("site_id").loc["S1", "f_review_grade"] == "중앙"
