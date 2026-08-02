# Data discovery scripts

Run metadata-only Sentinel-2 discovery through Earth Engine from the repository root:

```powershell
$env:EARTH_ENGINE_PROJECT='your-google-cloud-project-id'
python -m scripts.data.discover_earth_engine --pilot all
```

The command queries `COPERNICUS/S2_SR_HARMONIZED` for the fixed Nagpur and Bengaluru Urban windows and writes sanitized reports to `data/raw/earth-engine-discovery/`. That directory is ignored by Git. Authenticate locally first with `earthengine authenticate`.

The configured bounding boxes are government-published search envelopes, not approved analytical district polygons. Do not use them for clipping, area calculation, common-valid coverage, or public map boundaries.

The reports intentionally omit provider URLs and credentials. They contain enough metadata to select candidate image IDs before a separate controlled processing/export step. `discover_catalog.py` remains the direct-CDSE fallback.
