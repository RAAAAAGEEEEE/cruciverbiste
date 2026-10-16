#!/usr/bin/env python3
"""Une étape du flux de production de définitions, en lots, reprise possible, budget plafonné.

Étapes (voir docs/USAGE.md) :
  candidates  propose des réponses candidates pour un thème
  draft-new   rédige 3 définitions (niveaux 1, 2, 3) pour des candidats
  draft-extra ajoute de nouvelles définitions à des mots existants
  solve       résolution à l'aveugle (rubrique + motif + définition, sans la réponse)
  verify      contrôle factuel et d'unicité par un second modèle

Exemple :
  export ANTHROPIC_API_KEY=...        # jamais écrite dans un fichier du dépôt
  python3 scripts/run_stage.py candidates out.jsonl --theme "Astronomie" --ledger ledger.jsonl --cap 1
  python3 scripts/run_stage.py solve in.jsonl out.jsonl --ledger ledger.jsonl --cap 5 --model claude-sonnet-5-5

Chaque ligne de sortie reprend l'`id` de l'entrée. Relancer la même commande ne traite que les
entrées absentes de la sortie. Le coût de chaque appel est ajouté au registre `--ledger` ; l'étape
s'arrête dès que le total du registre atteint `--cap` dollars.
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
from concurrent.futures import CancelledError, ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm import BudgetExceeded, LlmError, ask, extract_json, spent  # noqa: E402

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"
DEFAULTS = {  # (modèle, taille de lot)
    "candidates": ("claude-sonnet-5-5", 1),
    "draft-new": ("claude-sonnet-5-5", 25),
    "draft-extra": ("claude-sonnet-5-5", 30),
    "solve": ("claude-sonnet-5-5", 60),
    "verify": ("claude-opus-5-5", 25),
}


def pattern_of(display: str | None, answer: str) -> str:
    """Motif de longueur d'une réponse : « 4,5 » pour deux mots, « 6-3 » pour un trait d'union."""
    if not display or not any(sep in display for sep in " -"):
        return str(len(answer))
    parts = []
    for chunk in display.replace("'", "").split():
        parts.append("-".join(str(sum(c.isalpha() for c in piece)) for piece in chunk.split("-")))
    return ",".join(parts)


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def render(template: str, **values: str) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def read_prompt(name: str) -> str:
    return (PROMPTS / f"{name}.md").read_text(encoding="utf-8")


def read_rules(path: str | None) -> str:
    """Règles de rédaction : le fichier donné, sinon prompts/rules.md (français)."""
    return Path(path).read_text(encoding="utf-8") if path else read_prompt("rules")


def item_line(stage: str, item: dict) -> str:
    """Représentation compacte (JSON, clés en français) d'une entrée pour le prompt."""
    if stage == "solve":  # le résolveur ne voit jamais la réponse
        return f"{item['id']} | {item['domain']} | {item['pattern']} | {item['text']}"
    answer = item["answer"]
    display = item.get("display") or answer
    base = {"id": item["id"], "reponse": answer, "forme": display, "longueur": len(answer),
            "rubrique": item["domain"]}
    if stage == "draft-extra":
        base["existantes"] = [{"niveau": c["level"], "texte": c["text"]} for c in item.get("clues", [])]
    elif stage == "draft-new":
        source = item.get("source", {})
        base["fiche"] = f"{source.get('qid', '')} : {source.get('description', '')}".strip(" :")
        if source.get("others"):
            base["homonymes"] = source["others"]
    elif stage == "verify":
        base["niveau"] = item["level"]
        base["texte"] = item["text"]
        base["autres"] = item.get("others", [])
        base["resolveur"] = item.get("guesses", [])
        if item.get("source"):
            base["fiche"] = item["source"]
    return json.dumps(base, ensure_ascii=False)


def parse_item(stage: str, raw: dict, item: dict) -> dict:
    """Normalise la réponse du modèle pour une entrée (clés anglaises, niveaux entiers)."""
    out: dict = {"id": item["id"]}
    if "skip" in raw:
        out["skip"] = str(raw["skip"])
        return out
    if stage == "draft-extra":
        out["new"] = [{"level": int(c["niveau"]), "text": str(c["texte"])} for c in raw.get("new", [])]
    elif stage == "draft-new":
        out["familiarity"] = int(raw.get("notoriete", 2))
        out["clues"] = [{"level": int(c["niveau"]), "text": str(c["texte"])} for c in raw.get("clues", [])]
    elif stage == "solve":
        out["for"] = item.get("text")
        out["guesses"] = [str(g) for g in raw.get("reponses", [])]
    elif stage == "verify":
        out["for"] = item.get("text")
        out["v"] = str(raw.get("v", "drop")).strip().lower()
        if raw.get("texte"):
            out["text"] = str(raw["texte"])
        if raw.get("pourquoi"):
            out["why"] = str(raw["pourquoi"])
        if raw.get("cause"):
            out["cause"] = str(raw["cause"]).strip().lower()
    return out


