# 사업성 파트 — 실행 방법

**최종본: [`사업성_지도.html`](사업성_지도.html)** — 내려받아 더블클릭하면 열립니다(위성사진·3D 지형 포함, 인터넷 연결 필요).
GitHub 웹에서 누르면 코드만 보이니 **Download raw file** 로 받아서 여세요.

청주시 기준 ④ 재정투입 효율성 · ⑤ 기존투자를 맡아, 공원별 **시 부담 금액 → 1·2단계 · 재원(특례·국비)** 을 정합니다.

---

## 폴더

```
biz/
  사업성_지도.html        최종본 (build_page.py가 만듦)
  README.md               이 파일
  code/
    biz_engine.py         계산 엔진 (시 부담·특례·국비·단계·8개 시나리오)
    params.yaml           모든 기준값과 출처 ← 단가·비율은 여기서만 바꾼다
    rules.md              판정 규칙 5개
    build_mapdata.py      지도 데이터 만들기 (→ out/mapdata.json)
    build_page.py         최종 지도 HTML 만들기 (→ 사업성_지도.html)
    map_template.html     지도 화면 틀
    vworld_collect.js     V-World 브라우저 수집기 (콘솔에 붙여넣기용 완성본)
    vworld_collect.template.js · make_collector.py   수집기 원본·생성기
    extract_basemap.py · extract_dem.py               위성사진·지형 파일 풀기
  data/
    input/   sites.csv (공고 40곳) · need.TEMPLATE.csv (필요성 결과 양식) · need.csv (받으면 여기에)
    vworld/  land_own.csv (국공유 비율) · land_price.csv (2026 공시지가 등)
             parks.txt (공원 경계) · parcels.txt (필지 모양) · parcel_attr.txt (필지 소유·용도·이용상황) · gu.txt (구 경계)
    map/     img/ (위성사진·일반지도 41장) · dem/ (지형 40장)
  out/       계산 결과 — 실행하면 생김, 저장소에 안 올림
```

| 자료 | 출처 · 기준일 |
|---|---|
| `data/input/sites.csv` | 청주시 공고 제2026-2004호 |
| `data/vworld/*` | V-World 도시계획시설·연속지적도·토지소유정보·토지임야목록·토지특성정보, 2026-11-13 조회 |
| `data/map/img` | V-World WMTS 위성사진·일반지도 |
| `data/map/dem` | Terrarium 표고 타일 (AWS Open Data, 한국은 SRTM 30m급) |
| 단가·비율 | `code/params.yaml` 각 줄의 출처 |

---

## 0. 준비물

| 무엇 | 필요할 때 |
|---|---|
| Python 3.9+ 와 `pip install pyyaml` | 계산·지도 만들 때 |
| 크롬 또는 엣지 + **V-World 인증키** (팀 단톡방 공유) | V-World 자료를 새로 받을 때만 |

V-World는 해외·클라우드 서버 접속을 막으므로 수집은 **한국 PC의 브라우저**에서 합니다. 계산과 지도는 어디서나 됩니다.
인증키는 개발키(2026-11-13 발급, **2027-05-13 만료**, 도메인 `localhost`)입니다. 만료되면 vworld.kr → 오픈API → 인증키 관리에서 연장합니다.

---

## 1. V-World 토지 자료 새로 받기 (선택, 내 PC 브라우저, 10~15분)

> 매년 공시지가가 바뀔 때나 공원 목록이 바뀔 때만. 2026-11-13 수집분이 이미 `data/vworld/` 에 있습니다.

1. 크롬/엣지 주소창에 **`https://api.vworld.kr/req/search`** 를 엽니다 (오류 글자가 떠도 정상).
2. `F12` → **Console** 탭 (붙여넣기 경고가 나오면 `allow pasting` 입력 후 Enter).
3. 키를 넣습니다:
   ```js
   window.VWORLD_KEY = '팀 단톡방의 인증키'
   ```
