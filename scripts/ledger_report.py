#!/usr/bin/env python3
"""Résume le registre des coûts (JSONL écrit par llm.py) : total, par étape, par modèle.

Usage : python3 scripts/ledger_report.py ledger.jsonl [--cap 60]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def summarize(path: Path) -> dict:
    total = 0.0
    calls = 0
    errors = 0
    by_stage: dict[str, dict] = defaultdict(lambda: {"calls": 0, "cost": 0.0, "in": 0, "out": 0})
    by_model: dict[str, float] = defaultdict(float)
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            cost = float(row.get("cost", 0.0))
            total += cost
            calls += 1
            errors += 1 if row.get("error") else 0
            stage = by_stage[row.get("stage", "")]
            stage["calls"] += 1
            stage["cost"] += cost
            stage["in"] += int(row.get("in", 0))
            stage["out"] += int(row.get("out", 0))
            by_model[row.get("model", "")] += cost
    return {"total": round(total, 4), "calls": calls, "errors": errors,
            "by_stage": {k: {**v, "cost": round(v["cost"], 4)} for k, v in by_stage.items()},
            "by_model": {k: round(v, 4) for k, v in by_model.items()}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("ledger")
    parser.add_argument("--cap", type=float, help="plafond en dollars, pour afficher le reste")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    summary = summarize(Path(args.ledger))
    if args.cap is not None:
        summary["remaining"] = round(args.cap - summary["total"], 4)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
