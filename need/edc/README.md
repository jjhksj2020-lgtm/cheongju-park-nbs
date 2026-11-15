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
