# 프롬프트 7 — F 확장 열 연결 (12~13주차, 백엔드) v1

역할: 너는 테스트를 먼저 쓰는 Python 개발자다.
목표: engine.py(사업성)의 결과에 engine_dcf.build_exec_f_table을 붙여 판정표 CSV에 F 확장 열을 더한다.
입력: data/park_parcel.parquet(owner_count 열을 D12로 추가), data/master_d0.csv, params.yaml + params_dcf.yaml,
      engine.py의 land_cost·build_cost 결과(site_id → (value, status, src_keys))
할 일:
1. total_cost = land_cost + build_cost. build_cost가 '미산정'이면 total_cost도 '미산정'이다(0으로 더하지 마라).
2. build_exec_f_table을 부르고 site_id로 판정표에 조인한다.
3. 화면 카드에 f_review_grade와 f_margin_*를 '일정' 줄로 보인다. f_margin이 음수면 그 수단에 '시한 지남' 배지.
제약: 규칙1~5의 결과(단계·재원)는 바꾸지 마라. F 확장 열은 표시와 정렬 후보로만 쓴다(팀 합의 전).
테스트: 기존 골든 파일의 단계·재원 열이 바뀌지 않는다 / 모든 F 열에 __status·__src가 있다 / '해제' 0건.
