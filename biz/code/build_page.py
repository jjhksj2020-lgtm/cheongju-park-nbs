"""사업성 지도 최종본 만들기 → biz/사업성_지도.html (한 파일. 위성사진·지형까지 들어 있어 더블클릭으로 열림)
순서: python biz/code/biz_engine.py → python biz/code/build_mapdata.py → python biz/code/build_page.py"""
import base64, json, os
C = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(C)   # biz/code, biz/
t = open(f'{C}/map_template.html', encoding='utf-8').read()
data = open(f'{B}/out/mapdata.json', encoding='utf-8').read()
assets = {}
for sub in ('img', 'dem'):
    d = f'{B}/data/map/{sub}'
    if not os.path.isdir(d): continue
    for fn in sorted(os.listdir(d)):
        if fn.endswith('.json'): continue
        mime = 'image/jpeg' if fn.endswith('.jpg') else 'image/png'
        assets[f'{sub}/{fn}'] = f'data:{mime};base64,' + base64.b64encode(open(f'{d}/{fn}', 'rb').read()).decode()
page = t.replace('__DATA__', data).replace('const D = ', 'const __ASSETS__ = ' + json.dumps(assets) + ';\nconst D = ', 1)
out = f'{B}/사업성_지도.html'
open(out, 'w', encoding='utf-8').write('<!doctype html>\n<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n' + page + '\n</html>\n')
print('biz/사업성_지도.html', os.path.getsize(out) // 1024, 'KB,', len(assets), '사진·지형')
