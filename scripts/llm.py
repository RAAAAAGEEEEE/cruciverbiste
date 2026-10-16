#!/usr/bin/env python3
"""Appel d'un modèle Claude via `claude -p --bare` avec budget en dollars.

Chaque appel :
- utilise uniquement la clé de la variable d'environnement ANTHROPIC_API_KEY (mode --bare : ni
  abonnement, ni CLAUDE.md, ni hooks, ni outils) ;
- écrit une ligne dans un registre JSONL (modèle, jetons, coût `total_cost_usd`) ;
- refuse de partir si le total déjà dépensé atteint le plafond.

La clé n'est jamais lue, affichée ni écrite par ce module.
"""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import threading
import time
from pathlib import Path

_LOCK = threading.Lock()


def claude_command() -> list[str]:
    """Commande du CLI : `claude` par défaut ; CRUCIVERBISTE_CLAUDE_CMD la remplace (tests, binaire hors PATH)."""
    return shlex.split(os.environ.get("CRUCIVERBISTE_CLAUDE_CMD", "claude"))


class BudgetExceeded(RuntimeError):
    """Le plafond de dépense est atteint : on s'arrête avant l'appel."""


class LlmError(RuntimeError):
    """L'appel au modèle a échoué après les nouvelles tentatives."""


def spent(ledger: Path) -> float:
    """Total dépensé (en dollars) d'après le registre."""
    if not ledger.exists():
        return 0.0
    total = 0.0
    with ledger.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                total += float(json.loads(line).get("cost", 0.0))
    return total


def ask(prompt: str, model: str, *, ledger: Path, cap: float, stage: str = "",
        system: str | None = None, effort: str | None = None,
        timeout: int = 900, retries: int = 2) -> str:
    """Envoie `prompt` à `model` et renvoie le texte de la réponse."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise LlmError("ANTHROPIC_API_KEY absente de l'environnement")
    cmd = claude_command() + ["-p", "--bare", "--model", model, "--tools", "",
           "--no-session-persistence", "--output-format", "json"]
    if system:
        cmd += ["--system-prompt", system]
    if effort:
        cmd += ["--effort", effort]
    last_error = ""
    for attempt in range(retries + 1):
        with _LOCK:
            if spent(ledger) >= cap:
                raise BudgetExceeded(f"plafond de {cap:.2f} $ atteint ({spent(ledger):.2f} $ dépensés)")
        try:
            done = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                                  encoding="utf-8", timeout=timeout)
        except subprocess.TimeoutExpired:
            last_error = "délai dépassé"
            time.sleep(5 * (attempt + 1))
            continue
        try:
            data = json.loads(done.stdout)
        except json.JSONDecodeError:
            last_error = f"sortie illisible (code {done.returncode})"
            time.sleep(5 * (attempt + 1))
            continue
        cost = float(data.get("total_cost_usd", 0.0))
        usage = data.get("usage", {})
        with _LOCK, ledger.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "ts": int(time.time()), "stage": stage, "model": model, "cost": cost,
                "in": usage.get("input_tokens", 0), "out": usage.get("output_tokens", 0),
                "error": bool(data.get("is_error")),
            }) + "\n")
        if data.get("is_error"):
            last_error = str(data.get("result", ""))[:200]
            time.sleep(5 * (attempt + 1))
            continue
        return str(data.get("result", ""))
    raise LlmError(last_error or "échec inconnu")


def extract_json(text: str):
    """Premier tableau ou objet JSON d'une réponse (tolère les blocs ```json)."""
    start_candidates = [i for i in (text.find("["), text.find("{")) if i >= 0]
    if not start_candidates:
        raise ValueError("pas de JSON dans la réponse")
    start = min(start_candidates)
    closer = "]" if text[start] == "[" else "}"
    end = text.rfind(closer)
    if end < start:
        raise ValueError("JSON non fermé")
    return json.loads(text[start:end + 1])
