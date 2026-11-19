"""engine_dcf 결과 열에서 Supabase 마이그레이션과 열 목록을 만든다. 열을 바꾸면 이 스크립트를 다시 돌린다."""
import datetime as dt
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import engine_dcf as E  # noqa: E402

P = E.load_params("params_dcf.yaml")
grid = pd.DataFrame({"grid_id": ["g"], "pop": [1], "pop_status": ["확정"], "served_by_built": [False], "reach_sites": ["S1"]})
master = pd.DataFrame({"site_id": ["S1"], "park_type": ["근린공원"], "area_m2": [1], "lapse_year": [2030]})
pt = pd.DataFrame({"patch_id": ["A", "B"], "area_m2": [1000, 1000], "site_id": [None, "S1"]})
pdist = pd.DataFrame({"a": ["A"], "b": ["B"], "dist_m": [10.0]})
need = E.build_need_dc_table(
    master, grid, pd.DataFrame({"site_id": ["S1"], "admin_code": ["A"]}),
    pd.DataFrame({"admin_code": ["A"], "pop": [1], "pop_status": ["확정"], "built_park_area_m2": [1]}), pt, pdist,
    pd.DataFrame({"site_id": ["S1"], "axis_dist_m": [1.0], "axis_status": ["가정"]}), P)
pp = pd.DataFrame({"site_id": ["S1"], "pnu": ["1"], "jimok": ["임"], "in_area_m2": [1.0], "owner_class": ["국유"], "owner_count": [None]})
fx = E.build_exec_f_table(master, pp, {"S1": E.V(1, "확정", ("D2",))}, dt.date(2027, 1, 1), P)

INT = {"d_irreplaceable_pop", "d_shared_pop", "c_rank_spread", "f_private_owners"}


def typ(c):
    if c.endswith("__status") or c.endswith("__src") or c == "f_review_grade":
        return "text"
    if c == "c_assumption_dependent":
        return "boolean"
    if c in INT or c.startswith("f_margin_"):
        return "integer"
    return "double precision"


def table(name, df, comment):
    cols = [f'  "{c}" {typ(c)}' for c in df.columns if c != "site_id"]
    chk = [f"  check (\"{c}\" in ('확정','가정','미산정'))" for c in df.columns if c.endswith("__status")]
    return (f"-- {comment}\ncreate table if not exists public.{name} (\n  site_id text primary key,\n"
            + ",\n".join(cols + chk)
            + ",\n  data_base_date date not null,\n  updated_at timestamptz not null default now()\n);\n"
            f"alter table public.{name} enable row level security;\n"
            f"create policy \"{name}_read\" on public.{name} for select to authenticated using (true);\n"
            "-- 쓰기는 service_role(서버의 계산 엔진)만 한다. 키는 클라이언트에 두지 않는다.\n\n")


sql = ("-- D 결핍 · C 연결 · F 실행 지표 표. 열 이름은 engine_dcf.build_*_table 결과와 같다.\n"
       "-- 값 열마다 <열>__status(확정/가정/미산정)와 <열>__src(출처키를 +로 이음)를 둔다.\n"
       "-- 이 파일은 scripts/gen_migration_dcf.py가 만든다. 손으로 고치지 않는다.\n\n"
       + table("need_dc", need, "필요성 파트 입력(판정 아님)")
       + table("exec_f_ext", fx, "사업성 판정표에 붙는 F 확장 열"))
pathlib.Path("supabase/migrations/20261119000001_dcf_indicators.sql").write_text(sql, encoding="utf-8")
pathlib.Path("data/columns_need_dc.txt").write_text("\n".join(need.columns) + "\n", encoding="utf-8")
pathlib.Path("data/columns_exec_f_ext.txt").write_text("\n".join(fx.columns) + "\n", encoding="utf-8")
print("need_dc", len(need.columns), "exec_f_ext", len(fx.columns))
