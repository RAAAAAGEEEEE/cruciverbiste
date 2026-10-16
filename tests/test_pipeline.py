"""Test de bout en bout du flux avec un faux CLI `claude` (aucun réseau, aucune clé, aucun coût réel)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FAKE = Path(__file__).resolve().parent / "fake_claude.py"
sys.path.insert(0, str(SCRIPTS))

import llm  # noqa: E402
from ledger_report import summarize  # noqa: E402


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.env = {**os.environ, "PYTHONIOENCODING": "utf-8", "ANTHROPIC_API_KEY": "cle-factice-de-test",
                    "CRUCIVERBISTE_CLAUDE_CMD": f"{Path(sys.executable).as_posix()} {FAKE.as_posix()}"}
        self.ledger = self.dir / "ledger.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self, name: str, *args: str, ok: bool = True) -> str:
        done = subprocess.run([sys.executable, str(SCRIPTS / name), *args], capture_output=True, text=True,
                              encoding="utf-8", env=self.env, cwd=self.dir)
        if ok:
            self.assertEqual(done.returncode, 0, done.stderr + done.stdout)
        return done.stdout

    def stage(self, stage: str, src: Path, out: Path, *extra: str, cap: str = "5", ok: bool = True) -> dict:
        text = self.run_script("run_stage.py", stage, str(src), str(out), "--ledger", str(self.ledger),
                               "--cap", cap, "--workers", "2", *extra, ok=ok)
        return json.loads(text.strip().splitlines()[-1])

    def test_extra_flow_end_to_end(self):
        items = [
            {"id": "ZELDA", "answer": "ZELDA", "display": "", "domain": "jeux", "clues": [{"level": 1, "text": "Princesse d'Hyrule"}]},
            {"id": "SKIPME", "answer": "SKIPME", "display": "", "domain": "jeux", "clues": []},
            {"id": "MARIO", "answer": "MARIO", "display": "", "domain": "jeux", "clues": []},
        ]
        write_jsonl(self.dir / "items.jsonl", items)
        stats = self.stage("draft-extra", self.dir / "items.jsonl", self.dir / "drafts.jsonl", "--batch", "2")
        self.assertEqual(stats["written"], 3)
        self.run_script("combine.py", "solve-input", "items.jsonl", "drafts.jsonl", "solve_in.jsonl", "lint_rejects.jsonl")
        self.assertEqual(len(read_jsonl(self.dir / "solve_in.jsonl")), 4)
        self.stage("solve", self.dir / "solve_in.jsonl", self.dir / "solved.jsonl")
        self.run_script("combine.py", "verify-input", "items.jsonl", "drafts.jsonl", "solved.jsonl", "verify_in.jsonl")
        self.assertEqual(len(read_jsonl(self.dir / "verify_in.jsonl")), 4)
        self.stage("verify", self.dir / "verify_in.jsonl", self.dir / "verified.jsonl")
        self.run_script("combine.py", "finalize", "items.jsonl", "drafts.jsonl", "verified.jsonl",
                        "accepted.jsonl", "rejected.jsonl", "--mode", "extra")
        accepted = {row["id"]: row for row in read_jsonl(self.dir / "accepted.jsonl")}
        self.assertEqual(sorted(accepted), ["MARIO", "ZELDA"])
        self.assertEqual([c["level"] for c in accepted["ZELDA"]["clues"]], [1, 2])
        rejected = read_jsonl(self.dir / "rejected.jsonl")
        self.assertTrue(any(r["id"] == "SKIPME" for r in rejected))
        summary = summarize(self.ledger)
        self.assertGreater(summary["total"], 0)
        self.assertEqual(set(summary["by_stage"]), {"draft-extra", "solve", "verify"})

    def test_new_flow_drops_word_on_factual_doubt_but_not_on_ambiguity(self):
        items = [{"id": "ALPHA", "answer": "ALPHA", "display": "", "domain": "d", "source": {"qid": "Q1", "description": "x"}},
                 {"id": "BRAVO", "answer": "BRAVO", "display": "", "domain": "d"},
                 {"id": "DELTA", "answer": "DELTA", "display": "", "domain": "d"}]
        write_jsonl(self.dir / "items.jsonl", items)
        drafts = [
            {"id": "ALPHA", "familiarity": 1, "clues": [{"level": 1, "text": "Porte nette"}, {"level": 2, "text": "Fait FAUX ici"}, {"level": 3, "text": "Allusion fine"}]},
            {"id": "BRAVO", "familiarity": 2, "clues": [{"level": 1, "text": "Porte nette"}, {"level": 2, "text": "Moyen AMBIGU ici"}, {"level": 3, "text": "Mur CORRIGER"}]},
            {"id": "DELTA", "familiarity": 3, "clues": [{"level": 1, "text": "Avec DELTA dedans"}, {"level": 2, "text": "Fait précis"}, {"level": 3, "text": "Allusion INSOLUBLE"}]},
        ]
        write_jsonl(self.dir / "drafts.jsonl", drafts)
        self.run_script("combine.py", "solve-input", "items.jsonl", "drafts.jsonl", "solve_in.jsonl", "lint_rejects.jsonl")
        self.assertTrue(any("contient la réponse" in r["reason"] for r in read_jsonl(self.dir / "lint_rejects.jsonl")))
        self.stage("solve", self.dir / "solve_in.jsonl", self.dir / "solved.jsonl")
        self.run_script("combine.py", "verify-input", "items.jsonl", "drafts.jsonl", "solved.jsonl", "verify_in.jsonl")
        self.stage("verify", self.dir / "verify_in.jsonl", self.dir / "verified.jsonl")
        self.run_script("combine.py", "finalize", "items.jsonl", "drafts.jsonl", "verified.jsonl", "accepted.jsonl", "rejected.jsonl")
        accepted = {row["id"]: row for row in read_jsonl(self.dir / "accepted.jsonl")}
        self.assertNotIn("ALPHA", accepted, "doute factuel : mot retiré")
        self.assertIn("BRAVO", accepted, "ambiguïté : seule la définition tombe")
        self.assertEqual(len(accepted["BRAVO"]["clues"]), 2)
        self.assertEqual(accepted["BRAVO"]["clues"][1]["text"], "Version corrigée sans défaut")
        self.assertEqual([c["level"] for c in accepted["DELTA"]["clues"]], [2, 3], "la porte qui contient la réponse est écartée")

    def test_corrections_are_rechecked(self):
        items = [{"id": "ECHO", "answer": "ECHO", "display": "", "domain": "d", "clues": []}]
        write_jsonl(self.dir / "items.jsonl", items)
        write_jsonl(self.dir / "drafts.jsonl", [{"id": "ECHO", "new": [
            {"level": 1, "text": "Porte CORRIGER"}, {"level": 2, "text": "Moyen précis"}]}])
        self.run_script("combine.py", "solve-input", "items.jsonl", "drafts.jsonl", "solve_in.jsonl")
        self.stage("solve", self.dir / "solve_in.jsonl", self.dir / "solved.jsonl")
        self.run_script("combine.py", "verify-input", "items.jsonl", "drafts.jsonl", "solved.jsonl", "verify_in.jsonl")
        self.stage("verify", self.dir / "verify_in.jsonl", self.dir / "verified.jsonl")
        out = json.loads(self.run_script("combine.py", "fix-input", "verify_in.jsonl", "verified.jsonl", "recheck_in.jsonl").strip())
        self.assertEqual(out["to_recheck"], 1)
        self.stage("verify", self.dir / "recheck_in.jsonl", self.dir / "rechecked.jsonl")
        self.run_script("combine.py", "finalize", "items.jsonl", "drafts.jsonl", "verified.jsonl", "accepted.jsonl",
                        "rejected.jsonl", "--mode", "extra", "--recheck", "rechecked.jsonl")
        accepted = read_jsonl(self.dir / "accepted.jsonl")
        self.assertEqual([c["text"] for c in accepted[0]["clues"]], ["Version corrigée sans défaut", "Moyen précis"])
        # sans verdict « ok » à la revérification, la correction tombe
        write_jsonl(self.dir / "rechecked.jsonl", [{"id": "ECHO#1#0", "v": "drop", "why": "douteuse"}])
        self.run_script("combine.py", "finalize", "items.jsonl", "drafts.jsonl", "verified.jsonl", "accepted.jsonl",
                        "rejected.jsonl", "--mode", "extra", "--recheck", "rechecked.jsonl")
        accepted = read_jsonl(self.dir / "accepted.jsonl")
        self.assertEqual([c["text"] for c in accepted[0]["clues"]], ["Moyen précis"])

    def test_unexpected_verdicts_are_rejected(self):
        items = [{"id": "FOXTROT", "answer": "FOXTROT", "display": "", "domain": "d", "clues": []}]
        write_jsonl(self.dir / "items.jsonl", items)
        write_jsonl(self.dir / "drafts.jsonl", [{"id": "FOXTROT", "familiarity": 1, "clues": [
            {"level": 1, "text": "Porte nette"}, {"level": 2, "text": "Moyen précis"}, {"level": 3, "text": "Allusion fine"}]}])
        write_jsonl(self.dir / "verified.jsonl", [
            {"id": "FOXTROT#1#0", "v": "ok"}, {"id": "FOXTROT#2#0", "v": "doute"}, {"id": "FOXTROT#3#0", "v": "fix"}])
        self.run_script("combine.py", "finalize", "items.jsonl", "drafts.jsonl", "verified.jsonl", "accepted.jsonl", "rejected.jsonl")
        self.assertEqual(read_jsonl(self.dir / "accepted.jsonl"), [], "verdict inconnu ou « fix » sans texte : mot retiré")
        self.run_script("combine.py", "finalize", "items.jsonl", "drafts.jsonl", "verified.jsonl", "accepted.jsonl", "rejected.jsonl", "--mode", "extra")
        kept = read_jsonl(self.dir / "accepted.jsonl")
        self.assertEqual([c["text"] for c in kept[0]["clues"]], ["Porte nette"])

    def test_resume_only_processes_missing_items(self):
        items = [{"id": f"MOT{i}", "answer": f"MOT{i}", "display": "", "domain": "d", "clues": []} for i in range(4)]
        write_jsonl(self.dir / "items.jsonl", items)
        self.stage("draft-extra", self.dir / "items.jsonl", self.dir / "drafts.jsonl", "--limit", "2", "--batch", "1")
        spent_first = summarize(self.ledger)["calls"]
        self.stage("draft-extra", self.dir / "items.jsonl", self.dir / "drafts.jsonl", "--batch", "1")
        self.assertEqual(len(read_jsonl(self.dir / "drafts.jsonl")), 4)
        self.assertEqual(summarize(self.ledger)["calls"], spent_first + 2)

    def test_budget_cap_stops_before_spending(self):
        items = [{"id": f"MOT{i}", "answer": f"MOT{i}", "display": "", "domain": "d", "clues": []} for i in range(10)]
        write_jsonl(self.dir / "items.jsonl", items)
        done = subprocess.run([sys.executable, str(SCRIPTS / "run_stage.py"), "draft-extra", str(self.dir / "items.jsonl"),
                               str(self.dir / "drafts.jsonl"), "--ledger", str(self.ledger), "--cap", "0.025",
                               "--workers", "1", "--batch", "1"], capture_output=True, text=True, encoding="utf-8", env=self.env)
        self.assertEqual(done.returncode, 1)
        self.assertIn("plafond", done.stdout)
        self.assertLessEqual(summarize(self.ledger)["total"], 0.03)

    def test_candidates_stage_writes_domain(self):
        done = subprocess.run([sys.executable, str(SCRIPTS / "run_stage.py"), "candidates", str(self.dir / "cand.jsonl"),
                               "--ledger", str(self.ledger), "--cap", "1", "--theme", "Astronomie", "--domain", "sciences",
                               "--count", "5"], capture_output=True, text=True, encoding="utf-8", env=self.env)
        self.assertEqual(done.returncode, 0, done.stderr)
        rows = read_jsonl(self.dir / "cand.jsonl")
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[0]["domain"], "sciences")

    def test_llm_errors_are_retried_then_raised(self):
        with self.assertRaises(llm.LlmError):
            old = os.environ.copy()
            os.environ.update(self.env)
            try:
                llm.ask("PANNE", "claude-sonnet-5-5", ledger=self.ledger, cap=5, retries=0)
            finally:
                os.environ.clear()
                os.environ.update(old)

    def test_missing_binary_is_an_llm_error_not_a_crash(self):
        old = os.environ.copy()
        os.environ.update({"ANTHROPIC_API_KEY": "test", "CRUCIVERBISTE_CLAUDE_CMD": "commande-qui-n-existe-pas"})
        try:
            with self.assertRaises(llm.LlmError):
                llm.ask("x", "claude-sonnet-5-5", ledger=self.ledger, cap=5, retries=0)
        finally:
            os.environ.clear()
            os.environ.update(old)

    def test_missing_key_is_refused(self):
        old = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            with self.assertRaises(llm.LlmError):
                llm.ask("x", "claude-sonnet-5-5", ledger=self.ledger, cap=5)
        finally:
            if old is not None:
                os.environ["ANTHROPIC_API_KEY"] = old

    def test_extract_json_tolerates_fences(self):
        self.assertEqual(llm.extract_json("```json\n[{\"a\": 1}]\n```"), [{"a": 1}])
        with self.assertRaises(ValueError):
            llm.extract_json("aucun json")

    def test_extract_json_ignores_trailing_text_and_second_array(self):
        self.assertEqual(llm.extract_json('[{"a": 1}]' + chr(10) + 'Note : [voir ci-dessus]'), [{"a": 1}])
        self.assertEqual(llm.extract_json('Voici :' + chr(10) + '[{"a": 1}]' + chr(10) + '[{"b": 2}]'), [{"a": 1}])


if __name__ == "__main__":
    unittest.main()
