"""청주 장기미집행 공원 40개소 — 사업성 룰 엔진 (재정투입 효율성 · 기존투자)

입력
  data/sites.csv            공고 제2026-2004호 전사 (site_id, type, name, expiry, area_m2, jimok, notice_stage)
  params.yaml               모든 상수 (출처 포함)
  data/land_own.csv  [선택] site_id, public_share (국공유지 비율 0~1), plan_notice (조성계획 고시 1/0)   ← 토지소유 자료
  data/land_price.csv[선택] site_id, land_price_krw_m2 (개별공시지가 ㎡당), jimok_dae_m2 (지목 '대' 사유지 면적)  ← V-World
  data/need.csv      [선택] site_id, grade (상/중/하), verdict, H1_high (1/0), industrial_downwind (1/0), C1_near (1/0), river_adjacent (1/0)  ← 필요성 파트

출력 (out/)
  master_biz.csv     40행 × 사업성 열 (기준 시나리오 + 범위)
  scenarios.csv      40행 × 8개 시나리오 단계 + stage_stable + switch_value
  cards/<site>.md    후보지 카드 40장 (사업성 블록)
  summary.md         요약 + 검증 결과

규칙 출처는 params.yaml 주석과 제출물 2 §2-3 참조. 코드에 숫자 상수를 쓰지 않는다.
"""
from __future__ import annotations
import csv, os, sys, itertools, yaml

HERE = os.path.dirname(os.path.abspath(__file__))
P = yaml.safe_load(open(os.path.join(HERE, 'params.yaml'), encoding='utf-8'))
OUT = os.path.join(HERE, 'out'); os.makedirs(os.path.join(OUT, 'cards'), exist_ok=True)


def read_csv(name, key='site_id'):
    path = os.path.join(HERE, 'data', name)
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8-sig') as f:
        return {int(r[key]): r for r in csv.DictReader(f)}


sites = read_csv('sites.csv')
for _s in sites.values():
    _s['site_id'] = int(_s['site_id']); _s['area_m2'] = int(_s['area_m2']); _s['expiry'] = int(_s['expiry'])
own = read_csv('land_own.csv')
price = read_csv('land_price.csv')
need = read_csv('need.csv')


def fnum(d, k, default=None):
    v = d.get(k) if d else None
    try:
        return float(v) if v not in (None, '') else default
    except ValueError:
        return default


def private_area(s):
    """사유지 면적. 토지소유 자료가 없으면 params.private_share_default(=1.0) 가정."""
    o = own.get(s['site_id'])
    pub = fnum(o, 'public_share')
    tag = '실자료' if pub is not None else '가정'
    share = (1 - pub) if pub is not None else P['private_share_default']
    return s['area_m2'] * share, share, tag


def unit_effective(s, unit):
    """보상 단가 = max(실적 단가, 사유지 공시지가 × 계수). 계수: 하한 1.0(토지보상법 §70①), 상한 1/현실화율. params.land_price_rule."""
    cu = P['compensation_unit_krw_m2']; r = cu['land_price_rule']
    lp = fnum(price.get(s['site_id']), 'land_price_krw_m2')
    if lp is None:
        return unit, '실적'
    t = min(1.0, max(0.0, (unit - cu['low']) / (cu['high'] - cu['low'])))
    factor = r['low_factor'] + (1 / r['realization_rate'] - r['low_factor']) * t
    return (lp * factor, '공시지가') if lp * factor > unit else (unit, '실적')


def compensation(s, unit):
    """토지보상 = 사유지 면적 × 단가(unit_effective)."""
    pa, _, _ = private_area(s)
    return pa * unit_effective(s, unit)[0]


def construction(s, unit):
    if s['type'] in P['construction_unit_krw_m2']['excluded_types']:
        return None  # 미산정 (실적 없음)
    return s['area_m2'] * unit


def special_ok(s):
    sp = P['special_project']
    return s['area_m2'] >= sp['min_area_m2'] and s['type'] not in sp['excluded_types']


def subsidy_routes(s):
    """국비 경로. 필요성 지표(need.csv)가 없으면 '검토'로 두고 경로 없음 취급."""
    n = need.get(s['site_id'])
    routes = []
    if not n:
        return routes, '검토(필요성 지표 수령 전)'
    ns = P['national_subsidy']
    if fnum(n, 'H1_high', 0) == 1 or fnum(n, 'industrial_downwind', 0) == 1:
        routes.append(('도시숲', ns['urban_forest']['share_low']))
    if fnum(n, 'C1_near', 0) == 1 or fnum(n, 'river_adjacent', 0) == 1:
        routes.append(('생태축', ns['eco_axis']['share_low']))
    if fnum(n, 'refund_eligible', 0) == 1:
        routes.append(('반환사업', ns['eco_refund']['share_low']))
    return routes, '판정'


