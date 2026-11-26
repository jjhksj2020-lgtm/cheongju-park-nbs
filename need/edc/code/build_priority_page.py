"""need/out/priority_map.json + priority_template.html → need/edc/우선순위_시험판.html (한 파일, 더블클릭으로 열림)
먼저 build_priority.py (그리고 build_hotspot.py) 를 실행해야 한다."""
import json, os
from common import EDC, OUT

d = json.load(open(f'{OUT}/priority_map.json', encoding='utf-8'))
hp = f'{OUT}/hotspot_map.json'   # build_hotspot.py 결과(없으면 핫스팟 탭은 대기 표시)
d['hot'] = json.load(open(hp, encoding='utf-8')) if os.path.exists(hp) else None
t = open(f'{EDC}/code/priority_template.html', encoding='utf-8').read()
html = t.replace('__DATA__', json.dumps(d, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/'))
out = f'{EDC}/우선순위_시험판.html'
open(out, 'w', encoding='utf-8').write(html)
print(out, os.path.getsize(out) // 1024, 'KB')
