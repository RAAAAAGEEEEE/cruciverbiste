#!/usr/bin/env python3
"""Assemble les étapes du flux : contrôles mécaniques, résolution à l'aveugle, vérification, bilan.

Sous-commandes (toutes en JSONL, gratuites, sans appel au modèle) :

  solve-input   items.jsonl drafts.jsonl solve_in.jsonl [rejects.jsonl]
      Contrôle mécanique (lint) de chaque définition rédigée ; les valides deviennent des lignes
      pour la résolution à l'aveugle (id « RÉPONSE#niveau#n », sans la réponse dans le texte du prompt).
  verify-input  items.jsonl drafts.jsonl solved.jsonl verify_in.jsonl [--drop-unsolved-level 1]
      Rapproche chaque définition de ce que le résolveur a proposé ; prépare le contrôle factuel.
  fix-input     verify_in.jsonl verified.jsonl recheck_in.jsonl
      Reprend les définitions corrigées par le vérificateur (verdict « fix ») pour les faire revérifier :
      une correction n'a jamais été relue par personne, elle repasse donc par la vérification.
  finalize      items.jsonl drafts.jsonl verified.jsonl accepted.jsonl rejected.jsonl [--mode new|extra]
                [--recheck rechecked.jsonl]
      Applique les verdicts (ok / fix / drop), refait le lint, écrit les entrées acceptées et les rejets.
      Avec --recheck, une correction n'est gardée que si la revérification répond « ok ».

Les formats sont décrits dans docs/ARCHITECTURE.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lint_clues import lint_clue, normalize  # noqa: E402
from run_stage import pattern_of  # noqa: E402


def read_jsonl(path: str | Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: str | Path, rows: list[dict]) -> None:
    with Path(path).open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def clues_of(draft: dict) -> list[dict]:
    """Définitions rédigées d'un brouillon (clé « new » pour draft-extra, « clues » pour draft-new)."""
    return list(draft.get("new") or draft.get("clues") or [])


def existing_texts(item: dict) -> list[str]:
    return [c["text"] for c in item.get("clues", [])]


def clue_id(item_id: str, level: int, n: int) -> str:
    return f"{item_id}#{level}#{n}"


def linted_clues(item: dict, draft: dict, max_len: int) -> tuple[list[dict], list[dict]]:
    """(définitions propres, rejets de lint) d'un brouillon. Les doublons internes comptent aussi."""
    good: list[dict] = []
    bad: list[dict] = []
    seen = existing_texts(item)
    for n, clue in enumerate(clues_of(draft)):
        level = int(clue["level"])
        problems, cleaned = lint_clue(item["answer"], clue["text"], seen, max_len)
        if level not in (1, 2, 3):
            problems.append("niveau hors de 1 à 3")
        if problems:
            bad.append({"id": clue_id(item["id"], level, n), "text": clue["text"], "reason": "; ".join(problems)})
        else:
            good.append({"level": level, "text": cleaned, "n": n})
            seen.append(cleaned)
    return good, bad


def cmd_solve_input(args: argparse.Namespace) -> int:
    items = {row["id"]: row for row in read_jsonl(args.items)}
    rows: list[dict] = []
    rejects: list[dict] = []
    for draft in read_jsonl(args.drafts):
        item = items.get(draft["id"])
        if item is None or "skip" in draft:
            continue
        good, bad = linted_clues(item, draft, args.max_len)
        rejects += bad
        for clue in good:
            rows.append({"id": clue_id(item["id"], clue["level"], clue["n"]), "domain": item["domain"],
                         "pattern": pattern_of(item.get("display"), item["answer"]), "text": clue["text"]})
    write_jsonl(args.output, rows)
    if args.rejects:
        write_jsonl(args.rejects, rejects)
    print(json.dumps({"to_solve": len(rows), "lint_rejects": len(rejects)}, ensure_ascii=False))
    return 0


def solved_guess(guesses: list[str], answer: str) -> bool:
    return answer in {normalize(g).replace(" ", "") for g in list(guesses)[:3]}


