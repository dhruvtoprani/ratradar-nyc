from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_geojson(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def normalize_modzcta_geojson(payload: dict[str, Any]) -> dict[str, Any]:
    for feature in payload.get("features", []):
        properties = feature.setdefault("properties", {})
        zip_code = str(
            properties.get("modzcta")
            or properties.get("MODZCTA")
            or properties.get("zcta")
            or ""
        ).zfill(5)
        properties["zip_code"] = zip_code
        feature["id"] = zip_code
    return payload
