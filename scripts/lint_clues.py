#!/usr/bin/env python3
"""Contrôles mécaniques d'une définition de mots croisés (sans modèle, gratuits).

Usage en module :
    from lint_clues import lint_clue
    problems, cleaned = lint_clue("ZELDA", "Princesse d'Hyrule", existing=["Héros en vert"])

Usage en ligne de commande (fichier JSONL, une entrée par ligne :
{"answer": "ZELDA", "clues": [{"level": 1, "text": "..."}]}) :
    python3 scripts/lint_clues.py entrees.jsonl [--max-len 80]
Code de sortie 0 si aucun problème, 1 sinon.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata

MAX_LEN = 80


def normalize(text: str) -> str:
    """Majuscules sans accents, lettres A-Z séparées par des espaces."""
    decomposed = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(c for c in decomposed if not unicodedata.combining(c))
    return re.sub(r"[^A-Z]+", " ", ascii_text.upper()).strip()


def leaks_answer(answer: str, clue: str) -> bool:
    """Vrai si la définition contient la réponse ou un dérivé direct (même début)."""
    stem = answer[: max(4, len(answer) - 1)] if len(answer) > 4 else answer
    for token in normalize(clue).split():
        if token == answer or (len(token) >= len(stem) and token.startswith(stem)):
            return True
    return answer in normalize(clue).replace(" ", "")


def clean(text: str) -> str:
    """Corrections sûres : apostrophes droites, espaces, point final retiré."""
    text = text.replace("’", "'").replace("‘", "'").replace(" ", " ")
    text = re.sub(r"\s+", " ", text).strip()
    if text.endswith(".") and not text.endswith(".."):
        text = text[:-1].rstrip()
    return text


def _tokens(text: str) -> set[str]:
    return {t for t in normalize(text).split() if len(t) > 2}


def similarity(a: str, b: str) -> float:
    """Part de mots communs (indice de Jaccard) entre deux définitions."""
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def lint_clue(answer: str, text: str, existing: list[str] | None = None,
              max_len: int = MAX_LEN, near_duplicate: float = 0.6) -> tuple[list[str], str]:
    """Renvoie (problèmes, texte nettoyé). `answer` est la réponse sans accents ni espaces."""
    problems: list[str] = []
    cleaned = clean(text)
    if not cleaned:
        return ["vide"], cleaned
    if len(cleaned) > max_len:
        problems.append(f"trop longue ({len(cleaned)} > {max_len})")
    if leaks_answer(answer, cleaned):
        problems.append("contient la réponse ou un dérivé")
    if any(ch in cleaned for ch in "—–"):
        problems.append("tiret long (remplacer par une virgule ou deux-points)")
    if re.search(r"[\U0001F000-\U0001FFFF☀-➿]", cleaned):
        problems.append("emoji")
    for other in existing or []:
        if normalize(other) == normalize(cleaned):
            problems.append("identique à une définition existante")
            break
        if similarity(other, cleaned) >= near_duplicate:
            problems.append(f"quasi-doublon de : {other}")
            break
    return problems, cleaned


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("path", help="fichier JSONL d'entrées")
    parser.add_argument("--max-len", type=int, default=MAX_LEN)
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    bad = 0
    total = 0
    with open(args.path, encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            entry = json.loads(line)
            answer = normalize(entry["answer"]).replace(" ", "")
            texts: list[str] = []
            for clue in entry["clues"]:
                total += 1
                problems, _ = lint_clue(answer, clue["text"], texts, args.max_len)
                texts.append(clue["text"])
                if problems:
                    bad += 1
                    print(f"{answer}: {clue['text']!r} -> {'; '.join(problems)}")
    print(f"{total} définitions contrôlées, {bad} avec problème")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
