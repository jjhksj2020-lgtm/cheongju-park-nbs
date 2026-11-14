"""biz/code/vworld_collect.template.js + 저장소 자료 → biz/code/vworld_collect.js (브라우저에 붙여넣을 완성본)
공원 경계·공고 면적·위성사진 경계를 스크립트 안에 넣어, 저장소가 비공개여도 브라우저에서 바로 돈다.
공원 경계(biz/data/vworld/parks.txt)나 sites.csv가 바뀌면 다시 실행: python biz/code/make_collector.py"""
import csv, json, os
C = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(C)
t = open(f'{C}/vworld_collect.template.js', encoding='utf-8').read()
parks = open(f'{B}/data/vworld/parks.txt', encoding='utf-8').read().strip()
area = {r['site_id']: float(r['area_m2']) for r in csv.DictReader(open(f'{B}/data/input/sites.csv', encoding='utf-8-sig'))}
img = {k: {'bounds': v['bounds']} for k, v in json.load(open(f'{B}/data/map/img/manifest.json', encoding='utf-8')).items()}
t = t.replace('__PARKS__', parks).replace('__AREA__', json.dumps(area)).replace('__IMG__', json.dumps(img))
open(f'{C}/vworld_collect.js', 'w', encoding='utf-8').write(t)
print('biz/code/vworld_collect.js', len(t), 'bytes')
