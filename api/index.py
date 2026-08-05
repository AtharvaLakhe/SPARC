"""Vercel ASGI entrypoint for the SPARC API.

The API remains the same FastAPI application used locally. Vercel invokes the
exported ``app`` object as a Python function; no credentials or Earth Engine
workers run in the deployed function.
"""

from __future__ import annotations

import os
import tempfile

# Vercel's function filesystem is read-only. Report artifacts are explicitly
# ephemeral in P0, so use the writable temporary filesystem for this runtime.
os.environ.setdefault("SPARC_DATA_MODE", "precomputed")
os.environ.setdefault("SPARC_REPORT_WORKSPACE", os.path.join(tempfile.gettempdir(), "sparc-reporting"))

from apps.api.app.main import app  # noqa: E402

__all__ = ["app"]