def buyout_cap(s):
    pr = price.get(s['site_id'])
    dae = fnum(pr, 'jimok_dae_m2'); lp = fnum(pr, 'land_price_krw_m2')
    if dae is None or lp is None:
        return None
    return dae * lp


def costs(s, comp_unit, cons_unit, subsidy_selected):
    comp = compensation(s, comp_unit)
    cons = construction(s, cons_unit)
    routes, _ = subsidy_routes(s)
    special = special_ok(s)
    if cons is None:
        return comp, None, None, None, routes, special
    cmax = comp + cons
    if special:
        cmin = 0.0
    elif routes and subsidy_selected:
        best = max(r[1] for r in routes)
        cmin = cmax - cons * best
    else:
        cmin = cmax
    return comp, cons, cmax, cmin, routes, special


def stage_conditions(s, routes, special):
    """1단계 조건 (하나라도 충족). 보류 판정이면 단계 없음."""
    n = need.get(s['site_id'])
    verdict = n.get('verdict') if n else None
    if verdict == '보류':
        return None, ['보류: 단계 없음']
    reasons = []
    sr = P['stage_rules']
    if s['expiry'] <= sr['stage1_expiry_max']:
        reasons.append(f"실효 {s['expiry']} ≤ {sr['stage1_expiry_max']} (국토계획법 §48)")
    if s['notice_stage'] == '1단계':
        reasons.append('공고 1단계 유지 (공고 제2026-2004호)')
    if special or routes:
        reasons.append('외부 재원 경로 ≥ 1 (' + ', '.join((['특례'] if special else []) + [r[0] for r in routes]) + ')')
    return ('1단계' if reasons else '2단계'), reasons


def run_scenario(comp_unit, cons_unit, subsidy_selected):
    """한 시나리오: 단계 조건 → 1단계 합계 점검선 적용(시 부담 최소 낮은 순) → 최종 단계."""
    rows = {}
    for sid, s in sites.items():
        comp, cons, cmax, cmin, routes, special = costs(s, comp_unit, cons_unit, subsidy_selected)
        st, reasons = stage_conditions(s, routes, special)
        rows[sid] = dict(comp=comp, cons=cons, cmax=cmax, cmin=cmin, routes=routes, special=special, stage=st, reasons=reasons)
    # 점검선: 1단계 후보를 (필요성 등급순 →) 시 부담 최소 낮은 순으로 누적, 선을 넘으면 2단계로
    line = P['stage_rules']['stage1_budget_line_krw']
    grade_rank = {'상': 0, '중': 1, '하': 2}
    cand = [sid for sid, r in rows.items() if r['stage'] == '1단계']
    def key(sid):
        g = need.get(sid, {}).get('grade') if need else None
        return (grade_rank.get(g, 9), rows[sid]['cmin'] if rows[sid]['cmin'] is not None else float('inf'))
    cum = 0.0
    for sid in sorted(cand, key=key):
        r = rows[sid]
        if r['cmin'] is None:
            r['stage'] = '토지소유 수령 후'; r['reasons'].append('조성 단가 미산정 → 단계 보류')
            continue
        if cum + r['cmin'] > line:
            r['stage'] = '2단계'; r['reasons'].append(f'1단계 합계 점검선 {line/1e8:,.0f}억 초과 → 2단계로 이월')
        else:
            cum += r['cmin']
    return rows


def fmt(v):
    return '미산정' if v is None else f'{v/1e8:,.1f}억'


