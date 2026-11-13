# 청주 장기미집행 공원 40개소 — 사업성 룰 엔진

실행: `pip install pyyaml` 후 `python biz_engine.py` (Python 3.9+). 다른 프로그램 설치 불필요.

## 지금 상태에서 되는 것
공고 40개소(data/sites.csv) + V-World 토지소유·2026 공시지가(data/land_own.csv, land_price.csv, 39개소 실자료) + 청주 실적 단가로
보상·조성 범위, 특례, 시 부담 최대·최소, 단계, 8개 시나리오, 카드 40장이 나온다. 필요성 지표(need.csv)는 아직 미수령이라 국비 요건은 "검토"로 표시된다.

## 입력 파일
1. data/need.csv  ← 필요성 파트 산출 (등급·판정·H1·C1 플래그). 템플릿: need.TEMPLATE.csv
2. data/land_own.csv, data/land_price.csv ← 수집 완료(2026-11-13). 다시 받는 법은 실행방법.md 1번.

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

## 토지소유·공시지가 수집

저장소 맨 위 `실행방법.md` 1번 (브라우저 수집기 `tools/vworld_collect.js`). 2026-11-13 수집분이 `data/land_own.csv`, `data/land_price.csv` 에 들어 있다.
