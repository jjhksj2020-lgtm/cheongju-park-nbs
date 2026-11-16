# -*- coding: utf-8 -*-
"""
청주 장기미집행 공원 40개소 — 필요성(H 열환경) 대시보드
실행:  pip install -r requirements.txt  →  streamlit run app.py
데이터: ../data/H_results_40parks.csv  (GEE 2026-11-16 결과 + V-World 좌표)
"""
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import pydeck as pdk

st.set_page_config(page_title="청주 공원 열환경 DSS", layout="wide")

# ---------- 데이터 ----------
@st.cache_data
def load():
    df = pd.read_csv("../data/H_results_40parks.csv")
    num = ["lon", "lat", "area_m2", "lsta", "ndvi", "pop300", "vol300"]
    for c in num:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

df = load()
B_CONTROLLED = -10.135   # 청주 전역 회귀: NDVI 1.0당 ℃ (GEE 2026-11-14)
NDVI_TREE, NDVI_GRASS = 0.863, 0.535

# ---------- 사이드바: 시나리오 ----------
st.sidebar.header("시나리오")
scen = st.sidebar.radio("조성 유형", ["수목형 (NDVI 0.86)", "잔디형 (NDVI 0.54)"])
target = NDVI_TREE if scen.startswith("수목") else NDVI_GRASS
b = st.sidebar.slider("녹지→온도 계수 (℃ / NDVI)", -16.9, -5.0, float(B_CONTROLLED), 0.1,
                      help="−10.1 = 건물밀도 통제 회귀, −16.9 = 단순 회귀")
w_heat = st.sidebar.slider("가중치: 현재 더위", 0.0, 1.0, 0.5, 0.05)
w_pop  = st.sidebar.slider("가중치: 주변 인구", 0.0, 1.0, 0.5, 0.05)
types = st.sidebar.multiselect("공원 유형", sorted(df["type"].dropna().unique()), default=sorted(df["type"].dropna().unique()))

