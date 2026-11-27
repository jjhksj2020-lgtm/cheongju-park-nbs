"""data/r1_newgreen_kr_patches.txt 압축 형식을 (위도, 경도, 픽셀수) 목록으로 푼다."""
import sys
def load(p='data/r1_newgreen_kr_patches.txt'):
    body = ' '.join(l for l in open(p, encoding='utf-8') if not l.startswith('#')).split()
    out, lat = [], 0
    for tok in body:
        a, b, c = tok.split('.')
        lat += int(a, 36)
        out.append((lat / 1e4, (1260000 + int(b, 36)) / 1e4, int(c, 36)))
    return out
if __name__ == '__main__':
    P = load(); print(len(P), P[0], P[-1], sum(1 for p in P if p[0] < 36.0 or p[0] > 37.75 or p[1] < 126.6 or p[1] > 127.9), '중부권 밖')