def cmd_verify_input(args: argparse.Namespace) -> int:
    items = {row["id"]: row for row in read_jsonl(args.items)}
    solved_rows = {row["id"]: row for row in read_jsonl(args.solved)}
    rows: list[dict] = []
    dropped: list[dict] = []
    for draft in read_jsonl(args.drafts):
        item = items.get(draft["id"])
        if item is None or "skip" in draft:
            continue
        good, _ = linted_clues(item, draft, args.max_len)
        texts = existing_texts(item) + [c["text"] for c in good]
        for clue in good:
            cid = clue_id(item["id"], clue["level"], clue["n"])
            if cid not in solved_rows:
                continue
            if solved_rows[cid].get("for") not in (None, clue["text"]):
                dropped.append({"id": cid, "text": clue["text"], "reason": "résolution périmée : le texte a changé depuis la résolution"})
                continue
            guesses = solved_rows[cid].get("guesses", [])
            if clue["level"] in args.drop_unsolved_level and not solved_guess(guesses, item["answer"]):
                dropped.append({"id": cid, "text": clue["text"], "reason": f"non résolue à l'aveugle (niveau {clue['level']}) : {guesses}"})
                continue
            src = item.get("source") or {}
            row = {"id": cid, "answer": item["answer"], "display": item.get("display") or "", "domain": item["domain"],
                   "level": clue["level"], "text": clue["text"], "others": [t for t in texts if t != clue["text"]],
                   "guesses": guesses}
            if src:
                row["source"] = f"{src.get('qid', '')} : {src.get('description', '')}".strip(" :")
                if src.get("others"):
                    row["source"] += " (homonymes : " + " ; ".join(src["others"]) + ")"
            rows.append(row)
    write_jsonl(args.output, rows)
    if args.dropped:
        write_jsonl(args.dropped, dropped)
    print(json.dumps({"to_verify": len(rows), "dropped_unsolved": len(dropped)}, ensure_ascii=False))
    return 0


def cmd_fix_input(args: argparse.Namespace) -> int:
    originals = {row["id"]: row for row in read_jsonl(args.verify_in)}
    rows: list[dict] = []
    for verdict in read_jsonl(args.verified):
        original = originals.get(verdict["id"])
        if verdict.get("v") != "fix" or not verdict.get("text") or original is None:
            continue
        problems, text = lint_clue(original["answer"], verdict["text"], original["others"], args.max_len)
        if problems:
            continue  # la correction invalide sera rejetée à la finalisation
        rows.append({**original, "text": text, "others": original["others"], "guesses": []})
    write_jsonl(args.output, rows)
    print(json.dumps({"to_recheck": len(rows)}, ensure_ascii=False))
    return 0


def doubtful_cause(cause) -> bool:
    """Une cause de rejet autre que `ambigu` ou `autre` (absente comprise) est un doute factuel."""
    return str(cause or "").strip().lower() not in ("ambigu", "autre")


