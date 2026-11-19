# 청주시 장기미집행 공원 40개소 — 3D GIS GitHub Pages 추가 모듈

이 ZIP은 기존 `dcf_dashboard_pkg.zip`에 **추가**하는 전시/시각화 코드입니다. 기존 D/C/F 엔진을 변경하지 않습니다.

## 실제로 보이는 것
- 공원 폴리곤의 **상대값 3D 돌출** (3D 원근 지도; 실제 지형 높이/건물 높이와 다름)
- D 결핍, C 연결, F 실행, K2 재정부담, LST/열저감 지표 전환
- 원자료 값이 없으면 **회색/미산정** (실데이터를 가짜로 채우지 않음)
- 공원 클릭 → 지표값, 판정, 출처 키, 확정/가정/미산정 표시
- 2D/3D 시점 전환

## 준비해야 할 실제 데이터

`data/park_boundary.geojson` — **40개소 정확한 경계 Polygon/MultiPolygon** + 공식 `site_id` (1~40) 열. CRS를 알 수 있어야 함. `park_name`만 있을 경우 공식 마스터와 검증된 매핑 테이블을 거쳐 `site_id`를 먼저 붙이세요.

입력 데이터(존재하는 것부터):
- `data/master_d0.csv` — site_id, park_name, park_type, lapse_year 등
- `data/need_dc.csv` — `engine_dcf.build_need_dc_table` 출력; **현재 사용자의 ZIP에 미포함**
- `data/exec_f_ext.csv` — `engine_dcf.build_exec_f_table` 출력; **현재 ZIP에 미포함**
- `data/finance_k2k4.csv` (선택) — site_id, `k2_city_burden_won`, `k4_invested_won` 및 각각의 `__status`, `__src`
- `data/heat_metrics.csv` (선택) — site_id, `lst_mean_c`, `heat_reduction_c` 및 각각의 `__status`, `__src`

**열저감**은 LST와 같은 값이 아닙니다. `heat_reduction_c`는 복원 전후를 비교한 실측 또는 명시된 모델링 결과만 넣으세요.

> 현재 사용자 ZIP에는 위 실데이터와 3D 프런트엔드가 들어 있지 않습니다. 이 도구는 입력 없이 수치를 생성하지 않습니다.

## 배치와 실행

1. 이 ZIP을 풀어 `docs/` 와 `scripts/export_map3d.py`를 기존 GitHub 저장소 루트에 복사합니다.
2. 로컬 환경에서 `pip install geopandas pandas`.
3. 필요한 데이터를 준비하고 다음 중 해당 명령을 실행합니다.

```bash
# 먼저 공원 경계만으로 표시. 지표는 회색/미산정
python scripts/export_map3d.py --boundary data/park_boundary.geojson --master data/master_d0.csv

# D·C / F 계산이 끝난 후
python scripts/export_map3d.py --boundary data/park_boundary.geojson --master data/master_d0.csv --need data/need_dc.csv --exec data/exec_f_ext.csv

# 사업성과 온도 자료도 확보한 경우
python scripts/export_map3d.py --boundary data/park_boundary.geojson --master data/master_d0.csv --need data/need_dc.csv --exec data/exec_f_ext.csv --finance data/finance_k2k4.csv --heat data/heat_metrics.csv
```

4. `docs/parks_3d.geojson`이 생성됩니다. `docs/index.html`, `docs/app.js`, `docs/style.css`와 함께 GitHub에 커밋하세요.
5. 저장소 Settings → Pages → **Deploy from a branch** → `main` → `/docs` → Save. 기존 저장소가 이미 Pages를 운영한다면 기존 설정에 맞춰 해당 폴더를 게시하도록 합치세요.
6. Pages 주소에서 지표를 전환합니다. GitHub Pages는 정적 파일만 서빙하므로 **Python 계산은 Pages에서 실행되지 않습니다**. 계산 후 GeoJSON을 재생성해 업로드해야 합니다.

## 향후 고도화

- **실제 지형 3D**: MapLibre raster-DEM 지형 타일 소스를 추가하거나, VWorld 3D API 기반 화면으로 전환. DEM 제공자의 이용조건·키 필요 여부 확인.
- **열환경 격자/래스터**: LST GeoTIFF → 서버/정적 타일로 변환 → 히트 래스터 오버레이. 공원별 평균 LST만 있을 때는 현재와 같이 공원 단위 색칠만 가능합니다.
- **보행 서비스권**: `prep_d_reach`의 결과 CSV는 격자 ID만 있으므로 SGIS 격자 GeoJSON과 결합해야 서비스권이 지도 영역으로 보입니다.
- **녹지 네트워크 선**: `patch_dist.csv`에는 간선 ID와 거리만 있어, patch geometry를 보존해 선/패치 GeoJSON으로 별도 내보내야 합니다.
- **Supabase 실시간 연결**: 현재 원본 migration RLS는 `authenticated`만 SELECT 허용. 로그인 없는 GitHub Pages에서 직접 익명 조회할 수 없음. 공개할 값만 서버에서 승인해 정적 GeoJSON으로 내보내는 방식이 안전합니다. service_role 키를 브라우저에 노출하면 안 됩니다.

## 최소 검증 기준

1. 공고 40개 `site_id` 전수 일치, 폴리곤 개수 정확히 40, 중복/빈 경계 0.
2. 좌표계 EPSG:4326 변환 후 청주시 일대에 표시되는지 확인.
3. D·C·F·K2·열환경 값은 원본 CSV와 **site_id별 동일**해야 함.
4. `미산정`은 0이 아닌 Null/회색, `가정`은 출처를 표시.
5. F·K2 표시가 N 등급/존치·조성 판정을 수정하지 않도록 유지.
6. 지도 색과 3D 상대높이는 선택 지표에 따라 갱신되는지, 2D/3D 전환과 클릭 상세가 작동하는지 확인.
7. 브라우저 개발자 도구 Console/Network에서 GeoJSON 404, 타일 네트워크 오류를 확인.

**유의**: 이 데모는 공원별 수치를 3D로 시각화하는 화면이며 건물·산악 지형 자체가 실제 3D인 모델은 아닙니다. 실제 지형이 필요하면 DEM/3D Tiles를 별도로 연동해야 합니다.
