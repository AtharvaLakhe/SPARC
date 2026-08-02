# SPARC API

This is the first implementation slice: a read-only FastAPI service backed by the committed synthetic contract examples. It performs no raster processing, database access, provider calls, or live job creation.

## Run locally

From the repository root:

```powershell
python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000
```

The default allowed browser origins are `http://localhost:5173` and the supplied Orbital UI reference at `http://localhost:8123`. Override them with a comma-separated `SPARC_ALLOWED_ORIGINS` value. Do not use `*`.

## Request flow

```text
HTTP request
→ request ID and size checks
→ FastAPI/Pydantic syntax and type validation
→ date and comparison domain validation
→ allowlisted in-memory catalogue lookup
→ immutable synthetic JSON response
→ sanitized Problem Details on failure
```

`POST /api/v1/comparisons` only resolves precomputed mock results. `modePreference: live` is rejected, and the administrative processing-creation route is not implemented.

## Tests

Install the pinned test extra and run the standard-library suite:

```powershell
python -m pip install -r apps/api/requirements-dev.txt
python -m unittest discover -s tests -p "test_*.py"
```
