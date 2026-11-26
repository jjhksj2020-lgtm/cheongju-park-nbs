"""발표용 껍데기를 통합 지도에 씌운다 — 주제·목적 → 공원이란 → 이용성 → 에너지저감 → 사업성 → 종합 우선순위.
지도 앱(total_template.html)은 그대로 두고, 앞에 설명 페이지(present_shell.html)와 페이지 넘기기(present_shell.js)를 붙이고,
지도 보정(present_map.js: 청주시 경계 모양 배경, 3D에서 공원 모양이 솟는 블록, 시 경계에 맞춘 첫 화면)을 덧붙인다.

  build_total.py 가 마지막에 wrap() 을 부른다 (보통은 이것만 쓰면 됨).
  python total/code/present.py   # 계산 없이: 이미 만든 total/*.html 안의 데이터를 꺼내 발표판만 다시 만든다
                                 # (need/edc 계산에 shapely 등이 없는 환경용)
숫자 기준값은 biz/code/params.yaml 에서 읽는다(1단계 실효년도·민간특례 면적·월명공원 검증값)."""
import json, os, sys
import yaml
C = os.path.dirname(os.path.abspath(__file__)); T = os.path.dirname(C); ROOT = os.path.dirname(T)
OUT = f'{T}/청주_장기미집행_공원_40개소_조성_지도.html'
TITLE = '청주시 장기미집행 공원 40개소 — 조성 우선순위 판단'


def pz():
    B = yaml.safe_load(open(f'{ROOT}/biz/code/params.yaml', encoding='utf-8'))
    return {'stage1_expiry_max': B['stage_rules']['stage1_expiry_max'],
            'special_min_m2': B['special_project']['min_area_m2'],
            'wolmyeong': B['validation']['wolmyeong']}


def edc_geo():
    """이용성 공원 화면용: need/edc/EDC_지도.html(이용성 파트 결과물) 안의 100m 인구 격자·기존 공원·이용 거리(버퍼)를 꺼낸다.
    cells = [경도, 위도, 인구, 아동·고령 비율], served = 기존 공원 이용권(합쳐진 면), existing = 기존 공원 경계, buffer = 대상 공원 이용 거리."""
    f = f'{ROOT}/need/edc/EDC_지도.html'
    if not os.path.exists(f):
        return None
    s = open(f, encoding='utf-8').read()
    a = s.index('=', s.index('const D')) + 1
    E, _ = json.JSONDecoder().raw_decode(s[a:].lstrip())
    return {'asof': E.get('asof'), 'pop_source': E.get('pop_source'), 'cells': E['cells'], 'served': E['served'],
            'existing': E['existing'], 'buffer': {k: v['buffer'] for k, v in E['geo'].items()}}


def wrap(page):
    """page = 데이터가 들어간 지도 앱 본문(total_template.html 치환 결과). 발표판 전체 HTML을 돌려준다."""
    shell = open(f'{C}/present_shell.html', encoding='utf-8').read()
    js = open(f'{C}/present_shell.js', encoding='utf-8').read()
    mapjs = open(f'{C}/present_map.js', encoding='utf-8').read()   # 청주시 모양 배경 · 3D 공원 블록 · 처음 화면 맞춤
    page = page.replace('<div class="wrap">', '<div class="wrap" id="app">', 1)
    page = page.replace('<title>청주 장기미집행 공원 40개소 조성 지도</title>', f'<title>{TITLE}</title>', 1)
    # V-World 키는 HTML에 넣지 않고 옆 파일(vworld_key.js, git 제외)에서 읽는다 — 없으면 404로 넘어가고 파일 안 사진을 씀
    body = '<script src="vworld_key.js"></script>\n' + shell + page + '\n<script>\nconst PZU = ' + json.dumps(edc_geo(), ensure_ascii=False, separators=(',', ':')) + ';\n' + mapjs + '</script>\n<script>\nconst PZ = ' + json.dumps(pz(), ensure_ascii=False) + ';\n' + js + '</script>\n'
    return ('<!doctype html>\n<html lang="ko" data-theme="light"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n' + body + '\n</html>\n')


def from_html(path):
    """이미 만든 지도/발표판 HTML에서 사진·지형(__ASSETS__)과 데이터(D)를 꺼낸다."""
    s = open(path, encoding='utf-8').read()
    a = s.index('const __ASSETS__ = ') + len('const __ASSETS__ = ')
    b = s.index(';\nconst D = ', a)
    d0 = b + len(';\nconst D = ')
    d1 = s.index(';\n// 한 파일판', d0)
    return json.loads(s[a:b]), json.loads(s[d0:d1])


def page_of(assets, D):
    t = open(f'{C}/total_template.html', encoding='utf-8').read()
    return t.replace('__DATA__', json.dumps(D, ensure_ascii=False, separators=(',', ':'))).replace(
        'const D = ', 'const __ASSETS__ = ' + json.dumps(assets) + ';\nconst D = ', 1)


if __name__ == '__main__':
    assets, D = from_html(sys.argv[1] if len(sys.argv) > 1 else OUT)
    open(OUT, 'w', encoding='utf-8').write(wrap(page_of(assets, D)))
    print(f'{os.path.relpath(OUT, ROOT)} {os.path.getsize(OUT)//1024} KB · 발표판 (데이터 기준일 {D["asof"]})')
