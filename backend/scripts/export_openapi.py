"""Export the OpenAPI schema to a JSON file for frontend TypeScript codegen.

Usage:
    python scripts/export_openapi.py

Output:
    shared/openapi.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.main import app  # noqa: E402


def export() -> None:
    """Export FastAPI OpenAPI schema to the shared directory."""
    schema = app.openapi()
    output_path = Path(__file__).resolve().parents[2] / "shared" / "openapi.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(f"OpenAPI schema exported to {output_path}")


if __name__ == "__main__":
    export()
