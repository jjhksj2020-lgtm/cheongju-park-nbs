"""지도 페이지 만들기
  python dashboard/build_page.py            → dashboard/park-land-map.html (img/·dem/ 폴더와 함께 써야 함, 웹 게시용)
                                              + dashboard/park-land-map_standalone.html (사진·지형까지 한 파일, 더블클릭으로 열림)
먼저 python dashboard/build_mapdata.py 로 mapdata.json을 만든다."""
import base64, json, os
R = os.path.dirname(os.path.abspath(__file__))
t = open(f'{R}/park-land-map.template.html', encoding='utf-8').read()
data = open(f'{R}/mapdata.json', encoding='utf-8').read()
open(f'{R}/park-land-map.html', 'w', encoding='utf-8').write(t.replace('__DATA__', data))
assets = {}
for sub, mime in (('img', None), ('dem', 'image/png')):
    d = f'{R}/{sub}'
    if not os.path.isdir(d): continue
    for fn in sorted(os.listdir(d)):
        if fn.endswith('.json'): continue
        m = mime or ('image/jpeg' if fn.endswith('.jpg') else 'image/png')
        assets[f'{sub}/{fn}'] = f'data:{m};base64,' + base64.b64encode(open(f'{d}/{fn}', 'rb').read()).decode()
sa = t.replace('__DATA__', data).replace('const D = ', 'const __ASSETS__ = ' + json.dumps(assets) + ';\nconst D = ', 1)
out = f'{R}/park-land-map_standalone.html'
open(out, 'w', encoding='utf-8').write('<!doctype html>\n<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n' + sa + '\n</html>\n')
print('park-land-map.html', os.path.getsize(f'{R}/park-land-map.html')//1024, 'KB / standalone', os.path.getsize(out)//1024, 'KB,', len(assets), 'assets')
