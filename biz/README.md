# 청주 장기미집행 공원 40개소 — 사업성 룰 엔진

실행: `pip install pyyaml` 후 `python biz_engine.py` (Python 3.9+). 다른 프로그램 설치 불필요.

## 지금 상태에서 되는 것
공고 40개소 표(data/sites.csv)와 청주 실적 단가만으로 보상·조성 범위, 특례 가능, 시 부담 최대·최소, 단계, 8개 시나리오, 카드 40장이 나온다.
단, 토지소유 미수령이라 사유지 100% 가정(상한)이고 국비 요건·필요성 등급은 "미수령"으로 표시된다.

## 실데이터를 넣는 순서 (파일 세 개만 채우면 됨)
1. data/need.csv  ← 필요성 파트 산출 (등급·판정·H1·C1 플래그). 템플릿: need.TEMPLATE.csv
2. data/land_own.csv  ← 토지소유 구분. 국가공간정보포털(nsdi.go.kr) 회원가입 → 오픈마켓 "토지소유정보" 또는 선진 통해 청주시 요청. 템플릿: land_own.TEMPLATE.csv
3. data/land_price.csv ← 개별공시지가. vworld.kr 회원가입 → 오픈API 인증키 신청(무료, 즉시) → 지번별 조회. 템플릿: land_price.TEMPLATE.csv
   수집 코드는 제출물 2 §2-6 예시 3 프롬프트로 생성. 호출 도메인은 api.vworld.kr만.

파일을 넣고 다시 실행하면 열은 그대로, 값만 바뀐다. 파일이 없으면 가정값으로 돌고 카드에 "가정/미수령"이 찍힌다.

## 출력 (out/)
- master_biz.csv — 40행 사업성 열 (범위 + 기준 시나리오 단계·이유·출처키)
- scenarios.csv — 8개 시나리오 단계, stage_stable, 전환값
- cards/*.md — 후보지 카드 사업성 블록 40장
- summary.md — RQ4·RQ5 판정, 경계 후보지, 월명공원 재현 검증

## 검증 (제출물 2 §2-6)
- 월명공원 재현: 상한 단가로 보상 351억·조성 63억 ±1% → summary.md에 통과/실패
- 코드에 숫자 상수 없음 (params.yaml만)
- 수기 검산: 근린공원8 = 41,315 × 23만 = 95.0억 … master_biz.csv와 대조
