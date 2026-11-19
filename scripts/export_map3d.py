#!/usr/bin/env python3
"""Export the existing D/C/F analysis to a public, static GitHub Pages 3D map.

Inputs MUST be actual Cheongju park boundaries with a stable official site_id.
No mock parks, financial estimates, or temperature values are generated.

Examples:
  python scripts/export_map3d.py --boundary data/park_boundary.geojson \
    --master data/master_d0.csv --need data/need_dc.csv \
    --exec data/exec_f_ext.csv --output docs/parks_3d.geojson

Optional datasets may include (site_id + relevant columns):
  --finance data/finance_k2k4.csv  # k2_city_burden_won, k4_invested_won, ...
  --heat data/heat_metrics.csv     # lst_mean_c, heat_reduction_c (ONLY measured/model-derived)

Every metric keeps <name>__status and <name>__src, if present.
"""
import argparse
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

ALLOWED_METRICS = [
    'd_irreplaceable_pop', 'd_shared_pop', 'd_unserved_share',
    'd_area_gap_m2pc', 'c_dpc_median', 'c_rank_spread', 'c_axis_dist_m',
    'f_public_ratio', 'f_private_owners', 'f_high_value_ratio',
    'f_margin_plan', 'f_margin_direct', 'f_margin_grant',
    'f_margin_special', 'f_paid_area_ratio', 'f_spent_won',
    'k2_city_burden_won', 'k4_invested_won',
    'lst_mean_c', 'heat_reduction_c',
]
DISPLAY_FIELDS = ['site_id', 'park_name', 'park_type', 'area_m2', 'lapse_year',
                  'lapse_date', 'exec_stage', 'n_grade', 'judgment', 'financing_route']


def norm_id(x):
    if pd.isna(x):
        return ''
    s = str(x).strip()
    if s.endswith('.0') and s[:-2].isdigit():
        s = s[:-2]
    return s


def read_tab(path, label):
    df = pd.read_csv(path, dtype={'site_id': 'string'})
    if 'site_id' not in df.columns:
        raise ValueError(f'{label} lacks site_id')
    df['site_id'] = df['site_id'].map(norm_id)
    if df['site_id'].eq('').any() or df['site_id'].duplicated().any():
        raise ValueError(f'{label}: empty/duplicate site_id')
    return df


def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('--boundary', required=True)
    a.add_argument('--master')
    a.add_argument('--need')
    a.add_argument('--exec', dest='execution')
    a.add_argument('--finance')
    a.add_argument('--heat')
    a.add_argument('--output', default='docs/parks_3d.geojson')
    a.add_argument('--expected', type=int, default=40)
    args = a.parse_args()

    geo = gpd.read_file(args.boundary)
    if 'site_id' not in geo.columns:
        raise ValueError('Boundary lacks site_id. Join by verified official park_name to master first; never guess IDs.')
    if geo.crs is None:
        raise ValueError('Boundary has no CRS. Assign correct source CRS before export; do not guess EPSG.')
    geo['site_id'] = geo['site_id'].map(norm_id)
    if len(geo) != args.expected or geo.site_id.duplicated().any() or geo.site_id.eq('').any():
        raise ValueError(f'Expected {args.expected} unique official sites, found {len(geo)} rows, {geo.site_id.nunique()} IDs')
    if args.expected == 40 and set(geo.site_id) != {str(i) for i in range(1, 41)}:
        raise ValueError('Official 40-site identifiers must be exactly site_id 1..40')
    if geo.geometry.isna().any() or geo.geometry.is_empty.any():
        raise ValueError('One or more missing/empty park geometries')
    if not set(geo.geometry.geom_type).issubset({'Polygon', 'MultiPolygon'}):
        raise ValueError('Park boundaries must be polygons')

    for label, path in [('master', args.master), ('need', args.need),
                        ('execution', args.execution), ('finance', args.finance), ('heat', args.heat)]:
        if not path:
            continue
        df = read_tab(path, label)
        fields = [k for k in df.columns if k in DISPLAY_FIELDS or k in ALLOWED_METRICS
                  or any(k == f'{m}{suffix}' for m in ALLOWED_METRICS for suffix in ('__status', '__src'))]
        # Duplicate descriptive fields are common between boundary and official master.
        # Validate their equality instead of overwriting or raising unnecessarily.
        shared = [c for c in fields if c != 'site_id' and c in geo.columns]
        if shared:
            left = geo[['site_id'] + shared].merge(df[['site_id'] + shared], on='site_id',
                                                   how='left', suffixes=('_map', '_table'), validate='one_to_one')
            for c in shared:
                a = left[c + '_map'].astype('string').fillna('')
                b = left[c + '_table'].astype('string').fillna('')
                if (a != b).any():
                    raise ValueError(f'{label}: {c} disagrees with boundary values; resolve in source data')
        fields = [c for c in fields if c != 'site_id' and c not in geo.columns]
        geo = geo.merge(df[['site_id'] + fields], on='site_id', how='left', validate='one_to_one')

    geo = geo.to_crs(epsg=4326)
    allowed = set(['geometry'] + DISPLAY_FIELDS + ALLOWED_METRICS)
    allowed |= {m + suffix for m in ALLOWED_METRICS for suffix in ('__status', '__src')}
    out = geo[[c for c in geo.columns if c in allowed]].copy()
    for m in ALLOWED_METRICS:
        if m not in out:
            continue
        # Preserve nulls: missing measurements should NEVER be rendered as zero.
        vals = pd.to_numeric(out[m], errors='coerce')
        out[m] = vals.where(pd.notna(vals), None)
        status = m + '__status'
        if status not in out:
            out[status] = '미산정'
        else:
            out[status] = out[status].where(out[status].isin(['확정', '가정', '미산정']), '미산정')
        src = m + '__src'
        if src not in out:
            out[src] = ''
        # Never render a numerical value without status + provenance key.
        invalid = out[m].isna() | out[status].eq('미산정') | out[src].isna() | out[src].astype('string').str.strip().eq('')
        out.loc[invalid, m] = None
        out.loc[invalid, status] = '미산정'
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    obj = json.loads(out.to_json())
    # Robust JSON encoding of numeric nulls is supplied by GeoPandas.to_json.
    target.write_text(json.dumps(obj, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f'Wrote {len(obj["features"])} verified boundaries to {target} in WGS84 (EPSG:4326).')
    print('Check provenance: each unavailable indicator is NULL/미산정, not 0.')


if __name__ == '__main__':
    main()
