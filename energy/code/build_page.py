"""에너지 지도 최종본 만들기 → energy/에너지_지도.html (한 파일, 인터넷 없이 더블클릭으로 열림)
순서: python energy/code/energy_engine.py → python energy/code/build_page.py"""
import os
C = os.path.dirname(os.path.abspath(__file__)); E = os.path.dirname(C)
t = open(f'{C}/page_template.html', encoding='utf-8').read()
data = open(f'{E}/out/energydata.json', encoding='utf-8').read()
out = f'{E}/에너지_지도.html'
open(out, 'w', encoding='utf-8').write('<!doctype html>\n<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
                                        + t.replace('__DATA__', data) + '\n</html>\n')
print('energy/에너지_지도.html', os.path.getsize(out) // 1024, 'KB')
