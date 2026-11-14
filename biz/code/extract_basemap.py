"""브라우저에서 받은 cheongju_basemap_vworld.json(V-World WMTS 타일 모자이크) → biz/data/map/img/*.jpg|png + manifest.json
사용: python biz/code/extract_basemap.py <json 경로>"""
import base64, json, os, sys
R = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'map')
src = json.load(open(sys.argv[1], encoding='utf-8'))
os.makedirs(f'{R}/img', exist_ok=True); man = {}
for k, v in src.items():
    if not isinstance(v, dict) or 'data' not in v: continue
    head, b64 = v['data'].split(',', 1); ext = 'jpg' if 'jpeg' in head else 'png'
    fn = f'{k}.{ext}'; open(f'{R}/img/{fn}', 'wb').write(base64.b64decode(b64))
    man[k] = {'file': fn, 'bounds': v['bounds'], 'z': v['z'], 'w': v['w'], 'h': v['h']}
json.dump(man, open(f'{R}/img/manifest.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(man), 'images')
