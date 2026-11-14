# 에너지(열저감) 파트 — 실행 방법

**최종본: [`에너지_지도.html`](에너지_지도.html)** — 내려받아 더블클릭하면 열립니다(인터넷 없이 됨).
GitHub 웹에서는 코드만 보이니 **Download raw file** 로 받아서 여세요.

**독립 참고 결과**입니다. 판정(필요성)·단계(사업성)에는 넣지 않고, 공원별 열저감·전력 절감 효과를 따로 보여 줍니다.
질문: *공원을 조성하면 지금 상태와 비교해 공원과 주변이 얼마나 시원해지고, 주변 주민의 전력을 얼마나 줄이나?*
개발 압력·비용은 다루지 않습니다(필요성·사업성 몫).

---

## 계산 사슬 (공원마다)

| 단계 | 계산 | 자료 |
|---|---|---|
| ① 녹지 증가 | 조성 목표 NDVI − 지금 NDVI (0 미만이면 0) | Sentinel-2 여름 10m, 목표 = 청주 잔디~수목 중앙값 |
| ② 공원 안 지표온도 | 청주 녹지-온도 계수 × ① | Landsat 8·9 여름 회귀 (GEE) |
| ③ 주변 기온 | ② × 퍼짐 비율 × 지표→기온 비율 | 특례사업지 전후 실측(E1) · 문헌(E2) |
| ④ 최대전력 kW | 주변 인구 × ③ × W/°C·인 | GHSL 2020 인구 · Santamouris 2015(E4) |
| ⑤ 연간 냉방전력 MWh | 주변 인구 × 1인당 냉방전력 × %/°C × ③ | 한전 191.5kWh(E5) · E4 |

- 6개 계수(목표 NDVI·온도 계수·퍼짐·기온 비율·W/°C·%/°C)의 상·하한 **64개 조합**으로 범위를 내고, 표의 "기준"은 각 계수 중간값입니다.
- 등급: 시나리오마다 연간 절감 순위로 상(상위 25%)·중(50%까지)·하 → 64개가 모두 같으면 **확정**, 아니면 **경계**.
- 성격: 지금 NDVI가 잔디 수준 이상이면 **보전형**(이미 녹지), 미만이면 **조성형**(녹지를 새로 만듦).
- 미산정: 어린이공원152(경계 없음), 생태공원3(하천·제방 위주, 사업성 파트와 같은 제외).

## 폴더

```
energy/
  에너지_지도.html          최종본 (build_page.py가 만듦)
  README.md                 이 파일
  code/
    params.yaml             모든 기준값과 출처 ← 계수는 여기서만 바꾼다
    gee_energy.template.js  GEE 스크립트 틀
    make_gee_script.py      틀 + params + 공원 경계 → gee_energy.js
    gee_energy.js           GEE Code Editor에 붙여넣는 완성본
    energy_engine.py        계산 엔진 (64개 시나리오, 등급)
    page_template.html · build_page.py   지도 화면 틀 · 최종본 만들기
  data/gee/
    gee_output.txt          GEE 콘솔 출력 원본 (2026-11-14 실행)
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

1. `python energy/code/make_gee_script.py` → `code/gee_energy.js` 생성
2. [GEE Code Editor](https://code.earthengine.google.com/) 에서 프로젝트 **cheongju-grpi** (비상업·학술 등록, Community 등급) 선택
3. `gee_energy.js` 내용을 붙여넣고 **Run** → 1~2분 뒤 콘솔에 `CITY|` 1줄, `PARK|` 39줄, `DONE|39`
4. 그 줄들을 `data/gee/gee_output.txt` 에 덮어쓰고 위 "실행"을 다시 합니다.

- 비상업 무료 사용은 학교 과제일 때만입니다. 용역 납품물에 쓰면 상업 라이선스가 필요합니다.
- 1회 실행은 월 무료 사용량(150 EECU-시간)의 아주 작은 부분입니다. 지도 레이어 없이 숫자만 출력합니다.

## 결과

| 파일 | 내용 |
|---|---|
| `out/summary.md` | 청주 계수, 합계, 보전형·조성형 비교, 상위 10, 미산정, 검증 |
| `out/master_energy.csv` | 40행: 땅 상태 비율, 성격, 지금 NDVI, 주변 인구, 단계별 기준·하한·상한, 등급·확정 |
| `에너지_지도.html` | 지도(원 크기 = 연간 절감) · 공원별 계산 과정 · 순위 · 전체 표 · 방법 |

## 한계

- 지표온도 계수를 문헌 비율(0.08~0.6)로 기온으로 바꿨습니다. 기온 실측이 없어 범위가 넓습니다.
- 1ha 미만 소공원은 위성 열자료(100m급)로 직접 잴 수 없어 청주 전체 계수를 적용한 추정입니다.
- 전력은 주변 거주 인구 기준이라 상가·업무 건물 몫이 빠져 있고, %/°C는 총전력 기준이라 보수적입니다.