def cmd_finalize(args: argparse.Namespace) -> int:
    items = {row["id"]: row for row in read_jsonl(args.items)}
    verdicts = {row["id"]: row for row in read_jsonl(args.verified)}
    rechecks = {row["id"]: row for row in read_jsonl(args.recheck)} if args.recheck else None
    accepted: list[dict] = []
    rejected: list[dict] = []
    for draft in read_jsonl(args.drafts):
        item = items.get(draft["id"])
        if item is None:
            continue
        if "skip" in draft:
            rejected.append({"id": item["id"], "reason": f"renoncé par le rédacteur : {draft['skip']}"})
            continue
        good, bad = linted_clues(item, draft, args.max_len)
        rejected += [{"id": b["id"], "reason": "lint : " + b["reason"], "text": b["text"]} for b in bad]
        kept: list[dict] = []
        factual_doubt = False
        for clue in good:
            cid = clue_id(item["id"], clue["level"], clue["n"])
            verdict = verdicts.get(cid)
            if verdict is None:
                rejected.append({"id": cid, "reason": "non vérifiée (résolution ou vérification absente)", "text": clue["text"]})
                continue
            if verdict.get("for") not in (None, clue["text"]):
                rejected.append({"id": cid, "reason": "verdict périmé : le texte a changé depuis la vérification", "text": clue["text"]})
                continue
            if verdict.get("v") == "drop":
                rejected.append({"id": cid, "reason": f"vérificateur : {verdict.get('why', '')}", "cause": verdict.get("cause", ""), "text": clue["text"]})
                factual_doubt = factual_doubt or doubtful_cause(verdict.get("cause"))
                continue
            if verdict.get("v") not in ("ok", "fix") or (verdict.get("v") == "fix" and not verdict.get("text")):
                rejected.append({"id": cid, "reason": f"verdict inconnu ou incomplet : {verdict.get('v')!r}", "text": clue["text"]})
                factual_doubt = True
                continue
            text = clue["text"]
            if verdict.get("v") == "fix" and str(verdict.get("cause") or "").strip().lower() == "fait":
                factual_doubt = True
            if verdict.get("v") == "fix" and verdict.get("text"):
                again = rechecks.get(cid, {}) if rechecks is not None else {}
                if rechecks is not None and (again.get("v") != "ok" or again.get("for") not in (None, verdict["text"], lint_clue(item["answer"], verdict["text"], [], args.max_len)[1])):
                    if again.get("v") == "drop" and doubtful_cause(again.get("cause")) or again.get("v") not in (None, "ok", "fix", "drop") \
                            or again.get("v") == "fix" and str(again.get("cause") or "").strip().lower() == "fait":
                        factual_doubt = True
                    rejected.append({"id": cid, "reason": "correction non confirmée à la revérification : " + str(again.get("why") or again.get("v") or "absente"),
                                     "text": verdict["text"]})
                    continue
                problems, text = lint_clue(item["answer"], verdict["text"], [c["text"] for c in kept] + existing_texts(item), args.max_len)
                if problems:
                    rejected.append({"id": cid, "reason": "correction invalide : " + "; ".join(problems), "text": verdict["text"]})
                    continue
            kept.append({"level": clue["level"], "text": text})
        if args.mode == "new" and factual_doubt and not args.keep_on_doubt:
            rejected.append({"id": item["id"], "reason": "doute factuel sur une définition : mot retiré"})
            continue
        if len(kept) < args.min_clues:
            rejected.append({"id": item["id"], "reason": f"moins de {args.min_clues} définition(s) retenue(s)"})
            continue
        if args.mode == "new" and all(c["level"] == 3 for c in kept):
            rejected.append({"id": item["id"], "reason": "aucune définition de niveau 1 ou 2"})
            continue
        kept.sort(key=lambda c: c["level"])
        out = {"id": item["id"], "answer": item["answer"], "display": item.get("display") or "",
               "domain": item["domain"], "clues": kept}
        if "familiarity" in draft:
            out["familiarity"] = draft["familiarity"]
        if item.get("source"):
            out["source"] = item["source"]
        accepted.append(out)
    write_jsonl(args.accepted, accepted)
    write_jsonl(args.rejected, rejected)
    print(json.dumps({"accepted": len(accepted), "rejected_lines": len(rejected)}, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("solve-input")
    p.add_argument("items"); p.add_argument("drafts"); p.add_argument("output"); p.add_argument("rejects", nargs="?")
    p.add_argument("--max-len", type=int, default=80)
    p.set_defaults(func=cmd_solve_input)

    p = sub.add_parser("verify-input")
    p.add_argument("items"); p.add_argument("drafts"); p.add_argument("solved"); p.add_argument("output")
    p.add_argument("--dropped", help="JSONL des définitions écartées faute de résolution")
    p.add_argument("--drop-unsolved-level", type=int, nargs="*", default=[1],
                   help="niveaux écartés d'office si le résolveur ne trouve pas la réponse (défaut : 1)")
    p.add_argument("--max-len", type=int, default=80)
    p.set_defaults(func=cmd_verify_input)

    p = sub.add_parser("fix-input")
    p.add_argument("verify_in"); p.add_argument("verified"); p.add_argument("output")
    p.add_argument("--max-len", type=int, default=80)
    p.set_defaults(func=cmd_fix_input)

    p = sub.add_parser("finalize")
    p.add_argument("--recheck", help="JSONL des verdicts de revérification des corrections")
    p.add_argument("items"); p.add_argument("drafts"); p.add_argument("verified")
    p.add_argument("accepted"); p.add_argument("rejected")
    p.add_argument("--mode", choices=["new", "extra"], default="new")
    p.add_argument("--min-clues", type=int, default=None, help="définitions minimales (défaut : 2 en mode new, 1 en extra)")
    p.add_argument("--keep-on-doubt", action="store_true", help="mode new : garder le mot même si un fait est douteux")
    p.add_argument("--max-len", type=int, default=80)
    p.set_defaults(func=cmd_finalize)

    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.command == "finalize" and args.min_clues is None:
        args.min_clues = 2 if args.mode == "new" else 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
