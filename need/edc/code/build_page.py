"""need/out/edc_map.json + page_template.html → need/edc/EDC_지도.html (한 파일, 더블클릭으로 열림)
먼저 build_edc.py 를 실행해야 한다."""
import json, os
from common import EDC, OUT

d = json.load(open(f'{OUT}/edc_map.json', encoding='utf-8'))
t = open(f'{EDC}/code/page_template.html', encoding='utf-8').read()
html = t.replace('__DATA__', json.dumps(d, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/'))
out = f'{EDC}/EDC_지도.html'
open(out, 'w', encoding='utf-8').write(html)
print(out, os.path.getsize(out) // 1024, 'KB')
