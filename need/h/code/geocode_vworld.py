# -*- coding: utf-8 -*-
"""
park40_addresses.csv 의 addr_search 열을 V-World 지오코딩 API로 좌표(lon, lat)로 바꿉니다.
사용법:
  1) vworld.kr 에서 인증키 발급 (즉시)
  2) 아래 KEY 에 붙여넣기
  3) python geocode_vworld.py
  → park40_geocoded.csv 생성 (lon, lat, geocode_tag 채워짐)
  → GEE Assets 에 이 CSV 를 업로드하거나, 열을 복사해 스크립트 parkList 에 붙여넣기
"""
import csv, time, requests

KEY = "여기에_V-World_인증키"
SRC = "park40_addresses.csv"
DST = "park40_geocoded.csv"
URL = "https://api.vworld.kr/req/address"

def geocode(addr, kind):
    r = requests.get(URL, params={
        "service": "address", "request": "getcoord", "version": "2.0",
        "crs": "epsg:4326", "type": kind, "address": addr, "key": KEY,
    }, timeout=15).json()
    res = r.get("response", {})
    if res.get("status") == "OK":
        pt = res["result"]["point"]
        return float(pt["x"]), float(pt["y"])
    return None

rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
for row in rows:
    addr = row["addr_search"]
    hit = geocode(addr, "parcel")                      # 지번 주소
    tag = "실자료(지번)"
    if hit is None:                                    # 산번지 등 실패 시 동·리까지만
        short = " ".join(addr.split()[:-1])
        hit = geocode(short, "parcel")
        tag = "가정(동리 중심)"
    if hit is None:
        row["lon"], row["lat"], row["geocode_tag"] = "", "", "미산정"
    else:
        row["lon"], row["lat"], row["geocode_tag"] = f"{hit[0]:.6f}", f"{hit[1]:.6f}", tag
    print(row["site_id"], row["name"], row["lon"], row["lat"], row["geocode_tag"])
    time.sleep(0.2)

with open(DST, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader(); w.writerows(rows)
print("saved:", DST)

# GEE parkList 형식으로도 출력
print("\n--- GEE parkList (복사해서 스크립트에 붙여넣기) ---")
for row in rows:
    if row["lon"]:
        print(f"  [{row['site_id']}, '{row['name']}', {row['lon']}, {row['lat']}, {row['area_m2']}],")
