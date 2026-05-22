# Dashboards

The Metabase dashboard ("pNEUMA Traffic Overview") sits on top of the `analytics.*` star schema. It connects to Postgres as the **`metabase_ro`** role, which has read-only access to `analytics` only — a leaked Metabase password cannot see `raw.*` or any developer schema.

## Connection details

| Field | Value |
|---|---|
| Database type | PostgreSQL |
| Host | `postgres` (inside the compose network) or `localhost` (browser-on-host) |
| Port | 5432 |
| Database name | `warehouse` |
| Username | `metabase_ro` |
| Password | `METABASE_RO_PASSWORD` from `.env` |

## Charts

Six cards, six different visualisations — the point is to show what the data *says*, not to file every story into a bar chart.

### 1. Fleet mix
- **Source**: `analytics.dim_track` joined to `analytics.dim_vehicle_type`
- **Visualisation**: donut chart, sliced by `vehicle_type`
- **Why donut**: a single moment-in-time share-of-total reads naturally as a circle. Sorting bars by size adds zero information when the answer is "what fraction is each".

### 2. Speed profile by vehicle type
- **Source**: `analytics.fct_trajectory_points` joined to `analytics.dim_track` and `analytics.dim_vehicle_type`
- **Visualisation**: box plot per vehicle type on `speed_kmh`
- **Why box plot**: an average hides the spread. Buses might average 25 km/h but have a long tail of standing-still moments; motorcycles average 35 km/h with very tight clustering. Box plots show median, IQR, and outliers in one glance.

### 3. Speed distribution (all vehicles)
- **Source**: `analytics.fct_trajectory_points`
- **Visualisation**: area chart of count vs. binned `speed_kmh` (~30 bins)
- **Why area**: a smoothed shape conveys the long right tail and the peak around the urban speed limit better than a tower of bars.

### 4. Where traffic concentrates
- **Source**: a SQL question that buckets coordinates into a grid:
  ```sql
  SELECT
    ROUND(latitude::numeric, 4) AS lat_bin,
    ROUND(longitude::numeric, 4) AS lon_bin,
    COUNT(*) AS point_count
  FROM analytics.fct_trajectory_points
  GROUP BY 1, 2
  ```
- **Visualisation**: pivot table → heatmap (rows = `lat_bin`, columns = `lon_bin`, colour = `point_count`)
- **Why not a pin map**: Metabase's pin map plots one dot per row. With millions of trajectory points it renders as a black blob over Athens — visually noisy, analytically useless. A binned heatmap captures where the density actually is.

### 5. Longest journeys
- **Source**: `analytics.dim_track`
- **Aggregation**: top 10 tracks by `traveled_distance_m`
- **Visualisation**: table with conditional formatting (gradient on the distance column)
- **Why a table**: small-N rankings live and die by exact values. A bar chart of 10 rows wastes space the table uses for context (track_id, vehicle_type, avg speed alongside the distance).

### 6. Acceleration footprint
- **Source**: `analytics.fct_trajectory_points`, sampled
  ```sql
  SELECT lon_acceleration_ms2, lat_acceleration_ms2
  FROM analytics.fct_trajectory_points
  TABLESAMPLE BERNOULLI(1)
  ```
- **Visualisation**: scatter plot, `lon_acceleration_ms2` on X, `lat_acceleration_ms2` on Y
- **Why scatter**: the "kamm circle" of vehicle dynamics — accelerations stay within a roughly elliptical envelope around (0, 0). Outliers along the axes are heavy braking/accelerating events; off-axis points are cornering. Tells a story no aggregate can.

## Screenshots

Saved in [docs/screenshots/](screenshots/) for the writeup.

| File | What it shows |
|---|---|
| `dashboard_overview.png` | The full dashboard at default size |
| `fleet_mix.png` | Card 1 alone |
| `speed_profile_boxplot.png` | Card 2 alone |
| `trajectory_heatmap.png` | Card 4 alone |
| `acceleration_scatter.png` | Card 6 alone |

## Why `metabase_ro` instead of `warehouse` or `postgres`

The `metabase_ro` role exists *specifically* for this. Postgres role separation is the answer to "what if Metabase is compromised?" Granting it only `SELECT` on `analytics` means:

- It can build any dashboard from the published marts.
- It cannot read `raw.*` (no source-tracking columns or in-flight loads).
- It cannot read `staging.*` or `intermediate.*` (no dbt working state).
- It cannot write anywhere.

`init.sh` sets this up with `ALTER DEFAULT PRIVILEGES`, so every new mart dbt creates is automatically granted to `metabase_ro` — no per-model GRANT needed.
