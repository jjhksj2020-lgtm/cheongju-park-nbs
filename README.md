# 청주 장기미집행 공원 40개소 판정 모형

상명대 CCS자연기반해법(NbS)계획및설계 · 선진엔지니어링 트랙 「2040 청주시 공원녹지기본계획」

청주시 공고 제2026-2004호의 장기미집행 공원 40개소를 **존치·조성 / 존치 / 보류**로 가르고 **1·2단계** 집행 순서를 정하는 근거를, 청주시 평가 기준 5개(공원조성 가치·재정투입 효율성·개발압력·기존투자·이용성)로 만든다.

| 파트 | 맡는 시 기준 | 하는 일 | 폴더 |
|---|---|---|---|
| 필요성 | ① 공원조성 가치 · ② 이용성 · ③ 개발압력 | 순위·등급 → **판정** | `need/` |
| 사업성 | ④ 재정투입 효율성 · ⑤ 기존투자 | 시 부담 금액 → **단계·재원** | `biz/` |

필요성이 먼저고 사업성은 그 안에서 순서를 정한다. "해제"는 모형이 내지 않는다.

## 폴더

```
docs/        제출물 1·2 (PDF·Word), 공통 정의서, 웹 페이지판
biz/         사업성 룰 엔진 (python biz_engine.py) — params.yaml에 모든 상수와 출처
need/        필요성 파트 작업 폴더 (지표 계산 · 점수 · need.csv 산출)
dashboard/   땅 주인 지도 park-land-map.html (위성사진·지형·필지 소유)
data/geo/    공원 경계·필지 (V-World 수집분)
tools/       vworld_collect.js — V-World 브라우저 수집기
evidence/    근거 대장 (제도·단가·피해·청주 현안, 출처 URL·조사일)
data/raw/    원자료 응답 원본 (API JSON, 다운로드 파일) — 커밋 전 용량 확인
```

## 실행

**처음이면 [실행방법.md](실행방법.md) 를 보세요** (V-World 수집 → 계산 → 지도 순서, 인증키 포함).

```bash
pip install pyyaml
python biz/biz_engine.py          # → biz/out/ (master_biz.csv, scenarios.csv, cards/, summary.md)
```

실데이터는 템플릿(`biz/data/*.TEMPLATE.csv`)대로 채운 뒤 같은 폴더에 `need.csv`, `land_own.csv`, `land_price.csv`로 넣으면 열은 그대로, 값만 바뀐다.

## 두 파트가 주고받는 파일

- `need/out/need.csv` → `biz/data/need.csv` : `site_id, grade(상/중/하), verdict, H1_high, industrial_downwind, C1_near, river_adjacent, refund_eligible`
- `biz/out/master_biz.csv` → 대시보드·시설 카드 사업성 블록
- 마스터 키는 `site_id`(1~40, `biz/data/sites.csv` 순서 = 공고 표 순서)

## 공통 규칙

1. 모든 수치에 출처키(evidence/ 또는 docs 참고문헌 번호). 출처 없는 값은 "미산정", 추정값은 "가정"으로 표기.
2. 코드에 숫자 상수를 쓰지 않는다 — `params.yaml`, `presets.yaml`에서만 읽는다.
3. 확률 추출(몬테카를로)은 쓰지 않는다. 값을 정해 놓고 바꿔 보는 시나리오 분석(프리셋 4개 / 단가 상·하한 8조합)으로 "모두 같으면 확정, 하나라도 다르면 경계".
4. 같은 원자료를 두 파트에 중복 투입하지 않는다(공시지가 변동률 → 필요성, 수준 → 사업성).
5. 커밋마다 검증 결과(엔드포인트·패키지·수치·실적 재현) 한 줄을 커밋 메시지나 `CHANGELOG.md`에 남긴다.

## 일정 (11~15주)

11주 자료 수집·요청 → 12주 점수·공시지가 → 13주 등급·단계·시나리오 → 14주 화면 실데이터·검증 → 15주 발표. 세부는 `docs/청주_장기미집행공원_중간보고서.pdf` 2-5.