# ---------- 계산 (시나리오에 따라 매번) ----------
d = df[df["type"].isin(types)].copy()
d["dndvi"] = (target - d["ndvi"]).clip(lower=0)
d["cool"] = b * d["dndvi"]                       # ℃, 음수 = 냉각
d["lst_after"] = d["lsta"] + d["cool"]
d["benefit"] = d["cool"].abs() * d["pop300"]      # 명·℃
ok = d["lsta"].notna()
d.loc[ok, "heat_grade"] = pd.qcut(d.loc[ok, "lsta"].rank(ascending=False, method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
# 필요성 점수(H 부분): 현재 더위 등수 + 편익 등수, 가중
d.loc[ok, "r_heat"] = d.loc[ok, "lsta"].rank(pct=True)
d.loc[ok, "r_ben"]  = d.loc[ok, "benefit"].rank(pct=True)
d.loc[ok, "H_score"] = (w_heat * d.loc[ok, "r_heat"] + w_pop * d.loc[ok, "r_ben"]) / max(w_heat + w_pop, 1e-9)
d.loc[ok, "H_rank"] = d.loc[ok, "H_score"].rank(ascending=False, method="first").astype(int)
d["grade"] = np.where(d["H_score"] >= d["H_score"].quantile(0.7), "상",
             np.where(d["H_score"] >= d["H_score"].quantile(0.3), "중", "하"))
d.loc[~ok, "grade"] = "미산정"

# ---------- 상단 요약 ----------
st.title("청주 장기미집행 공원 40개소 — 열환경(H) 필요성")
c1, c2, c3, c4 = st.columns(4)
c1.metric("분석 공원", f"{ok.sum()} / {len(d)}")
c2.metric("평균 예상 냉각", f"{d.loc[ok,'cool'].mean():.1f} ℃")
c3.metric("현재 가장 더운 곳", f"{d.loc[ok].sort_values('lsta').iloc[-1]['name']} (+{d['lsta'].max():.1f}℃)")
c4.metric("편익 1위", d.loc[ok].sort_values("benefit").iloc[-1]["name"])
st.caption("출처: Landsat 8/9 82장·Sentinel-2 14장 (GEE, 2026-11-14) · 인구 300m 버퍼 · 좌표는 동·리 중심 근사(가정) · '해제'라는 표현은 쓰지 않음")

# ---------- 지도 + 순위 ----------
left, right = st.columns([3, 2])
with left:
    st.subheader("지도 — 색: 현재 온도 편차, 크기: 냉각 편익")
    m = d[ok & d["lon"].notna()].copy()
    def color(v):  # 파랑(시원) → 빨강(더움)
        t = (v - m["lsta"].min()) / (m["lsta"].max() - m["lsta"].min() + 1e-9)
        return [int(255 * t), int(80 * (1 - abs(t - 0.5) * 2)), int(255 * (1 - t)), 190]
    m["color"] = m["lsta"].apply(color)
    m["radius"] = 150 + 600 * (m["benefit"] / (m["benefit"].max() + 1e-9))
    layer = pdk.Layer("ScatterplotLayer", m, get_position="[lon, lat]", get_fill_color="color",
                      get_radius="radius", pickable=True)
    st.pydeck_chart(pdk.Deck(layers=[layer], map_style=None,
        initial_view_state=pdk.ViewState(latitude=36.64, longitude=127.49, zoom=10.3),
        tooltip={"text": "{name}\n현재 {lsta}℃ · 녹지 {ndvi}\n조성 시 {cool}℃ · 편익 {benefit}\n등급 {grade}"}))
with right:
    st.subheader("필요성(H) 순위")
    show = d[ok].sort_values("H_rank")[["H_rank", "name", "type", "grade", "lsta", "cool", "benefit", "heat_grade"]]
    show.columns = ["순위", "공원", "유형", "등급", "현재 ℃", "냉각 ℃", "편익", "열등급"]
    st.dataframe(show.round(2), hide_index=True, height=520)

# ---------- 차트 ----------
st.subheader("조성 전 → 후 예상 온도 (청주 평균 대비 ℃)")
t = d[ok].sort_values("lsta", ascending=False)
fig = px.bar(t, x="name", y=["lsta", "lst_after"], barmode="group",
             labels={"value": "℃ (청주 평균 대비)", "name": "", "variable": ""},
             color_discrete_map={"lsta": "#d6604d", "lst_after": "#4393c3"})
fig.for_each_trace(lambda tr: tr.update(name={"lsta": "현재", "lst_after": "조성 후"}[tr.name]))
fig.update_layout(height=380, legend=dict(orientation="h"))
st.plotly_chart(fig, use_container_width=True)

# ---------- 시설별 근거 카드 ----------
st.subheader("시설별 근거 문단")
pick = st.selectbox("공원 선택", d[ok].sort_values("H_rank")["name"])
r = d[d["name"] == pick].iloc[0]
st.markdown(f"""
**{r['name']} ({r['addr']}, {int(r['expire_yr'])} 실효) — 필요성 {r['grade']}, 열환경 {int(r['heat_grade'])}등급, H 순위 {int(r['H_rank'])}위**

이 자리는 여름 지표온도가 청주 평균보다 **{r['lsta']:+.1f}℃** 이고 녹지 정도(NDVI)는 **{r['ndvi']:.2f}** 이다 [Landsat/S2 2026-11].
{scen.split(' ')[0]} 공원으로 조성하면 녹지가 {r['ndvi']:.2f}→{target:.2f} 로 올라 **약 {abs(r['cool']):.1f}℃** 내려갈 것으로 추정된다 (청주 전역 회귀 {b:.1f}℃/NDVI).
300m 안에 **{int(r['pop300']):,}명** 이 살아 냉각 편익은 **{int(r['benefit']):,} 명·℃** 로 {ok.sum()}곳 중 **{int(d.loc[ok,'benefit'].rank(ascending=False)[r.name])}위** 다.
판정: {'존치·조성 후보' if r['grade']=='상' else ('존치' if r['grade']=='중' else '보류 (다른 축 검토)')}.
""")

st.download_button("결과 CSV 내려받기", d.to_csv(index=False).encode("utf-8-sig"), "parks_H_scenario.csv")
