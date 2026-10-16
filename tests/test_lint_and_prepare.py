"""Tests des contrôles mécaniques, de la préparation des candidats et de la fiche Wikidata (sans réseau)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lint_clues import clean, leaks_answer, lint_clue, normalize, similarity  # noqa: E402
from prepare_items import answer_of, display_of, prepare, variants  # noqa: E402
from run_stage import item_line, pattern_of  # noqa: E402
from wikidata import fold, lookup  # noqa: E402


class LintTests(unittest.TestCase):
    def test_normalize_strips_accents(self):
        self.assertEqual(normalize("Épée d'Hyrule"), "EPEE D HYRULE")

    def test_leak_detects_answer_and_family(self):
        self.assertTrue(leaks_answer("ZELDA", "La princesse Zelda"))
        self.assertTrue(leaks_answer("PIRATE", "Il pirate des comptes"))
        self.assertFalse(leaks_answer("ZELDA", "Princesse d'Hyrule"))

    def test_leak_detects_glued_answer(self):
        self.assertTrue(leaks_answer("LINK", "Hyperlink cassé"))

    def test_clean_fixes_apostrophes_and_final_period(self):
        self.assertEqual(clean("  L’épée  du héros. "), "L'épée du héros")

    def test_clue_too_long_is_flagged(self):
        problems, _ = lint_clue("ZELDA", "x" * 81)
        self.assertTrue(any("trop longue" in p for p in problems))

    def test_em_dash_and_emoji_are_flagged(self):
        problems, _ = lint_clue("ZELDA", "Princesse \u2014 d'Hyrule")
        self.assertTrue(any("tiret long" in p for p in problems))
        problems, _ = lint_clue("ZELDA", "Princesse \U0001F451")
        self.assertTrue(any("emoji" in p for p in problems))

    def test_near_duplicate_is_flagged(self):
        problems, _ = lint_clue("ZELDA", "Princesse du royaume d'Hyrule", existing=["Princesse du royaume d'Hyrule"])
        self.assertTrue(any("identique" in p for p in problems))
        problems, _ = lint_clue("ZELDA", "Princesse royaume Hyrule belle", existing=["Princesse du royaume d'Hyrule"])
        self.assertTrue(any("quasi-doublon" in p for p in problems))

    def test_distinct_clue_passes(self):
        problems, cleaned = lint_clue("ZELDA", "Elle porte la sagesse de la Triforce", existing=["Princesse d'Hyrule"])
        self.assertEqual(problems, [])
        self.assertEqual(cleaned, "Elle porte la sagesse de la Triforce")

    def test_similarity_bounds(self):
        self.assertEqual(similarity("", "abc"), 0.0)
        self.assertEqual(similarity("Roi des pirates", "Roi des pirates"), 1.0)


class PatternTests(unittest.TestCase):
    def test_pattern_single_word(self):
        self.assertEqual(pattern_of(None, "ZELDA"), "5")

    def test_pattern_two_words_and_hyphen(self):
        self.assertEqual(pattern_of("Dark Vador", "DARKVADOR"), "4,5")
        self.assertEqual(pattern_of("Spider-Man", "SPIDERMAN"), "6-3")

    def test_solve_line_hides_the_answer(self):
        line = item_line("solve", {"id": "ZELDA#1#0", "domain": "jeux", "pattern": "5", "text": "Princesse d'Hyrule"})
        self.assertEqual(line, "ZELDA#1#0 | jeux | 5 | Princesse d'Hyrule")


class PrepareTests(unittest.TestCase):
    def test_answer_and_display(self):
        self.assertEqual(answer_of("Spider-Man"), "SPIDERMAN")
        self.assertEqual(display_of("Spider-Man"), "Spider-Man")
        self.assertEqual(display_of("Zelda"), "")
        self.assertEqual(answer_of("L'Épée"), "LEPEE")

    def test_variants_cover_plurals(self):
        self.assertIn("ORC", variants("ORCS"))
        self.assertIn("ORCS", variants("ORC"))

    def test_prepare_filters(self):
        rows = [
            {"form": "Zelda", "hint": "Zelda", "domain": "jeux"},
            {"form": "Orcs", "hint": "Orcs", "domain": "jeux"},        # variante de ORC existant
            {"form": "Ab", "hint": "Ab", "domain": "jeux"},            # trop court
            {"form": "R2-D2", "hint": "R2-D2", "domain": "jeux"},      # chiffres
            {"form": "Zelda", "hint": "Zelda", "domain": "jeux"},      # doublon du lot
            {"form": "Inconnu total", "hint": "x", "domain": "jeux"},  # pas de fiche
        ]

        def resolve(term, context=""):
            return None if term == "Inconnu total" else {"qid": "Q1", "description": "personnage", "exact": True}

        kept, rejected = prepare(rows, {"ORC"}, min_len=3, max_len=13, resolve=resolve)
        self.assertEqual([k["answer"] for k in kept], ["ZELDA"])
        self.assertEqual(kept[0]["source"]["qid"], "Q1")
        reasons = " | ".join(r["reason"] for r in rejected)
        for expected in ("variante", "longueur", "chiffres", "aucune fiche"):
            self.assertIn(expected, reasons)
        self.assertEqual(len(rejected), 5)

    def test_prepare_rejects_approximate_and_unreachable(self):
        rows = [{"form": "Comète de Hal", "domain": "ciel"}, {"form": "Orion", "domain": "ciel"},
                {"form": "Vega", "domain": "ciel"}]
        fiches = {"Comète de Hal": {"qid": "Q1", "exact": False}, "Orion": {"unreachable": True},
                  "Vega": {"qid": "Q2", "exact": True}}
        kept, rejected = prepare(rows, set(), min_len=3, max_len=13, resolve=lambda t, c="": fiches[t])
        self.assertEqual([k["answer"] for k in kept], ["VEGA"])
        reasons = " | ".join(r["reason"] for r in rejected)
        self.assertIn("non concordante", reasons)
        self.assertIn("injoignable", reasons)

    def test_prepare_without_wikidata(self):
        kept, rejected = prepare([{"form": "Zelda", "domain": "jeux"}], set(), min_len=3, max_len=13)
        self.assertEqual(len(kept), 1)
        self.assertNotIn("source", kept[0])


class WikidataTests(unittest.TestCase):
    def test_fold(self):
        self.assertEqual(fold("Épée-Vorpale"), "EPEEVORPALE")

    def test_lookup_prefers_exact_label_and_uses_cache(self):
        calls = []

        def fake_search(term, lang):
            calls.append((term, lang))
            return [{"id": "Q2", "label": "Autre chose", "description": "autre"},
                    {"id": "Q1", "label": "Zelda", "description": "princesse"}]

        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "cache.json"
            first = lookup("Zelda", cache=cache, search=fake_search)
            second = lookup("Zelda", cache=cache, search=fake_search)
        self.assertEqual(first["qid"], "Q1")
        self.assertTrue(first["exact"])
        self.assertEqual(first, second)
        self.assertEqual(len(calls), 1)

    def test_lookup_falls_back_to_english_description(self):
        def fake_search(term, lang):
            return [{"id": "Q1", "label": "Zelda", "description": "" if lang == "fr" else "princess"}]

        self.assertEqual(lookup("Zelda", search=fake_search)["description"], "princess")

    def test_lookup_uses_context_to_choose_between_homonyms(self):
        def fake_search(term, lang):
            return [{"id": "Q1", "label": "Saturne", "description": "chanson de rap sortie en 2016"},
                    {"id": "Q2", "label": "Saturne", "description": "sixième planète du Système solaire"}]

        self.assertEqual(lookup("Saturne", search=fake_search)["qid"], "Q1")  # sans contexte : la première
        self.assertEqual(lookup("Saturne", search=fake_search, context="Saturne planète Astronomie")["qid"], "Q2")
        self.assertEqual(lookup("Saturne", search=fake_search)["others"], ["Q2 : sixième planète du Système solaire"])

    def test_lookup_approximate_hit_is_flagged_not_exact(self):
        hit = lookup("Comète de Hal", search=lambda term, lang: [{"id": "Q9", "label": "Comète de Halley", "description": "comète"}])
        self.assertIs(hit["exact"], False)

    def test_lookup_accepts_alias_as_exact(self):
        hit = lookup("Zed", search=lambda term, lang: [{"id": "Q3", "label": "Zeddy", "description": "x", "match": {"text": "Zed"}}])
        self.assertIs(hit["exact"], True)

    def test_lookup_no_hit(self):
        self.assertIsNone(lookup("Rien", search=lambda term, lang: []))


if __name__ == "__main__":
    unittest.main()