4. `code/vworld_collect.js` 내용을 **전부** 복사해 붙여넣고 Enter → `준비됨` 이 뜹니다.
5. `await collectAll()` → 다운로드 폴더에 4개 파일이 생깁니다. `data/vworld/` 의 같은 이름 파일에 덮어씁니다:
   `land_own.csv`, `land_price.csv`, `parcels.txt`, `parcel_attr.txt`

- 기준연도를 바꾸려면 `code/vworld_collect.template.js` 의 `const YEAR = '2026'` 을 고친 뒤 `python biz/code/make_collector.py` 로 완성본을 다시 만듭니다.
- 위성사진·지형까지 다시 받으려면 같은 콘솔에서 `await collectBasemap()`, `await collectDem()` → 받은 파일을
  `python biz/code/extract_basemap.py <파일>`, `python biz/code/extract_dem.py <파일>` 로 풉니다.

## 2. 필요성 결과 넣기 (받았을 때)

필요성 파트의 `need/out/need.csv` 를 `data/input/need.csv` 로 복사합니다. 없으면 국비 요건이 "검토"로 표시되고 나머지는 그대로 계산됩니다.

## 3. 계산 → 지도 (저장소 맨 위 폴더에서)

```bash
pip install pyyaml                  # 처음 한 번
python biz/code/biz_engine.py       # 계산      → biz/out/ (summary.md, master_biz.csv, scenarios.csv, cards/)
python biz/code/build_mapdata.py    # 지도 데이터 → biz/out/mapdata.json
python biz/code/build_page.py       # 최종 지도   → biz/사업성_지도.html
```

- `out/summary.md` 의 **월명공원 재현이 "통과"** 인지 먼저 봅니다. "실패"면 `params.yaml` 단가를 잘못 바꾼 것입니다.
- 단가·비율을 바꿀 때는 `code/params.yaml` 만 고치고 위 세 줄을 다시 실행합니다(코드에는 숫자가 없습니다).

| 결과 | 내용 |
|---|---|
| `out/summary.md` | 시 부담 합계, 1단계 목록, RQ4·RQ5 판정, 월명공원 재현 검증 |
| `out/master_biz.csv` | 40행: 사유지 비율, 보상·조성 범위, 시 부담 최대·최소, 특례, 국비, 단계와 이유 |
| `out/scenarios.csv` | 8개 시나리오(보상·조성·국비 상하한)별 단계, 확정/경계, 전환값 |
| `out/cards/*.md` | 공원별 사업성 카드 40장 |
| `사업성_지도.html` | 최종 지도 (도시 전체 / 공원 상세 / 비교 막대, 2D·3D, 위성사진·지형) |

## 4. 올리기

```bash
git add -A
git commit -m "무엇을 왜 + 검증 결과 (예: 2027 공시지가 반영, 월명 재현 통과)"
git push
```
`CHANGELOG.md` 에 날짜·바꾼 것·결과 숫자를 한 단락 남깁니다.

---

## 자주 막히는 곳

| 증상 | 해결 |
|---|---|
| 지도가 빈 화면 | 인터넷 연결 확인(지도 라이브러리를 인터넷에서 불러옴). GitHub 웹 미리보기가 아니라 내려받은 파일을 크롬·엣지로 열기 |
| 콘솔에 `…/req/search 페이지의 콘솔에서 실행하세요` | 1-1 주소를 연 탭에서 실행 |
| `KEY에 V-World 인증키를 넣으세요` | 1-3 키 줄을 먼저 실행하고 수집기를 다시 붙여넣기 |
| `INCORRECT_KEY` / `INVALID_KEY` | 키 만료(2027-05-13) 또는 오타 |
| 클라우드·해외에서 403 | V-World가 막음 → 한국 PC 브라우저에서 |
| `ModuleNotFoundError: yaml` | `pip install pyyaml` |
| 어린이공원152 값이 "가정" | V-World 도시계획 지도에 경계가 없음(청주시 확인 필요) → 사유지 100%로 계산 |
