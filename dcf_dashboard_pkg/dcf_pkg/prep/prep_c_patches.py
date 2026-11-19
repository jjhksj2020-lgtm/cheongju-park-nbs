"""C 연결 전처리: 녹지 패치·패치 간 거리·축 거리 → data/patches.csv, data/patch_dist.csv, data/site_axis.csv.

※ geopandas가 없는 환경에서 작성되어 실행 검증 전이다. 11~12주차에 실데이터로 돌린다.

입력 (EPSG:5186)
  data/landcover.gpkg          D9 : class_code, geometry  (토지피복 세분류)
  data/biotope.gpkg            C2 : (있으면 우선) biotope_grade, geometry
  data/built_parks.gpkg        D6+D4
  data/park_boundary.geojson   D4 → master_d0.csv의 site_id
  data/green_axes.gpkg         C3 : 녹지축·수변축 선(공원녹지기본계획에서 디지타이징), digitized_from_image(bool)
  data/streams.gpkg            D11: 하천 중심선(수변축 보조)

녹지로 보는 토지피복 코드는 --green-classes로 준다(기본: 산림·초지 대분류). 팀이 정한 코드 목록을 README에 남긴다.
"""
from __future__ import annotations

import argparse
import math

import geopandas as gpd
import pandas as pd

import engine_dcf as E

CRS = "EPSG:5186"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", default="params_dcf.yaml")
    ap.add_argument("--green-classes", default="300,400")   # 토지피복 대분류 산림(300)·초지(400) 등. 세분류면 목록으로
    a = ap.parse_args()
    P = E.load_params(a.params)
    c = P["need_c"]
    green_codes = {int(x) for x in a.green_classes.split(",")}

    lc = gpd.read_file("data/landcover.gpkg").to_crs(CRS)
    lc = lc[(lc["class_code"] // 100 * 100).isin(green_codes) | lc["class_code"].isin(green_codes)]
    built = gpd.read_file("data/built_parks.gpkg").to_crs(CRS)
    master = pd.read_csv("data/master_d0.csv")
    sites = gpd.read_file("data/park_boundary.geojson").to_crs(CRS).merge(master, on="park_name")

    green = pd.concat([lc[["geometry"]], built[["geometry"]]]).union_all()
    site_union = sites.union_all()
    # 40개소 안의 녹지는 공원별 패치로 떼어 site_id를 붙인다(제거 시나리오용)
    site_patches = gpd.overlay(sites[["site_id", "geometry"]],
                               gpd.GeoDataFrame(geometry=[green], crs=CRS), how="intersection")
    other = gpd.GeoDataFrame(geometry=[green.difference(site_union)], crs=CRS)
    other["site_id"] = None
    patches = pd.concat([site_patches, other]).explode(index_parts=False).reset_index(drop=True)
    patches["area_m2"] = patches.area
    patches = patches[patches["area_m2"] >= c["min_patch_m2"]].reset_index(drop=True)
    patches["patch_id"] = [f"P{i:05d}" for i in range(len(patches))]
    patches[["patch_id", "area_m2", "site_id"]].to_csv("data/patches.csv", index=False)

    # 연결 확률이 floor 이상일 수 있는 거리까지만 간선을 만든다
    theta_min = -math.log(c["p_at_dispersal"]) / max(c["dispersal_m"])
    max_d = -math.log(c["prob_floor"]) / theta_min
    sidx = patches.sindex
    rows = []
    for i, geom in enumerate(patches.geometry):
        for j in sidx.query(geom.buffer(max_d), predicate="intersects"):
            if j <= i:
                continue
            d = geom.distance(patches.geometry.iloc[j])
            if d <= max_d:
                rows.append((patches.patch_id.iloc[i], patches.patch_id.iloc[j], d))
    pd.DataFrame(rows, columns=["a", "b", "dist_m"]).to_csv("data/patch_dist.csv", index=False)

    axes = gpd.read_file("data/green_axes.gpkg").to_crs(CRS)
    status = "가정" if axes.get("digitized_from_image", pd.Series([True])).any() else "확정"
    au = axes.union_all()
    pd.DataFrame({"site_id": sites["site_id"], "axis_dist_m": sites.geometry.distance(au),
                  "axis_status": status}).to_csv("data/site_axis.csv", index=False)


if __name__ == "__main__":
    main()
