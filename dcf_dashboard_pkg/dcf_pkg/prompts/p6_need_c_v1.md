# 프롬프트 6 — C 연결 전처리와 dPC (12주차, 백엔드) v1

역할: 너는 경관생태 네트워크를 다루는 Python 개발자다.
목표: prep/prep_c_patches.py로 data/patches.csv, patch_dist.csv, site_axis.csv를 만들고,
      engine_dcf.c_dpc_by_distance로 reports/c_dpc_long.csv를 만든다.
입력: data/landcover.gpkg(D9) 또는 data/biotope.gpkg(C2, 있으면 우선), data/built_parks.gpkg,
      data/park_boundary.geojson, data/green_axes.gpkg(C3), params_dcf.yaml
제약:
- 녹지로 보는 토지피복 코드 목록을 README에 적고, 그 목록만 쓴다.
- 이동거리는 params의 네 값을 모두 계산한다. 하나만 고르지 마라.
- dPC는 항상 status='가정'이다.
- Conefor 2.6으로 2개 공원을 따로 계산해 엔진 값과 비교한다(상대오차 1% 이내).
테스트(pytest):
- patches의 area_m2 ≥ min_patch_m2
- 40개소 각각에 패치가 하나 이상 있거나, 없으면 reports/c_no_patch.csv에 이름이 있다
- 이동거리가 커지면 PC 분자가 줄지 않는다
