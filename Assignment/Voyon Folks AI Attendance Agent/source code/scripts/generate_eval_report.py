#!/usr/bin/env python
"""Generate structured evaluation report (JSON + Markdown).

Usage (from voyonattenagent/):
    python scripts/generate_eval_report.py
    python scripts/generate_eval_report.py --mode live
    python scripts/generate_eval_report.py --json docs/evaluation_report.json --md docs/evaluation_report.md
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.eval_runner import main

if __name__ == "__main__":
    main()
