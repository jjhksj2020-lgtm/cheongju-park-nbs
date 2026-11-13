# 필요성 파트 작업 폴더

산출물: `out/need.csv` — 열: `site_id, grade(상/중/하), verdict(존치·조성/존치/보류), H1_high, industrial_downwind, C1_near, river_adjacent, refund_eligible` (플래그 1/0)

- 지표·산식·프리셋은 `docs/청주_장기미집행공원_중간보고서.pdf` 2-3 (가).
- 상수(버퍼 반경, 유치거리, 프리셋 가중치)는 `presets.yaml`에만 쓴다.
- 원자료 응답은 `../data/raw/`에 저장하고 출처키를 붙인다.
