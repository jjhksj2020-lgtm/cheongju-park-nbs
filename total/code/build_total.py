"""사업성 + 열저감 + 이용성 + 우선순위 통합 지도 → total/청주_장기미집행_공원_40개소_조성_지도.html (한 파일, 더블클릭으로 열림)

각 파트의 계산(사업성 biz/, 열저감 energy/, 이용성 need/edc/)을 먼저 돌리고(읽기만, 파트 폴더는 고치지 않음) 결과를 한 지도에 합친다.
  python total/code/build_total.py            # 세 파트 계산 → 지도 데이터 → 통합 지도
  python total/code/build_total.py --no-run   # 이미 있는 biz/out, energy/out, need/out 결과만 써서 지도만 다시
사업성 지도 틀(biz/code/map_template.html)을 고쳤으면 먼저 python total/code/make_template.py"""
import base64, json, os, subprocess, sys
C = os.path.dirname(os.path.abspath(__file__)); T = os.path.dirname(C); ROOT = os.path.dirname(T)
if '--no-run' not in sys.argv:
    for s in ['biz/code/biz_engine.py', 'biz/code/build_mapdata.py', 'energy/code/energy_engine.py', 'energy/code/build_mapdata.py', 'need/edc/code/build_edc.py', 'need/edc/code/build_priority.py', 'need/edc/code/build_hotspot.py']:
        r = subprocess.run([sys.executable, f'{ROOT}/{s}'], capture_output=True, text=True)
        if r.returncode: sys.exit(f'{s} 실패:\n{r.stderr}')
        print('실행', s)
B = json.load(open(f'{ROOT}/biz/out/mapdata.json', encoding='utf-8'))
EN = json.load(open(f'{ROOT}/energy/out/mapdata.json', encoding='utf-8'))
# 열저감 공원 값(경계·좌표 제외)을 사업성 공원에 E 로 붙인다 — 키는 site_id
skip = {'poly', 'c', 'name', 'type', 'location', 'area_m2', 'expiry', 'id'}
ev = {p['id']: {k: v for k, v in p.items() if k not in skip} for p in EN['parks']}
for p in B['parks']:
    p['E'] = ev.get(p['id'], {'status': '미산정'})
B['E'] = {k: EN[k] for k in ('asof', 'change', 'city', 'coef', 'target', 'factors', 'base', 'periods', 'spill_sites', 'n_scen', 'cell_m2', 'ring_m')}
# 이용성(③ 인구·토지·생활권 E·D·C) 공원 값을 U 로 붙인다 — need/out/edc_map.json(값) + indicators_edc.csv(지표별 자료·tag)
import csv
UM = json.load(open(f'{ROOT}/need/out/edc_map.json', encoding='utf-8'))
utag = {}
for r in csv.DictReader(open(f'{ROOT}/need/out/indicators_edc.csv', encoding='utf-8-sig')):
    utag.setdefault(r['site_id'], {})[r['indicator']] = [r['tag'], r['source_key']]
uv = {}
for s in UM['sites']:
    sid = s['site_id']
    if s.get('E1_pop') is None:
        uv[sid] = {'status': '미산정', 'note': s.get('note', '')}; continue
    uv[sid] = {'status': '산정', 'tag': utag.get(sid, {}), **{k: v for k, v in s.items() if k not in ('site_id', 'name', 'type', 'note')}}
for p in B['parks']:
    p['U'] = uv.get(str(p['id']), {'status': '미산정'})
B['U'] = {k: UM[k] for k in ('asof', 'pop_source', 'landcover', 'existing_parks', 'zones', 'params', 'buffer_m')}
# 우선순위(조성형·보전형, 열 핫스팟, 열 노출 변화) 공원 값을 R 로 붙인다 — need/out/priority_map.json + hotspot_map.json + need/edc/code/references.yaml
import yaml
PM = json.load(open(f'{ROOT}/need/out/priority_map.json', encoding='utf-8'))
HP = f'{ROOT}/need/out/hotspot_map.json'
HM = json.load(open(HP, encoding='utf-8')) if os.path.exists(HP) else {'meta': {'gee': False}, 'zones': [], 'sites': {}, 'sens': []}
RF = f'{ROOT}/need/edc/code/references.yaml'
rv = {}
for s in PM['sites']:
    sid = s['site_id']
    rv[sid] = {**{k: v for k, v in s.items() if k not in ('site_id', 'name', 'type')}, 'hot': HM['sites'].get(sid, {}),
               'reach': PM['geo'].get(sid, {}).get('reach')}   # 냉각 효과 범위(공원 경계 + range_m), 공원 상세 화면용
for p in B['parks']:
    p['R'] = rv.get(str(p['id']), {'status': '미산정'})
