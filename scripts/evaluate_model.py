#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ratradar.config import MODELS_DIR


def main() -> None:
    parser = argparse.ArgumentParser(description="Print saved RatRadar metrics")
    parser.add_argument("--metrics", type=Path, default=MODELS_DIR / "metrics.json")
    args = parser.parse_args()
    if not args.metrics.exists():
        raise SystemExit(f"Metrics file does not exist: {args.metrics}")
    payload = json.loads(args.metrics.read_text())
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
