# GitHub Copilot / Cursor / Claude Code 바이브코딩 요청 예시

다음 프롬프트는 **기존 저장소 전체를 읽을 수 있는 코딩 도구**에 붙여 넣어 사용하세요.

> 너는 GIS·MapLibre GL JS·Python GeoPandas와 공공정책 대시보드 개발자다.
> 현재 저장소의 `engine.py`, `engine_dcf.py`, `params*.yaml`, `prep/`, `data/`, `supabase/`를 먼저 확인하라.
> 첨부된 `docs/index.html`, `docs/app.js`, `docs/style.css`, `scripts/export_map3d.py`를 기존 저장소에 통합한다.
> 
> 반드시 지켜야 할 사항:
> 1. 대상은 청주시 공고 제2026-2004호의 장기미집행 공원 40개소이다. 공식 `site_id` 1~40만 사용한다.
> 2. 필요성 N의 판단(존치·조성/존치/보류)을 사업성 F 또는 K2·K4 수치가 변경하면 안 된다.
> 3. 실제 경계 좌표가 없으면 지도를 공원 위치처럼 꾸며서 표시하지 않는다. 실제 GeoJSON의 polygon만 렌더링한다.
> 4. 숫자는 `(value, status, src)` 3종을 함께 저장한다. 자료 없는 값은 null / `미산정`이고, 임의 0은 금지한다.
> 5. `engine_dcf.py`의 함수와 기존의 판정 규칙1~5는 수정하지 않는다.
> 6. `D` 서비스권, `C` 연결성, `F` 국공유지 비율·기투자·착수 여유, `K2` 시 순재정부담, `H` LST 레이어를 선택할 수 있게 만든다. 입력이 아직 없는 K2/H는 회색/미산정으로 남긴다.
> 7. 3D 돌출 높이는 지표의 **상대값**일 뿐 물리적인 표고가 아니다. 실제 지형이 필요한 경우 DEM을 별도 계층으로 표시한다.
> 8. 지도 클릭 시 `site_id`, 공원명, 필요성 판정, 공고 단계, 선택 지표, 출처키, 상태를 노출한다.
> 9. GeoJSON은 EPSG:4326(WGS84)여야 한다. EPSG:5186 입력을 GeoPandas에서 적절하게 변환한다.
> 10. `docs/`를 GitHub Pages 정적 페이지로 게시할 수 있도록 README에 안내를 추가한다. Python 엔진은 GitHub Pages에서 돌릴 수 없으므로 로컬 또는 CI에서 계산한 결과만 게시한다.
> 11. 사용자가 제공한 `supabase` 정책은 authenticated만 읽기 가능하다. 무단으로 anon 정책을 열거나 브라우저에 service_role 키를 노출하지 않는다.
> 12. 인구·토지 원자료에 개인정보 또는 비공개 계약자료가 들어 있으면 공개 GitHub 저장소에 업로드하지 않는다.
> 
> 완료 기준:
> - 40개 site_id 매칭·좌표계·결측·출처·상태 자동 검증
> - 2D/3D 전환, D/C/F/K2/H 지표 전환, 클릭 팝업, 범례 기능 확인
> - 합성 데이터 테스트와 실제 원자료 검산을 별도로 보고
> - GitHub Pages에서 생성 파일이 정상 로드되는지 Network/Console 검사
> - 실패한 데이터 소스와 미구현 기능은 명시하고 절대 임의값으로 대체하지 않기

## 폴더 배치

- `docs/` → 브라우저 지도 화면 + 계산 결과 `parks_3d.geojson`
- `scripts/export_map3d.py` → 파이썬 지표/경계 결합 및 지도 데이터 변환
- 기존 계산/공간전처리 코드는 수정하지 않음
