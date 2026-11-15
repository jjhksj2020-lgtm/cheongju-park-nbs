"""열저감 지도 최종본 만들기 → energy/에너지_지도.html (한 파일. 사업성 지도와 같은 위성사진·지형을 넣어 더블클릭으로 열림)
순서: python energy/code/energy_engine.py → python energy/code/build_mapdata.py → python energy/code/build_page.py
위성사진·지형은 biz/data/map/ (사업성 파트 수집분, 읽기만)."""
import base64, json, os
C = os.path.dirname(os.path.abspath(__file__)); E = os.path.dirname(C); ROOT = os.path.dirname(E)
t = open(f'{C}/page_template.html', encoding='utf-8').read()
data = open(f'{E}/out/mapdata.json', encoding='utf-8').read()
assets = {}
for sub in ('img', 'dem'):
    d = f'{ROOT}/biz/data/map/{sub}'
    if not os.path.isdir(d): continue
    for fn in sorted(os.listdir(d)):
        if fn.endswith('.json'): continue
        mime = 'image/jpeg' if fn.endswith('.jpg') else 'image/png'
        assets[f'{sub}/{fn}'] = f'data:{mime};base64,' + base64.b64encode(open(f'{d}/{fn}', 'rb').read()).decode()
page = t.replace('__DATA__', data).replace('const D = ', 'const __ASSETS__ = ' + json.dumps(assets) + ';\nconst D = ', 1)
out = f'{E}/에너지_지도.html'
open(out, 'w', encoding='utf-8').write('<!doctype html>\n<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n' + page + '\n</html>\n')
print('energy/에너지_지도.html', os.path.getsize(out) // 1024, 'KB,', len(assets), '사진·지형')
