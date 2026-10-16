#!/usr/bin/env python3
"""Recherche d'une fiche Wikidata (identifiant, libellé, description) pour un terme.

Wikidata publie ses données en CC0 (https://www.wikidata.org/wiki/Wikidata:Licensing). Ce module
n'envoie à Wikidata que le terme cherché (un nom d'élément du thème), jamais de définition ni de clé.
Les résultats sont gardés dans un cache JSON pour ne pas rappeler l'API.

Usage en module :
    from wikidata import lookup
    fiche = lookup("Naruto Uzumaki", lang="fr", cache=Path("wd_cache.json"))
    # {"qid": "Q...", "label": "...", "description": "...", "exact": True} ou None
"""
from __future__ import annotations

import json
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://www.wikidata.org/w/api.php"
USER_AGENT = "cruciverbiste-skill/0.1 (https://github.com/RAAAAAGEEEEE/cruciverbiste)"
MIN_DELAY = 0.25  # secondes entre deux appels réseau


def fold(text: str) -> str:
    """Majuscules A-Z sans accents ni séparateurs, pour comparer des graphies."""
    decomposed = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(c for c in decomposed if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]+", "", ascii_text.upper())


def _search(term: str, lang: str) -> list[dict]:
    query = urllib.parse.urlencode({
        "action": "wbsearchentities", "search": term, "language": lang, "uselang": lang,
        "type": "item", "limit": 5, "format": "json"})
    request = urllib.request.Request(f"{API}?{query}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response).get("search", [])


def _pick(hits: list[dict], wanted: str) -> dict | None:
    """Première fiche dont le libellé ou l'alias concorde avec la graphie voulue, sinon la première."""
    for hit in hits:
        names = [hit.get("label", ""), (hit.get("match") or {}).get("text", "")]
        if any(fold(name) == wanted for name in names if name):
            return {**hit, "exact": True}
    return {**hits[0], "exact": False} if hits else None


def lookup(term: str, *, lang: str = "fr", cache: Path | None = None, search=_search) -> dict | None:
    """Fiche Wikidata de `term`, ou None. `search` est injectable pour les tests."""
    store: dict = {}
    key = f"{lang}|{term}"
    if cache and cache.exists():
        store = json.loads(cache.read_text(encoding="utf-8"))
        if key in store:
            return store[key]
    wanted = fold(term)
    hit = _pick(search(term, lang), wanted)
    if hit and not hit.get("description") and lang != "en":
        english = _pick(search(term, "en"), wanted)
        if english and english.get("id") == hit.get("id"):
            hit["description"] = english.get("description", "")
    result = None
    if hit:
        result = {"qid": hit.get("id", ""), "label": hit.get("label", ""),
                  "description": hit.get("description", ""), "exact": bool(hit.get("exact"))}
    if cache:
        store[key] = result
        cache.write_text(json.dumps(store, ensure_ascii=False, indent=1), encoding="utf-8")
    return result


def polite_lookup(term: str, **kwargs) -> dict | None:
    """`lookup` avec une pause entre appels et un seul nouvel essai en cas d'erreur réseau."""
    for attempt in range(2):
        try:
            time.sleep(MIN_DELAY)
            return lookup(term, **kwargs)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            time.sleep(3 * (attempt + 1))
    return None
