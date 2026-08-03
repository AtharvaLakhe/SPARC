# Data discovery scripts

Run metadata-only Sentinel-2 discovery through Earth Engine from the repository root:

```powershell
$env:EARTH_ENGINE_PROJECT='your-google-cloud-project-id'
python -m scripts.data.discover_earth_engine --pilot all
```

The command queries `COPERNICUS/S2_SR_HARMONIZED` for the fixed Nagpur and Bengaluru Urban windows and writes sanitized reports to `data/raw/earth-engine-discovery/`. That directory is ignored by Git. Authenticate locally first with `earthengine authenticate`.

The configured bounding boxes are government-published search envelopes, not approved analytical district polygons. Do not use them for clipping, area calculation, common-valid coverage, or public map boundaries.

The reports intentionally omit provider URLs and credentials. They contain enough metadata to select candidate image IDs before a separate controlled processing/export step. `discover_catalog.py` remains the direct-CDSE fallback.

## Boundary gate before processing

Do not use a search bounding box as an analytical district boundary. Before any Earth Engine composite or area calculation, validate the local GeoJSON and its reviewed provenance record:

```powershell
python -m scripts.data.validate_boundary_gate `
  --boundary path\\to\\approved-district.geojson `
  --provenance path\\to\\approved-district-provenance.json
```

The provenance JSON must provide `sourceName`, an `https` `sourceUrl`, `version`, `license`, `attribution`, and `redistributionPermitted: true`. The command rejects missing permission, non-polygon data, invalid coordinates, open rings, multi-feature inputs, and files larger than 5 MiB. It writes only a local hash/provenance manifest under ignored `data/raw/boundary-gate/`; it does not call Earth Engine or export imagery.

## P0 pre-publication processing

After the pinned geoBoundaries extraction and boundary gate have passed, calculate local pre-publication summaries without exporting to Google Drive or exposing a live API route:

```powershell
$env:EARTH_ENGINE_PROJECT='your-google-cloud-project-id'
python -m scripts.data.extract_geoboundaries_adm2
python -m scripts.data.process_earth_engine_p0 --region all
```

The worker uses `COPERNICUS/S2_SR_HARMONIZED`, allows SCL classes 4/5/6 only, requires two clear observations per period, calculates indices per observation before taking a median, and compares only the common-valid footprint. Results go to ignored `data/processed/earth-engine-p0/` and are explicitly pre-publication until threshold sensitivity and independent validation complete.

### Interactive timeout: controlled batch export

Do not increase resolution, use `bestEffort`, or relax masks when a district-wide 10 m reduction exceeds the interactive deadline. The worker can package the same scalar calculation as an Earth Engine CSV batch export. A dry run writes only a local, ignored request record:

```powershell
python -m scripts.data.process_earth_engine_p0 `
  --region nagpur `
  --indicator vegetation `
  --mode batch-export `
  --drive-folder SPARC_EE
```

Adding `--start-batch-export` creates a task and writes its result to the named Google Drive folder. That is an external write, so use it only after the destination has been approved. The downloaded CSV is pre-publication evidence, not a deployable application asset, until it has been imported into a provenance-complete manifest and passed sensitivity and independent-validation gates.

After downloading the completed CSV into the ignored raw-export directory, validate its task request, region, boundary checksum, method, CRS, pixel size, observation floor, and area arithmetic before producing the local report:

```powershell
python -m scripts.data.process_earth_engine_p0 `
  --region nagpur `
  --indicator vegetation `
  --import-export-csv data\raw\earth-engine-exports\sparc_nagpur_vegetation_p0_v1.csv
```
