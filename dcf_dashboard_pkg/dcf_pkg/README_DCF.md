# D 결핍 · C 연결 · F 실행 — 대시보드 연결 패키지

조사 문서: https://claude.ai/artifact/7YBTZxbsr1hqSvEs1e348z
대시보드 규약: 「청주 장기미집행 공원 대시보드 개발 전략 — 사업성 파트」(site_id, src_key, status, params.yaml, 순수 함수)

## 저장소에 넣는 위치

| 파일 | 넣을 곳 | 하는 일 |
|---|---|---|
| engine_dcf.py | 저장소 루트(engine.py 옆) | D·C·F 순수 함수. 모든 값은 (value, status, src_keys) |
| params_dcf.yaml | 루트 (또는 params.yaml에 세 블록을 붙여 넣기) | 유치거리, 이동거리, 심사 기준, 리드타임 |
| prep/prep_d_reach.py, prep/prep_c_patches.py | prep/ | 공간 전처리(geopandas·osmnx). **실데이터 실행 전** |
| data/sources_dcf.csv | data/ | 출처 탭에 이어 붙일 출처키 D5~D12, C2~C4, L6~L8, P1~P2 |
| data/methodology_dcf.csv | data/ | 방법론 탭에 이어 붙일 지표·산식 |
| data/limits_dcf.csv | data/ | 한계 탭에 이어 붙일 한계 D-1~F-3 |
| data/columns_*.txt | data/ | 판정표 열 이름(팀 합의용) |
| supabase/migrations/20261119000001_dcf_indicators.sql | supabase/migrations/ | need_dc, exec_f_ext 표 (Supabase를 쓸 때만) |
| scripts/gen_migration_dcf.py | scripts/ | 열이 바뀌면 SQL·열 목록을 다시 만든다 |
| prompts/p5~p7 | prompts/ | 바이브코딩 프롬프트(기존 1~4 다음 번호) |
| tests/test_dcf.py | tests/ | 합성 데이터 테스트 26개 |

## 규약

- 값 열 x마다 `x__status`(확정/가정/미산정)와 `x__src`(출처키를 `+`로 이음)를 둔다.
  기존 판정표가 다른 형식이면 `engine_dcf.to_columns` 한 곳만 고친다.
- D·C(`need_dc`)는 **필요성 파트의 입력**이다. 판정은 필요성 파트가 낸다. 사업성 화면은 이 표를 읽지 않는다.
- F 확장(`exec_f_ext`)은 사업성 판정표에 site_id로 붙는다. 규칙1~5의 결과는 바꾸지 않는다.
- 지표 번호(D1~D5, C1~C5, F1~F8)는 조사 문서용이다. 출처키 D0~D12·C1~C4와 겹치므로 **코드에서는 열 이름만 쓴다**.

## 실행

```bash
pip install pandas numpy scipy networkx pyyaml pytest      # 엔진·테스트
pip install geopandas osmnx                                # prep/ 전처리
pytest -q                                                  # 26 passed
python prep/prep_d_reach.py --factor 1.0                   # → data/grid_reach.csv, site_admin.csv
python prep/prep_c_patches.py                              # → data/patches.csv, patch_dist.csv, site_axis.csv
```

```python
import datetime as dt, pandas as pd, engine_dcf as E
P = E.load_params("params_dcf.yaml")
need = E.build_need_dc_table(master, grid_reach, site_admin, admin_park, patches, patch_dist, site_axis, P)
fx = E.build_exec_f_table(master, park_parcel, total_cost, dt.date(2026, 11, 19), P)
E.assert_no_banned_words(need); E.assert_no_banned_words(fx)
need.to_csv("data/need_dc.csv", index=False)
```

## 팀 합의가 필요한 것

1. 판정표의 status·src 열 형식(`__status`, `__src`)
2. 규칙5 정렬 키의 '실효일'을 F5 착수 여유(f_margin_*)로 바꿀지
3. 녹지로 보는 토지피복 코드 목록
4. 중앙 투자심사 금액 기준(현재 100억, '가정')
