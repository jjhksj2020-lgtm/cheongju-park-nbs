# 프롬프트 5 — D 결핍 전처리 실행·보완 (11~12주차, 백엔드) v1

역할: 너는 geopandas·osmnx를 쓰는 Python 데이터 엔지니어다.
목표: prep/prep_d_reach.py를 실데이터로 돌려 data/grid_reach.csv와 data/site_admin.csv를 만든다.
입력: data/sgis_grid_100m.gpkg(D5), data/built_parks.gpkg(D6+D4), data/park_boundary.geojson(D4),
      data/master_d0.csv(D0, 읽기 전용), data/admin_dong.gpkg(D8), params_dcf.yaml
할 일:
1. 스크립트를 실행하고 막히는 곳만 고친다. 계산식(engine_dcf.py)은 바꾸지 마라.
2. --factor 0.5 / 1.0 / 1.5 세 번 돌려 grid_reach_f0.5.csv, grid_reach.csv, grid_reach_f1.5.csv를 만든다.
3. reports/d_check.csv: 공원별 유치권 격자 수, 대체 불가 인구, 조성 공원과 겹치는 격자 수.
제약:
- 40개소는 공급(조성 공원)에 넣지 마라.
- 인구가 빈 격자를 0으로 채우지 마라(엔진이 '미산정'으로 처리한다).
- OSM 보행망을 쓰면 params의 need_d.network_status를 '가정'으로 둔다.
테스트(pytest):
- grid_reach의 reach_sites에 master에 없는 site_id가 없다
- factor 1.5의 유치권 격자 수 ≥ factor 1.0 ≥ factor 0.5 (모든 공원)
- served_by_built인 격자는 어떤 공원의 d_irreplaceable_pop에도 들어가지 않는다
