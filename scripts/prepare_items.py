#!/usr/bin/env python3
"""Transforme des candidats (sortie de `run_stage.py candidates`) en entrées prêtes à rédiger.

Pour chaque candidat : réponse normalisée (A-Z), filtre de longueur, rejet des doublons (liste
d'existants, variantes singulier/pluriel, doublons du lot), puis fiche Wikidata (preuve d'existence)
quand elle est demandée. Les rejets sont écrits dans `<sortie>.rejects`, avec leur raison.

Usage :
  python3 scripts/prepare_items.py candidates.jsonl items.jsonl --existing existants.txt \
      --min-len 3 --max-len 13 --lang fr --cache wd_cache.json

`existants.txt` : une réponse par ligne (A-Z). Chaque ligne de sortie :
  {"id", "answer", "display", "domain", "source": {"qid", "label", "description", "exact"}}
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lint_clues import normalize  # noqa: E402
from wikidata import polite_lookup  # noqa: E402


def answer_of(form: str) -> str:
    """Réponse A-Z d'une graphie lisible (« Spider-Man » -> SPIDERMAN)."""
    return normalize(form).replace(" ", "")


def display_of(form: str) -> str:
    """Graphie lisible à garder seulement si la réponse s'écrit en plusieurs mots (espace ou trait d'union)."""
    form = re.sub(r"\s+", " ", form).strip()
    return form if any(sep in form for sep in " -") else ""


def variants(answer: str) -> set[str]:
    """Formes proches à traiter comme le même élément (pluriel en S ou X)."""
    out = {answer}
    for suffix in ("S", "X"):
        if answer.endswith(suffix) and len(answer) > 3:
            out.add(answer[:-1])
        out.add(answer + suffix)
    return out


def prepare(rows: list[dict], existing: set[str], *, min_len: int, max_len: int, resolve=None) -> tuple[list[dict], list[dict]]:
    """Renvoie (entrées retenues, rejets). `resolve(terme)` renvoie une fiche ou None ; None = pas de fiche exigée."""
    kept: list[dict] = []
    rejected: list[dict] = []
    seen: set[str] = set(existing)
    for row in rows:
        form = str(row.get("form", "")).strip()
        answer = answer_of(form)
        reason = ""
        source = None
        if not form or any(ch.isdigit() for ch in form):
            reason = "graphie vide ou avec chiffres"
        elif not min_len <= len(answer) <= max_len:
            reason = f"longueur {len(answer)} hors de {min_len}-{max_len}"
        elif variants(answer) & seen:
            reason = "doublon ou variante d'une réponse existante"
        elif resolve is not None:
            source = resolve(str(row.get("hint") or form))
            if source is None:
                reason = "aucune fiche Wikidata"
        if reason:
            rejected.append({"form": form, "domain": row.get("domain", ""), "reason": reason})
            continue
        seen.add(answer)
        item = {"id": answer, "answer": answer, "display": display_of(form),
                "domain": row.get("domain") or row.get("theme", "")}
        if source:
            item["source"] = source
        kept.append(item)
    return kept, rejected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("candidates")
    parser.add_argument("output")
    parser.add_argument("--existing", help="fichier texte, une réponse A-Z par ligne")
    parser.add_argument("--min-len", type=int, default=3)
    parser.add_argument("--max-len", type=int, default=13)
    parser.add_argument("--lang", default="fr", help="langue des libellés Wikidata")
    parser.add_argument("--cache", help="cache JSON des fiches Wikidata")
    parser.add_argument("--no-wikidata", action="store_true", help="ne pas chercher de fiche (déconseillé)")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    existing: set[str] = set()
    if args.existing:
        existing = {line.strip().upper() for line in Path(args.existing).read_text(encoding="utf-8").splitlines() if line.strip()}
    rows = [json.loads(line) for line in Path(args.candidates).read_text(encoding="utf-8").splitlines() if line.strip()]
    cache = Path(args.cache) if args.cache else None
    resolve = None if args.no_wikidata else (lambda term: polite_lookup(term, lang=args.lang, cache=cache))
    kept, rejected = prepare(rows, existing, min_len=args.min_len, max_len=args.max_len, resolve=resolve)
    with Path(args.output).open("w", encoding="utf-8") as handle:
        for item in kept:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")
    with Path(args.output + ".rejects").open("w", encoding="utf-8") as handle:
        for row in rejected:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({"candidates": len(rows), "kept": len(kept), "rejected": len(rejected)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