def run(stage: str, items: list[dict], out_path: Path, *, model: str, batch: int, workers: int,
        ledger: Path, cap: float, constraints: str, levels: str, effort: str | None,
        language: str = "français", rules_path: str | None = None) -> dict:
    done = {row["id"] for row in load_jsonl(out_path)}
    todo = [item for item in items if item["id"] not in done]
    template = read_prompt({"draft-extra": "draft_extra", "draft-new": "draft_new",
                            "solve": "blind_solve", "verify": "fact_check"}[stage])
    rules = read_rules(rules_path)
    groups = [todo[i:i + batch] for i in range(0, len(todo), batch)]
    lock = threading.Lock()
    stats = {"items": len(todo), "written": 0, "failed_batches": 0, "stopped": ""}

    def work(group: list[dict]) -> None:
        prompt = render(template, rules=rules, constraints=constraints, levels=levels, language=language,
                        items="\n".join(item_line(stage, it) for it in group))
        text = ask(prompt, model, ledger=ledger, cap=cap, stage=stage, effort=effort)
        data = extract_json(text)
        if not isinstance(data, list):
            raise ValueError("la réponse n'est pas un tableau JSON")
        by_id = {str(row.get("id")): row for row in data if isinstance(row, dict)}
        rows = [parse_item(stage, by_id[it["id"]], it) for it in group if it["id"] in by_id]
        with lock, out_path.open("a", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            stats["written"] += len(rows)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(work, g) for g in groups]
        for future in as_completed(futures):
            try:
                future.result()
            except CancelledError:
                continue
            except BudgetExceeded as exc:
                stats["stopped"] = str(exc)
                for other in futures:
                    other.cancel()
            except (LlmError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
                stats["failed_batches"] += 1
                print(f"lot en échec : {exc}", file=sys.stderr)
    stats["spent_total"] = round(spent(ledger), 4)
    return stats


def candidates(args: argparse.Namespace) -> dict:
    prompt = render(read_prompt("candidates"), theme=args.theme, count=str(args.count),
                    min_len=str(args.min_len), max_len=str(args.max_len), language=args.language,
                    avoid=args.avoid or "aucune liste", constraints=args.constraints_text)
    text = ask(prompt, args.model or DEFAULTS["candidates"][0], ledger=Path(args.ledger), cap=args.cap,
               stage="candidates", effort=args.effort)
    rows = [row for row in extract_json(text) if isinstance(row, dict) and row.get("forme")]
    with Path(args.output).open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps({"theme": args.theme, "domain": args.domain or args.theme, "form": row["forme"],
                                     "hint": row.get("indice_wikidata", row["forme"])}, ensure_ascii=False) + "\n")
    return {"items": len(rows), "spent_total": round(spent(Path(args.ledger)), 4)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("stage", choices=sorted(DEFAULTS))
    parser.add_argument("input", nargs="?", help="JSONL d'entrées (inutile pour candidates)")
    parser.add_argument("output", nargs="?", help="JSONL de sortie (complété à chaque lot)")
    parser.add_argument("--ledger", required=True, help="registre JSONL des coûts")
    parser.add_argument("--cap", type=float, required=True, help="plafond cumulé en dollars")
    parser.add_argument("--model")
    parser.add_argument("--batch", type=int)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"])
    parser.add_argument("--levels", default="1, 2", help="niveaux à écrire (draft-extra)")
    parser.add_argument("--constraints", help="fichier texte de consignes propres au projet")
    parser.add_argument("--language", default="français", help="langue des définitions (défaut : français)")
    parser.add_argument("--rules", help="fichier de règles de rédaction (défaut : prompts/rules.md)")
    parser.add_argument("--limit", type=int, help="ne traiter que les N premières entrées (lot test)")
    parser.add_argument("--theme")
    parser.add_argument("--domain", help="rubrique à inscrire sur les candidats (défaut : le thème)")
    parser.add_argument("--count", type=int, default=60)
    parser.add_argument("--min-len", type=int, default=3)
    parser.add_argument("--max-len", type=int, default=13)
    parser.add_argument("--avoid", default="")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    args.constraints_text = Path(args.constraints).read_text(encoding="utf-8") if args.constraints else ""
    if args.stage == "candidates":
        args.output = args.output or args.input  # candidates n'a pas d'entrée : le seul chemin donné est la sortie
        if not args.output:
            parser.error("candidates demande un fichier de sortie")
        if not args.theme:
            parser.error("candidates demande --theme")
        try:
            stats = candidates(args)
        except (LlmError, BudgetExceeded, ValueError) as exc:
            print(f"échec : {exc}", file=sys.stderr)
            return 1
    else:
        if not args.input or not args.output:
            parser.error("l'étape demande un fichier d'entrées et un fichier de sortie")
        items = load_jsonl(Path(args.input))
        if args.limit:
            items = items[: args.limit]
        model, batch = DEFAULTS[args.stage]
        stats = run(args.stage, items, Path(args.output), model=args.model or model,
                    batch=args.batch or batch, workers=args.workers, ledger=Path(args.ledger),
                    cap=args.cap, constraints=args.constraints_text, levels=args.levels, effort=args.effort,
                    language=args.language, rules_path=args.rules)
    print(json.dumps(stats, ensure_ascii=False))
    return 1 if stats.get("stopped") else 0


if __name__ == "__main__":
    sys.exit(main())
