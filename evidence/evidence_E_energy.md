# E. 열저감·에너지 근거 (조사일 2026-11-14) — energy 파트

## E1. 청주 실측: 숲 → 개발 시 지표온도 상승 (본 연구, GEE)
- 민간공원 특례사업지 개발 전(2013–16 여름)·후(2023–25 여름) Landsat 8·9 지표온도 비교. 개발 효과 = ΔLST(숲→개발) − ΔLST(숲 유지).
- 청주 시가지 전체 +3.48°C, 잠두봉 +2.23°C(주변 300m +0.94°C), 매봉 +2.43°C(주변 300m +0.58°C). 원자료·스크립트: `energy/data/gee/tukrye_before_after.json`.
- 쓰는 곳: 공원 밖으로 퍼지는 비율(주변 300m ÷ 공원 안) = 매봉 0.24 ~ 잠두봉 0.42 → `params.yaml` 의 `spillover_sites`.

## E2. 지표온도(LST) 차이 → 기온 차이 환산
- 하한: 유럽 392개 도시, 수관 피복 1%당 낮 지표온도 0.075°C 하강 vs 기온 0.006°C → 기온은 지표의 약 0.08배 (Du et al. 2024, Environ. Res. Lett. 19:044037, https://www.pnnl.gov/publications/daytime-cooling-efficiencies-urban-trees-derived-land-surface-temperature-are-much).
- 상한: 베이징 올림픽삼림공원 실측, 공원 안이 주변보다 기온 1.0–3.5°C, 지표 1.7–4.8°C 낮음 → 약 0.6~0.7배 (Remote Sensing 2021, https://doaj.org/article/c975980238d642aea099ecdfa904f329). 보수적으로 0.6 사용.

## E3. 공원 냉기가 퍼지는 거리
- 소형 녹지 30–120m에서 기온 0.4–0.8°C, 중형 180–330m에서 0.6–1.0°C 하강 (ACRS 2020 발표문이 인용한 2016 연구, https://a-a-r-s.org/./proceeding/ACRS2020/i1s8gy.pdf). → 1ha 미만 120m, 1ha 이상 300m.
- 본 연구 E1의 300m 고리와 같은 범위.

## E4. 기온 1°C당 전력 증가
- 최대전력: 기온 1°C 상승마다 1인당 21 ± 10.4 W 증가(11개 연구 종합) → 10.6 ~ 31.4 W/°C·인.
- 총전력: 1°C당 0.5% ~ 8.5% 증가(15개 연구 종합).
- 출처: Santamouris et al. 2015, Energy and Buildings 98:119–124, doi:10.1016/j.enbuild.2014.09.052 (https://dias.library.tuc.gr/view/56310?locale=en).

## E5. 1인당 냉방 전력
- 한국 1인당 냉방 전력 소비량 191.5 kWh (2022, 한국전력 집계 — 이코노미스트 2026.7.29 https://economist.co.kr/article/view/ecn202607290031).
- 연간 냉방전력 절감 = 주변 고리 인구(GHSL 2020) × 191.5 kWh × E4 증가율(%/°C) × 기온 저감. 증가율은 총전력 기준이라 냉방전력에 쓰면 보수적(과소).
- 참고(미사용): 2024 공동주택 중부 원단위 136 kWh/㎡(국토부, 뉴스서울 2025.7.30 https://newsseoul.co.kr/news/view/1065567616973781) — 난방·급탕 포함 총에너지라 여름 전력 계산에 쓰지 않음.

## E6. 원자료 (GEE)
- Landsat 8·9 Collection 2 Level-2 (USGS), Sentinel-2 L2A harmonized (ESA), ESA WorldCover v200 (2021), GHSL P2023A 인구(GHS_POP)·건물부피(GHS_BUILT_V) 2020 (EC JRC).
- 공원 경계: `biz/data/vworld/parks.txt` (V-World 도시계획시설 lt_c_uq162, 2026-11-13). 현재 이용상황: `biz/data/vworld/parcel_attr.txt` (토지특성 2026).
