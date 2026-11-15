# 필요성 · 이용성(E·D)과 연결성(C) 지표

청주시 기준 **② 이용성**(E1·E2·D1·D2)과 **① 공원조성 가치 중 C1**(녹지축 거리)을 계산한다.
지표 정의는 `docs/청주_장기미집행공원_중간보고서.pdf` 2-3 (가).

> 이 폴더 밖은 고치지 않는다. 결과는 `need/out/indicators_edc.csv` 하나로만 넘긴다.

## 지표

| 지표 | 산식 | 자료 (출처키) |
|---|---|---|
| E1 버퍼 인구 | 공원 경계 + 버퍼(`presets.yaml` buffer_m) 안 인구, 면적 가중 | SGIS 격자·집계구 인구 (SGIS-grid) |
| E2 취약인구 비율 | 버퍼 안 (65세 이상 + 9세 이하) ÷ 버퍼 인구 | SGIS 연령별 인구 (SGIS-grid) |
| D1 서비스권 밖 인구 비율 | 기존 조성공원 유치거리 합집합 밖 버퍼 인구 ÷ 버퍼 인구 | 전국도시공원정보표준데이터 + 시행규칙 별표3 |
| D2 생활권 1인당 공원면적 | 공원이 속한 생활권 값 | 2030 도시기본계획 표 7-10 (CJ-park) |
| C1 녹지축 거리 | 공원 경계 → 4대 녹지축·5대 수변생태축 최단거리(m) | 제안서 p.9 도면 디지타이징 (SJ-axis) |
| (참고) 신규 수혜 인구 | 조성 시 처음 서비스권에 들어오는 인구 | D1 계산 부산물 |

- `C1_near`, `river_adjacent` 플래그(1/0)는 사업성 파트 `need.csv`에 들어간다(`biz/data/input/need.TEMPLATE.csv`).
- |r| ≥ 0.7이면 하나만 쓴다(D1↔E1). 용도지역 비율은 개발압력 P2와 겹치므로 점수에 넣지 않는다.

## 지금 쓰는 자료 (1차, 모두 tag `대체자료` 또는 `가정`)

| 출처키 | 자료 | 받는 법 | 교체 계획 |
|---|---|---|---|
| WP-2020 | WorldPop 2020 100m constrained 인구(전체·성별 연령 밴드) | data.worldpop.org, `data/raw/worldpop/` (용량이 커서 저장소에 안 올림) | SGIS 격자·집계구 인구(키 발급 후) |
| OSM-2026-11 | OpenStreetMap 공원·놀이터, 하천, 산림 (2026-11-15 Overpass) | `data/raw/osm/*.json` | 청주시 공원현황 표·V-World 도시계획시설 |
| — | D2: 구별 1인당 기존 공원면적 (OSM 공원 ÷ WorldPop) | 계산 | 2030 도시기본계획 표 7-10 생활권 값 |
| — | C1: 수변축 하천(params `axis_rivers`)·50ha 이상 산림까지 최단거리 | 계산 | 제안서 녹지축 도면 원본 |

기준값(유치거리, 플래그 경계, 하천 목록)은 `code/params.yaml`에만 있다.

**E2는 미산정이다.** WorldPop 연령 밴드는 넓은 행정구역의 연령 비율을 격자에 똑같이 나눠 놓은 자료라서, 모든 공원이 0.285로 같게 나왔다. 공원 사이의 차이를 보려면 SGIS 집계구 연령별 인구나 행안부 행정동 연령별 주민등록인구가 필요하다.

## 1차 결과 (2026-11-15)

- 산정 39/40 (5 어린이공원152는 경계가 없어 미산정). 버퍼 인구가 0인 곳은 33·34 두 곳이다.
- WorldPop 청주 총인구 90.2만 명 (주민등록 89.0만 명, 2026.8): 약 1% 차이.
- r(D1, E1)은 pearson −0.41, spearman −0.60으로 |r| < 0.7이라 둘 다 쓴다.
- C1은 50ha 이상 산림이 많아서 대부분 가깝게 나온다(C1_near 1이 28곳). 녹지축 도면을 받기 전에는 변별력이 약하다.

## 실행

```bash
pip install shapely pyproj pyyaml rasterio numpy
cd need/edc/code && python build_edc.py
```

결과: `need/out/indicators_edc.csv`(긴 표, 점수 계산용), `need/out/edc_wide.csv`(공원별 가로표, 검토용).
`data/raw/worldpop/`이 비어 있으면 아래로 받는다(약 160MB).

```bash
cd need/edc/data/raw/worldpop
curl -O https://data.worldpop.org/GIS/Population/Global_2000_2020_Constrained/2020/BSGM/KOR/kor_ppp_2020_UNadj_constrained.tif
for s in f m; do for a in 0 1 5 65 70 75 80; do curl -O https://data.worldpop.org/GIS/AgeSex_structures/Global_2000_2020_Constrained/2020/KOR/kor_${s}_${a}_2020_constrained.tif; done; done
```

## 폴더

```
need/edc/
  README.md
  indicators_edc.TEMPLATE.csv   결과 양식
  code/        계산 스크립트
  data/raw/    받은 원자료 (출처키별)
```

## 결과 양식

`site_id, indicator, value, unit, source_key, tag` — tag는 `실자료 / 가정 / 미산정 / 대체자료`.
공원 경계는 `biz/data/vworld/parks.txt`를 읽기만 한다(복사·수정 금지).
