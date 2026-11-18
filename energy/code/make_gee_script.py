"""GEE 스크립트 만들기: *.template.js + params.yaml(gee·change) + biz/data/vworld/parks.txt(공원 경계) → gee_energy.js · gee_change.js
만든 js 를 GEE Code Editor(프로젝트 cheongju-grpi)에 붙여넣고 Run → 콘솔 출력을 energy/data/gee/gee_output.txt · gee_change_output.txt 에 붙인다.
실행: python energy/code/make_gee_script.py"""
import json, os, yaml
C = os.path.dirname(os.path.abspath(__file__)); E = os.path.dirname(C); ROOT = os.path.dirname(E)
P = yaml.safe_load(open(f'{C}/params.yaml', encoding='utf-8'))
PARKS_TXT = f'{ROOT}/biz/data/vworld/parks.txt'   # 사업성 파트 수집분 (읽기만)


def decode(s):
    """biz/code/build_mapdata.py 와 같은 형식: 정수(경위도×1e5) 누적차분, 다각형 ';', 링 '|'."""
    scale = P['coord_scale']
    polys = []
    for p in s.split(';'):
        rings = []
        for r in p.split('|'):
            v = list(map(int, r.split(','))); x = y = 0; ring = []
            for i in range(0, len(v), 2):
                x += v[i]; y += v[i + 1]; ring.append([x / scale, y / scale])
            if ring[0] != ring[-1]:
                ring.append(ring[0])
            rings.append(ring)
        polys.append(rings)
    return polys


parks = []
for line in open(PARKS_TXT, encoding='utf-8').read().split('\n'):
    if line:
        sid, enc = line.split('~', 1)
        parks.append({'id': int(sid), 'g': decode(enc)})
for name in ('gee_energy', 'gee_change'):
    tpl = open(f'{C}/{name}.template.js', encoding='utf-8').read()
    js = (tpl.replace('__CFG__', json.dumps(P['gee'], ensure_ascii=False))
             .replace('__CHANGE__', json.dumps(P['change'], ensure_ascii=False))
             .replace('__PARKS__', json.dumps(parks, separators=(',', ':'))))
    open(f'{C}/{name}.js', 'w', encoding='utf-8').write(js)
    print(f'energy/code/{name}.js', len(parks), '공원', len(js) // 1024, 'KB')
