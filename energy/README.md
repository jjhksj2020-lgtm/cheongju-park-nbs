# 에너지(열저감) 파트 — 실행 방법

**최종본: [`에너지_지도.html`](에너지_지도.html)** — 내려받아 더블클릭하면 열립니다(인터넷 없이 됨).
GitHub 웹에서는 코드만 보이니 **Download raw file** 로 받아서 여세요.

**독립 참고 결과**입니다. 판정(필요성)·단계(사업성)에는 넣지 않고, 공원별 열저감 효과를 따로 보여 줍니다.
질문: *공원을 조성하면 지금 상태와 비교해 공원 일대와 주변의 여름 지표온도가 얼마나 내려가나?*
**계수는 모두 청주 위성 실측**(문헌 계수 0개)이고, 전력(kWh)으로는 바꾸지 않습니다(근거 부족 — `evidence/evidence_E_energy.md` E5).
개발 압력·비용은 다루지 않습니다(필요성·사업성 몫).

---

## 계산 사슬 (공원마다)

| 단계 | 계산 | 근거 (청주 실측) |
|---|---|---|
| ① 녹지 증가 | 조성 목표 NDVI − 지금 NDVI (0 미만이면 0) | Sentinel-2 여름: 지금 = 공원 경계 안, 목표 = 시가지 잔디 0.54 ~ 수목 0.86 (E4) |
| ② 공원 일대 지표온도 저감 | 계수 × ① × min(1, 면적 ÷ 1ha) | 계수 = 2013–16 → 2023–25 녹지가 실제로 변한 픽셀의 기울기 −2.14(늘어난 곳) ~ −7.01°C(줄어든 곳) / NDVI 1 (E2). 1ha = 위성 열밴드 최소 칸 (E3) |
| ③ 주변 300m 지표온도 저감 | ② × 퍼짐 비율, **1ha 이상 공원만** | 특례사업지 잠두봉·매봉 개발 전후 0.24 ~ 0.42 (E1) |
| ④ 냉각량 (°C·ha) | ② × 공원 일대 면적 + ③ × 고리 면적 | 순위·등급 기준 |

- 3개 계수(목표 NDVI·온도 계수·퍼짐)의 상·하한 **8개 시나리오**로 범위를 내고, "기준"은 각 계수 중간값입니다.
- 등급: 시나리오마다 냉각량 순위로 상(상위 25%)·중(50%까지)·하 → 8개가 모두 같으면 **확정**, 아니면 **경계**.
- 성격: 지금 NDVI가 잔디 수준 이상이면 **보전형**(이미 녹지), 미만이면 **조성형**(녹지를 새로 만듦).
- 미산정: 어린이공원152(경계 없음), 생태공원3(하천·제방 위주, 사업성 파트와 같은 제외).

## 폴더

```
energy/
  에너지_지도.html          최종본 (build_page.py가 만듦)
  README.md                 이 파일
  code/
    params.yaml             모든 기준값과 출처 ← 계수는 여기서만 바꾼다
    gee_energy.template.js  1차 GEE 틀 (공원별 지금 NDVI·인구, 조성 목표 NDVI)
    gee_change.template.js  2차 GEE 틀 (녹지 변화 → 온도 변화 계수, 고리 면적)
    make_gee_script.py      틀 + params + 공원 경계 → gee_energy.js · gee_change.js
    gee_energy.js · gee_change.js   GEE Code Editor에 붙여넣는 완성본
    energy_engine.py        계산 엔진 (8개 시나리오, 등급)
    page_template.html · build_page.py   지도 화면 틀 · 최종본 만들기
  data/gee/
    gee_output.txt          1차 GEE 출력 원본 (2026-11-14)
    gee_change_output.txt   2차 GEE 출력 원본 (2026-11-15)
    tukrye_before_after.json  특례사업지 개발 전후 실측 (퍼짐 비율 근거)
  out/                      계산 결과 — 실행하면 생김, 저장소에 안 올림
```

| 읽는 자료 (다른 파트, 읽기만) | 용도 |
|---|---|
| `biz/data/input/sites.csv` | 공원 40곳 (site_id) |
| `biz/data/vworld/parks.txt` · `gu.txt` | 공원·구 경계 |
| `biz/data/vworld/parcels.txt` · `parcel_attr.txt` | 필지별 지금 이용상황 (숲·농지·시가지 비율) |
| `biz/data/vworld/land_own.csv` | 경계 매칭 상태 (근사·불일치 표시) |

## 실행 (저장소 맨 위 폴더에서)

```bash
pip install pyyaml                     # 처음 한 번
python energy/code/energy_engine.py    # 계산 → energy/out/ (master_energy.csv, summary.md, energydata.json)
python energy/code/build_page.py       # 최종 지도 → energy/에너지_지도.html
```

계수만 바꿀 때는 `code/params.yaml` 을 고치고 위 두 줄을 다시 실행합니다. GEE는 다시 돌릴 필요 없습니다.

## GEE 다시 돌리기 (공원 경계·기간·위성 설정을 바꿀 때만)

1. `python energy/code/make_gee_script.py` → `code/gee_energy.js`, `code/gee_change.js` 생성
2. [GEE Code Editor](https://code.earthengine.google.com/) 에서 프로젝트 **cheongju-grpi** (비상업·학술 등록, Community 등급) 선택
3. `gee_energy.js` 붙여넣고 **Run** → `CITY|` 1줄, `PARK|` 39줄, `DONE|39` → `data/gee/gee_output.txt` 에 덮어쓰기
4. `gee_change.js` 붙여넣고 **Run** → `CHANGE|` 1줄, `RING|` 39줄, `DONE|39` → `data/gee/gee_change_output.txt` 에 덮어쓰기
5. 위 "실행"을 다시 합니다.

- 비상업 무료 사용은 학교 과제일 때만입니다. 용역 납품물에 쓰면 상업 라이선스가 필요합니다.
- 각 실행은 1~2분, 월 무료 사용량의 아주 작은 부분입니다. 지도 레이어 없이 숫자만 출력합니다.

## 결과

| 파일 | 내용 |
|---|---|
| `out/summary.md` | 청주 계수, 합계, 보전형·조성형 비교, 상위 10, 미산정, 검증 |
| `out/master_energy.csv` | 40행: 땅 상태 비율, 성격, 지금 NDVI, 단계별 기준·하한·상한, 냉각량, 주변 인구(참고), 등급·확정 |
| `에너지_지도.html` | 4단계 계산 흐름 · 지도(원 크기 = 냉각량) · 공원별 계산 과정 · 순위 · 전체 표 · 근거 |

## 한계

- 지표온도(땅 표면)이며 기온이 아닙니다. 공원 안 그늘 같은 체감 효과는 따로 보지 않습니다.
- 1ha 미만 공원은 위성 칸 안에서 섞인 만큼만 반영합니다. 그래서 소공원의 냉각량은 작게 나옵니다(위성으로 보이는 만큼).
- 주변 퍼짐 비율은 숲→개발(가열)에서 잰 값을 조성(냉각)에 쓴 것이라, 비슷한 규모(1ha 이상)에만 적용했습니다.
- 2026-11-14 1차 버전의 전력(kWh·kW) 추정은 문헌 계수를 쌓아 근거가 약해 폐기했습니다(E5).
