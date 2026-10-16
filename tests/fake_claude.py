#!/usr/bin/env python3
"""Faux CLI `claude` pour les tests : lit le prompt sur l'entrée standard et répond de façon déterministe.

Il reconnaît l'étape au texte du prompt et renvoie le JSON `--output-format json` du vrai CLI
(champs `result`, `total_cost_usd`, `usage`, `is_error`). Aucun réseau, aucune clé.
"""
import json
import re
import sys

COST = 0.01


def items_of(prompt: str) -> list[dict]:
    """Lignes JSON d'entrées (une par ligne qui commence par une accolade)."""
    return [json.loads(line) for line in prompt.splitlines() if line.startswith("{") and '"id"' in line]


def answer(prompt: str) -> str:
    if "Tu résous des définitions" in prompt:
        rows = []
        for line in prompt.splitlines():
            parts = [p.strip() for p in line.split(" | ")]
            if len(parts) == 4 and "#" in parts[0]:
                answer_id = parts[0].split("#")[0]
                # Résout toujours, sauf les définitions qui contiennent « INSOLUBLE »
                rows.append({"id": parts[0], "reponses": [] if "INSOLUBLE" in parts[3] else [answer_id]})
        return json.dumps(rows)
    if "relecteur factuel" in prompt:
        rows = []
        for item in items_of(prompt):
            text = item.get("texte", "")
            if "FAUX" in text:
                rows.append({"id": item["id"], "v": "drop", "pourquoi": "fait faux", "cause": "fait"})
            elif "AMBIGU" in text:
                rows.append({"id": item["id"], "v": "drop", "pourquoi": "plusieurs réponses", "cause": "ambigu"})
            elif "CORRIGER" in text:
                rows.append({"id": item["id"], "v": "fix", "texte": "Version corrigée sans défaut", "pourquoi": "tournure"})
            else:
                rows.append({"id": item["id"], "v": "ok"})
        return json.dumps(rows)
    if "NOUVELLES définitions" in prompt:
        rows = []
        for item in items_of(prompt):
            if item["reponse"].startswith("SKIP"):
                rows.append({"id": item["id"], "skip": "inconnu"})
            else:
                rows.append({"id": item["id"], "new": [
                    {"niveau": 1, "texte": f"Autre porte vers {item['rubrique']}"},
                    {"niveau": 2, "texte": f"Autre fait précis de {item['rubrique']}"}]})
        return json.dumps(rows)
    if "écris TROIS définitions" in prompt or "TROIS définitions" in prompt:
        rows = []
        for item in items_of(prompt):
            rows.append({"id": item["id"], "notoriete": 2, "clues": [
                {"niveau": 1, "texte": f"Entrée directe de {item['rubrique']}"},
                {"niveau": 2, "texte": f"Fait précis de {item['rubrique']}"},
                {"niveau": 3, "texte": f"Allusion fine à {item['rubrique']}"}]})
        return json.dumps(rows)
    if "candidats variés" in prompt:
        count = int(re.search(r"Objectif : (\d+)", prompt).group(1))
        return json.dumps([{"forme": f"Élément {chr(65 + i % 26)}{'x' * (i // 26)}", "indice_wikidata": f"élément {i}"} for i in range(count)])
    return "[]"


def main() -> int:
    sys.stdin.reconfigure(encoding="utf-8")
    prompt = sys.stdin.read()
    if "PANNE" in prompt:
        print(json.dumps({"is_error": True, "result": "panne simulée", "total_cost_usd": 0.0}))
        return 0
    print(json.dumps({"is_error": False, "result": "```json\n" + answer(prompt) + "\n```",
                      "total_cost_usd": COST, "usage": {"input_tokens": len(prompt) // 4, "output_tokens": 50}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