PP = yaml.safe_load(open(f'{ROOT}/need/edc/code/params.yaml', encoding='utf-8'))['priority']
B['R'] = {'asof': PM['asof'], 'coef': {**PM['coef'], 'build': PP['build']},   # 계수 표는 params 최신값(사례 수 n 포함) 'hot': HM['meta'], 'sens': HM.get('sens', []),
          'zones': [{k: v for k, v in z.items() if k != 'geo'} for z in HM['zones']],
          'refs': yaml.safe_load(open(RF, encoding='utf-8')) if os.path.exists(RF) else {},
          'evidence': yaml.safe_load(open(f'{ROOT}/need/edc/code/params.yaml', encoding='utf-8'))['priority'].get('evidence'),
          'energy': yaml.safe_load(open(f'{ROOT}/need/edc/code/params.yaml', encoding='utf-8'))['priority'].get('energy')}   # 기온→가정 냉방 전력 계수(min/base/max), 없으면 산정 예정
KS = f'{ROOT}/need/out/kma_summary.json'   # 청주 ASOS 실측 24°C 초과일수(kma_hotdays.py)가 있으면 가정값 대신 쓴다
if B['R']['energy'] and os.path.exists(KS):
    ks = json.load(open(KS, encoding='utf-8'))
    B['R']['energy'] = {**B['R']['energy'], 'hot_days': ks['hot_days'], 'hot_days_src': f"청주 ASOS {min(ks['years'])}~{max(ks['years'])} 실측", 'hot_years': ks['years']}
KL = f'{ROOT}/need/out/kma_lst_air.json'   # 청주 관측소 7곳 실측 지표온도→기온 비율(kma_lst_air.py): [장면 하위 사분위, 전체 기울기, 상위 사분위]
if B['R']['energy'] and os.path.exists(KL):
    kl = json.load(open(KL, encoding='utf-8'))
    q = kl['ratio_scene_q']
    B['R']['energy'] = {**B['R']['energy'], 'lst_to_air': [q[0], kl['ratio_pooled'], q[2]], 'lst_to_air_src': f"청주 관측소 실측(위성 {kl['scenes']}장면, {kl['pairs']}쌍)"}
KB = f'{ROOT}/need/out/bld_energy_coef.json'   # 청주 아파트 단지 실측 세대당 냉방 전력(bld_energy.py): [단지 하위 사분위, 전체 기울기, 상위 사분위]
if B['R']['energy'] and os.path.exists(KB):
    kb = json.load(open(KB, encoding='utf-8')); q = kb['lot_q_per_100cdd']
    B['R']['energy'] = {**B['R']['energy'], 'kwh_per_100cdd_month': [round(q[0], 1), round(kb['kwh_per_100cdd'], 1), round(q[2], 1)],
                        'kwh_src': f"청주 아파트 {kb['lots']}개 단지 실측(200세대 이상, 공용 전기 포함)"}   # 조성 전·후 지표온도 변화 표
B['asof'] = f"사업성 {B['asof']} · 열저감 {EN['asof']} · 이용성 {UM['asof']} · 우선순위 {PM['asof']}"
assets = {}
for sub in ('img', 'dem'):
    d = f'{ROOT}/biz/data/map/{sub}'
    for fn in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if fn.endswith('.json'): continue
        mime = 'image/jpeg' if fn.endswith('.jpg') else 'image/png'
        assets[f'{sub}/{fn}'] = f'data:{mime};base64,' + base64.b64encode(open(f'{d}/{fn}', 'rb').read()).decode()
# 발표판: 지도 앱 앞에 주제·목적 → 공원이란 → 이용성 → 에너지저감 → 사업성 페이지를 붙인다 (code/present.py)
sys.path.insert(0, C)
import present
out = present.OUT
open(out, 'w', encoding='utf-8').write(present.wrap(present.page_of(assets, B)))
# V-World 실시간 배경용 키 파일. 키는 .env에만 있고, 이 파일은 git에 올리지 않는다(.gitignore). HTML 옆에 두면 발표판이 V-World 타일을 쓴다
envf = f'{ROOT}/.env'
vk = [l.split('=', 1)[1].strip() for l in open(envf, encoding='utf-8') if l.startswith('VWORLD_KEY=')] if os.path.exists(envf) else []
if vk:
    open(f'{T}/vworld_key.js', 'w', encoding='utf-8').write(f'window.VWORLD_KEY = {json.dumps(vk[0])};\n')
    print('V-World 키 파일 total/vworld_key.js (git 제외)')
n = sum(1 for p in B['parks'] if p['E'].get('status') == '산정')
nu = sum(1 for p in B['parks'] if p['U'].get('status') == '산정')
nr = sum(1 for p in B['parks'] if p['R'].get('status') == '산정')
print(f'total/청주_장기미집행_공원_40개소_조성_지도.html {os.path.getsize(out)//1024} KB · 공원 40 (열저감 산정 {n}, 이용성 산정 {nu}, 우선순위 산정 {nr}) · 사진·지형 {len(assets)}')
