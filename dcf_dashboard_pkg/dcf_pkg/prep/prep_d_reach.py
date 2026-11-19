"""D 결핍 전처리: 100m 격자 → 공원까지 보행 네트워크 거리 → data/grid_reach.csv, data/site_admin.csv.

※ 이 스크립트는 geopandas·osmnx가 없는 환경에서 작성되어 실행 검증 전이다. 11주차에 실데이터로 돌리고
  결과를 국토통계지도 생활권공원 접근성 격자(검증용)와 방향이 맞는지 비교한다.

입력 (EPSG:5186)
  data/sgis_grid_100m.gpkg      D5  : grid_id, pop, pop65, geometry(격자 폴리곤)
  data/built_parks.gpkg         D6+D4 : park_type, geometry (이미 조성된 공원. 40개소는 넣지 않는다)
  data/park_boundary.geojson    D4  : park_name → master_d0.csv의 site_id로 대조
  data/master_d0.csv            D0
  data/admin_dong.gpkg          D8  : admin_code, geometry
  보행망: --network osm(기본, status=가정) | --network ktdb <파일>(국가교통DB, status=확정)

실행
  python prep/prep_d_reach.py --factor 1.0      # 민감도: --factor 0.5 / 1.5
"""
from __future__ import annotations

import argparse

import geopandas as gpd
import networkx as nx
import pandas as pd

import engine_dcf as E

CRS = "EPSG:5186"


def entrance_points(polys: gpd.GeoDataFrame, step_m: float) -> gpd.GeoDataFrame:
    """공원 경계를 step_m 간격 점으로 바꿔 입구를 대신한다."""
    rows = []
    for idx, r in polys.iterrows():
        ring = r.geometry.boundary
        n = max(int(ring.length // step_m), 1)
        for i in range(n):
            rows.append({"idx": idx, "geometry": ring.interpolate(i * step_m)})
    return gpd.GeoDataFrame(rows, crs=polys.crs)


def load_graph(kind: str, path: str | None, bounds) -> nx.Graph:
    if kind == "osm":
        import osmnx as ox
        minx, miny, maxx, maxy = gpd.GeoSeries.from_xy([bounds[0], bounds[2]], [bounds[1], bounds[3]],
                                                       crs=CRS).to_crs(4326).total_bounds
        g = ox.graph_from_bbox((minx, miny, maxx, maxy), network_type="walk")
        return ox.project_graph(g, to_crs=CRS).to_undirected()
    edges = gpd.read_file(path).to_crs(CRS)          # 국가교통DB 링크: F_NODE, T_NODE, geometry
    g = nx.Graph()
    for r in edges.itertuples():
        g.add_edge(r.F_NODE, r.T_NODE, length=r.geometry.length)
    return g


def nearest_nodes(g: nx.Graph, pts: gpd.GeoSeries):
    import osmnx as ox
    return ox.distance.nearest_nodes(g, pts.x.to_numpy(), pts.y.to_numpy(), return_dist=True)


def reach(g, src_nodes, src_snap, cutoff):
    """입구 점들에서 cutoff(m) 안의 노드 → 거리(입구 스냅 거리 포함)."""
    best: dict = {}
    for n, s in zip(src_nodes, src_snap):
        if s > cutoff:
            continue
        for v, d in nx.single_source_dijkstra_path_length(g, n, cutoff=cutoff - s, weight="length").items():
            if d + s < best.get(v, float("inf")):
                best[v] = d + s
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", default="params_dcf.yaml")
    ap.add_argument("--factor", type=float, default=1.0)
    ap.add_argument("--network", default="osm")
    ap.add_argument("--network-file")
    ap.add_argument("--step", type=float, default=30.0)
    a = ap.parse_args()
    P = E.load_params(a.params)

    grid = gpd.read_file("data/sgis_grid_100m.gpkg").to_crs(CRS)
    built = gpd.read_file("data/built_parks.gpkg").to_crs(CRS)
    master = pd.read_csv("data/master_d0.csv")
    sites = gpd.read_file("data/park_boundary.geojson").to_crs(CRS).merge(master, on="park_name")
    admin = gpd.read_file("data/admin_dong.gpkg").to_crs(CRS)

    g = load_graph(a.network, a.network_file, grid.total_bounds)
    cent = grid.geometry.centroid
    g_nodes, g_snap = nearest_nodes(g, cent)

    def served_nodes(polys: gpd.GeoDataFrame) -> dict:
        out: dict = {}
        for t, grp in polys.groupby("park_type"):
            sd = E.service_distance(t, P)
            if sd.value is None:
                continue
            ent = entrance_points(grp, a.step)
            n, s = nearest_nodes(g, ent.geometry)
            for v, d in reach(g, n, s, sd.value * a.factor).items():
                out[v] = min(out.get(v, float("inf")), d)
        return out

    def grid_within(node_dist: dict, cutoff: float):
        return [(nd in node_dist) and (node_dist[nd] + sn <= cutoff) for nd, sn in zip(g_nodes, g_snap)]

    # 1) 조성 공원 어느 곳이든 유형별 유치거리 안이면 served
    served = [False] * len(grid)
    for t, grp in built.groupby("park_type"):
        sd = E.service_distance(t, P)
        if sd.value is None:
            continue
        nd = served_nodes(grp)
        served = [x or y for x, y in zip(served, grid_within(nd, sd.value * a.factor))]

    # 2) 40개소 각각의 유치권
    reach_sites = [[] for _ in range(len(grid))]
    for _, s in sites.iterrows():
        sd = E.service_distance(s["park_type"], P)
        if sd.value is None:
            continue
        nd = served_nodes(gpd.GeoDataFrame([s], crs=CRS))
        for i, ok in enumerate(grid_within(nd, sd.value * a.factor)):
            if ok:
                reach_sites[i].append(s["site_id"])

    pop_status = "확정"
    out = pd.DataFrame({
        "grid_id": grid["grid_id"], "pop": grid["pop"], "pop_status": pop_status,
        "served_by_built": served, "reach_sites": [";".join(x) for x in reach_sites],
    })
    suffix = "" if a.factor == 1.0 else f"_f{a.factor}"
    out.to_csv(f"data/grid_reach{suffix}.csv", index=False)

    # 3) 공원 → 행정동(겹치는 면적이 가장 큰 곳)
    ov = gpd.overlay(sites[["site_id", "geometry"]], admin[["admin_code", "geometry"]], how="intersection")
    ov["a"] = ov.area
    ov.sort_values("a").groupby("site_id").tail(1)[["site_id", "admin_code"]].to_csv("data/site_admin.csv", index=False)
    print(f"network status = {'가정' if a.network == 'osm' else '확정'} → params need_d.network_status에 맞춰 둘 것")


if __name__ == "__main__":
    main()
