"""사업성 + 열저감 통합 지도 → total/통합_지도.html (한 파일, 더블클릭으로 열림)

각 파트의 계산을 먼저 돌리고(읽기만, 파트 폴더는 고치지 않음) 결과를 한 지도에 합친다.
  python total/code/build_total.py            # 두 파트 계산 → 지도 데이터 → 통합 지도
  python total/code/build_total.py --no-run   # 이미 있는 biz/out, energy/out 결과만 써서 지도만 다시
사업성 지도 틀(biz/code/map_template.html)을 고쳤으면 먼저 python total/code/make_template.py"""
import base64, json, os, subprocess, sys
C = os.path.dirname(os.path.abspath(__file__)); T = os.path.dirname(C); ROOT = os.path.dirname(T)
if '--no-run' not in sys.argv:
    for s in ['biz/code/biz_engine.py', 'biz/code/build_mapdata.py', 'energy/code/energy_engine.py', 'energy/code/build_mapdata.py']:
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
B['asof'] = f"사업성 {B['asof']} · 열저감 {EN['asof']}"
assets = {}
for sub in ('img', 'dem'):
    d = f'{ROOT}/biz/data/map/{sub}'
    for fn in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if fn.endswith('.json'): continue
        mime = 'image/jpeg' if fn.endswith('.jpg') else 'image/png'
        assets[f'{sub}/{fn}'] = f'data:{mime};base64,' + base64.b64encode(open(f'{d}/{fn}', 'rb').read()).decode()
t = open(f'{C}/total_template.html', encoding='utf-8').read()
page = t.replace('__DATA__', json.dumps(B, ensure_ascii=False, separators=(',', ':'))).replace('const D = ', 'const __ASSETS__ = ' + json.dumps(assets) + ';\nconst D = ', 1)
out = f'{T}/통합_지도.html'
open(out, 'w', encoding='utf-8').write('<!doctype html>\n<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n' + page + '\n</html>\n')
n = sum(1 for p in B['parks'] if p['E'].get('status') == '산정')
print(f'total/통합_지도.html {os.path.getsize(out)//1024} KB · 공원 40 (열저감 산정 {n}) · 사진·지형 {len(assets)}')
