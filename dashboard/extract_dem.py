"""브라우저에서 받은 cheongju_dem_terrarium.json → dashboard/dem/*.png + manifest.json
Terrarium 인코딩(표고 = R*256 + G + B/256 − 32768 m). 범위는 배경 위성사진(img/manifest.json)과 같은 경계.
사용: python dashboard/extract_dem.py <json 경로>"""
import base64, json, os, sys
R = os.path.dirname(os.path.abspath(__file__))
src = json.load(open(sys.argv[1], encoding='utf-8'))
os.makedirs(f'{R}/dem', exist_ok=True); man = {}
for k, v in src.items():
    fn = f'{k}.png'; open(f'{R}/dem/{fn}', 'wb').write(base64.b64decode(v['data'].split(',', 1)[1]))
    man[k] = {'file': fn, 'bounds': v['bounds'], 'w': v['w'], 'h': v['h'], 'min': v['min'], 'max': v['max']}
json.dump(man, open(f'{R}/dem/manifest.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(man), 'dem tiles')