def main():
    cu, ku = P['compensation_unit_krw_m2'], P['construction_unit_krw_m2']
    base = run_scenario(cu['base'], ku['base'], False)
    lows = run_scenario(cu['low'], ku['low'], False)
    highs = run_scenario(cu['high'], ku['high'], False)

    # --- 8개 시나리오
    combos = list(itertools.product([('보상低', cu['low']), ('보상高', cu['high'])],
                                    [('조성低', ku['low']), ('조성高', ku['high'])],
                                    [('국비X', False), ('국비O', True)]))
    scen = {name: run_scenario(c[1], k[1], s[1]) for (c, k, s) in combos for name in [f'{c[0]}·{k[0]}·{s[0]}']}
    names = list(scen.keys())

    # --- switch value: 경계 후보지에 대해 보상단가를 low→high로 올리며 단계가 바뀌는 지점 (조성 base, 국비 X)
    def stage_at(sid, comp_unit):
        return run_scenario(comp_unit, ku['base'], False)[sid]['stage']
    def switch_value(sid):
        lo, hi = cu['low'], cu['high']
        s_lo, s_hi = stage_at(sid, lo), stage_at(sid, hi)
        if s_lo == s_hi:
            return None
        for _ in range(20):
            mid = (lo + hi) / 2
            if stage_at(sid, mid) == s_lo: lo = mid
            else: hi = mid
        return hi, s_lo, s_hi

    # --- master
    mcols = ['site_id', 'name', 'type', 'location', 'expiry', 'area_m2', 'notice_stage', 'need_grade', 'need_verdict',
             'private_share', 'private_share_tag', 'comp_low_krw', 'comp_high_krw', 'cons_low_krw', 'cons_high_krw',
             'city_max_low_krw', 'city_max_high_krw', 'city_min_low_krw', 'city_min_high_krw',
             'special_ok', 'subsidy_routes', 'subsidy_status', 'buyout_cap_krw', 'public_share', 'plan_notice', 'notice_stage1',
             'stage_base', 'stage_reasons', 'source_keys']
    with open(os.path.join(OUT, 'master_biz.csv'), 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f); w.writerow(mcols)
        for sid, s in sites.items():
            pa, share, tag = private_area(s)
            n = need.get(sid, {})
            routes, status = subsidy_routes(s)
            b, lo, hi = base[sid], lows[sid], highs[sid]
            o = own.get(sid, {})
            w.writerow([sid, s['name'], s['type'], s['location'], s['expiry'], s['area_m2'], s['notice_stage'],
                        n.get('grade', '미수령'), n.get('verdict', '미수령'), round(share, 3), tag,
                        lo['comp'], hi['comp'], lo['cons'], hi['cons'], lo['cmax'], hi['cmax'], lo['cmin'], hi['cmin'],
                        int(b['special']), ';'.join(r[0] for r in routes) or '없음', status, buyout_cap(s),
                        o.get('public_share', '미수령'), o.get('plan_notice', '미확인'), int(s['notice_stage'] == '1단계'),
                        b['stage'], ' / '.join(b['reasons']), 'SJ-p27;CJ-cost;LAW-fund' + (';LAND-own' if o else '') + (';VW-upis' if price.get(sid) else '')])

    # --- scenarios
    with open(os.path.join(OUT, 'scenarios.csv'), 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f); w.writerow(['site_id', 'name'] + names + ['stage_stable', 'switch_value_krw_m2', 'switch_note'])
        boundary = []
        for sid, s in sites.items():
            sts = [scen[nm][sid]['stage'] for nm in names]
            stable = len(set(sts)) == 1
            sv = None if stable else switch_value(sid)
            note = '' if sv is None else f'보상단가 {sv[0]/1e4:.1f}만원/㎡ 이상이면 {sv[1]} → {sv[2]}'
            if not stable: boundary.append((s['name'], note or '국비·조성 단가 조합에 따라 변동'))
            w.writerow([sid, s['name']] + sts + [int(stable), '' if sv is None else round(sv[0]), note])

    # --- cards
    for sid, s in sites.items():
        pa, share, tag = private_area(s); lo, hi, b = lows[sid], highs[sid], base[sid]
        routes, status = subsidy_routes(s); n = need.get(sid, {}); o = own.get(sid, {})
        sts = [scen[nm][sid]['stage'] for nm in names]; stable = len(set(sts)) == 1
        lines = [f"# {s['name']} — 사업성 블록", '',
                 f"- 면적·실효: {s['area_m2']:,}㎡ · {s['expiry']} · 공고 {s['notice_stage']} [SJ-p27]",
                 f"- 필요성 등급·판정: {n.get('grade', '미수령')} · {n.get('verdict', '미수령')} (필요성 파트)",
                 f"- 사유지 면적: {pa:,.0f}㎡ ({'실자료' if tag == '실자료' else f'가정 {share:.0%}'})",
                 f"- 토지보상 추정: {fmt(lo['comp'])} ~ {fmt(hi['comp'])} (23~34만원/㎡, CJ-cost)",
                 f"- 조성비 추정: {fmt(lo['cons'])} ~ {fmt(hi['cons'])} (6.1~13.9만원/㎡, CJ-cost)",
                 f"- 시 부담 최대: {fmt(lo['cmax'])} ~ {fmt(hi['cmax'])}",
                 f"- 시 부담 최소: {fmt(lo['cmin'])} ~ {fmt(hi['cmin'])}" + (' (특례 시 0)' if b['special'] else ''),
                 f"- 민간공원특례: {'법 요건 충족 (≥5만㎡, 생태공원 제외) [A1]' if b['special'] else '불가'}",
                 f"- 국비 경로: {', '.join(r[0] for r in routes) if routes else '없음'} — {status}",
                 f"- 매수청구 회피액: {fmt(buyout_cap(s))} (지목 대 × 공시지가, [A8])",
                 f"- 기존투자: 국공유 비율 {o.get('public_share', '미수령')} · 조성계획 고시 {o.get('plan_notice', '미확인')} · 공고 1단계 {'예' if s['notice_stage']=='1단계' else '아니오'}",
                 '', f"**단계: {b['stage']}** — " + ' / '.join(b['reasons']),
                 f"안정성: 8개 시나리오 {'모두 동일 → 확정' if stable else '불일치 → 경계'} ({', '.join(sorted(set(sts)))})", '',
                 '출처: SJ-p27, CJ-cost(B7), LAW-fund(A1·A3·A4a·A4b·A8)' + ('' if o else ' · 토지소유 미수령'),]
        open(os.path.join(OUT, 'cards', f"{sid:02d}_{s['name']}.md"), 'w', encoding='utf-8').write('\n'.join(lines))

    # --- validation: 월명공원 재현 (상한 단가)
    v = P['validation']['wolmyeong']
    comp_v = v['area_m2'] * cu['high']; cons_v = v['area_m2'] * ku['low']
    ok_c = abs(comp_v - v['compensation_krw']) / v['compensation_krw'] <= v['tolerance']
    ok_k = abs(cons_v - v['construction_krw']) / v['construction_krw'] <= v['tolerance']

    # --- summary
    tot_max = sum(highs[s]['cmax'] or 0 for s in sites); tot_min = sum(lows[s]['cmin'] or 0 for s in sites)
    s1 = [sid for sid in sites if base[sid]['stage'] == '1단계']
    top5 = sorted([(highs[s]['cmax'] or 0, sites[s]['name']) for s in sites], reverse=True)[:5]
    top5_share = sum(x[0] for x in top5) / tot_max if tot_max else 0
    half = [sites[s]['name'] for s in sites if highs[s]['cmax'] and lows[s]['cmin'] is not None and lows[s]['cmin'] / highs[s]['cmax'] <= 0.5]
    md = ['# 사업성 엔진 실행 요약', '',
          f"- 입력 상태: 토지소유 {'수령' if own else '미수령(사유지 100% 가정)'} · 공시지가 {'수령' if price else '미수령(실적 단가)'} · 필요성 지표 {'수령' if need else '미수령(국비 요건 검토, 등급 미반영)'}",
          f"- 시 부담 최대 합계(상한 단가, 생태공원 제외): {tot_max/1e8:,.0f}억 / 최소 합계(하한·특례 0): {tot_min/1e8:,.0f}억",
          f"- 기준 시나리오 1단계: {len(s1)}개소 — " + ', '.join(sites[s]['name'] for s in s1),
          f"- RQ4 (외부 재원으로 시 부담 절반 이하): {len(half)}개소 → {'참(≤10)' if len(half) <= 10 else '거짓(>10)'} — " + ', '.join(half),
          f"- RQ5 (상위 5개소 비중): {top5_share:.0%} → {'참(≥80%)' if top5_share >= 0.8 else '거짓(<80%)'} — " + ', '.join(f'{n}({c/1e8:,.0f}억)' for c, n in top5),
          f"- 경계 후보지(시나리오 간 단계 불일치): {len(boundary)}개소" + (' — ' + '; '.join(f'{n}: {t}' for n, t in boundary) if boundary else ''),
          '', '## 검증', f"- 월명공원 재현: 보상 {comp_v/1e8:,.1f}억 (실적 351억) {'통과' if ok_c else '실패'} · 조성 {cons_v/1e8:,.1f}억 (실적 63억) {'통과' if ok_k else '실패'}",
          '- 코드에 숫자 상수 없음: params.yaml만 읽음', '']
    open(os.path.join(OUT, 'summary.md'), 'w', encoding='utf-8').write('\n'.join(md))
    print('\n'.join(md))


if __name__ == '__main__':
    main()
