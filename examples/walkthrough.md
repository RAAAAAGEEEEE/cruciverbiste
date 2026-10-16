# Déroulé complet (exemple)

Voir aussi : [../docs/USAGE.md](../docs/USAGE.md), [sample_report.md](sample_report.md), [sample_entries.jsonl](sample_entries.jsonl), [sample_accepted.jsonl](sample_accepted.jsonl).

Ce déroulé a deux parties, étiquetées :

- **Exécuté** : les commandes ci-dessous ont été lancées le 16/10/2026 avec le faux CLI des tests (`CRUCIVERBISTE_CLAUDE_CMD`, aucune clé réelle, aucun réseau). Les sorties de comptage sont réelles ; les textes de définition produits par le faux CLI sont des gabarits sans intérêt.
- **Illustratif** : les fichiers `sample_*` montrent à quoi ressemblent des données réelles sur un thème neutre. Ces lignes ont été écrites à la main pour la documentation, elles ne sortent pas d'un modèle.

## Exécuté : l'enchaînement complet hors ligne

```bash
export ANTHROPIC_API_KEY=fake
export CRUCIVERBISTE_CLAUDE_CMD="python3 tests/fake_claude.py"
python3 scripts/run_stage.py candidates candidats.jsonl --ledger registre.jsonl --cap 1 --theme "Astronomie" --count 4 --min-len 4 --max-len 10
python3 scripts/prepare_items.py candidats.jsonl entrees.jsonl --no-wikidata
python3 scripts/run_stage.py draft-new entrees.jsonl brouillons.jsonl --ledger registre.jsonl --cap 5
python3 scripts/combine.py solve-input entrees.jsonl brouillons.jsonl a_resoudre.jsonl rejets_lint.jsonl
python3 scripts/run_stage.py solve a_resoudre.jsonl resolu.jsonl --ledger registre.jsonl --cap 5
python3 scripts/combine.py verify-input entrees.jsonl brouillons.jsonl resolu.jsonl a_verifier.jsonl --dropped non_resolues.jsonl
python3 scripts/run_stage.py verify a_verifier.jsonl verdicts.jsonl --ledger registre.jsonl --cap 5
python3 scripts/combine.py fix-input a_verifier.jsonl verdicts.jsonl a_reverifier.jsonl
python3 scripts/run_stage.py verify a_reverifier.jsonl reverifies.jsonl --ledger registre.jsonl --cap 5
python3 scripts/combine.py finalize entrees.jsonl brouillons.jsonl verdicts.jsonl acceptes.jsonl rejetes.jsonl --mode new --recheck reverifies.jsonl
python3 scripts/ledger_report.py registre.jsonl --cap 5
```

Sorties de comptage obtenues :

```
{"items": 4, "spent_total": 0.01}
{"candidates": 4, "kept": 4, "rejected": 0}
{"items": 4, "written": 4, "failed_batches": 0, "stopped": "", "spent_total": 0.02}
{"to_solve": 12, "lint_rejects": 0}
{"items": 12, "written": 12, "failed_batches": 0, "stopped": "", "spent_total": 0.03}
{"to_verify": 12, "dropped_unsolved": 0}
{"items": 12, "written": 12, "failed_batches": 0, "stopped": "", "spent_total": 0.04}
{"to_recheck": 0}
{"items": 0, "written": 0, "failed_batches": 0, "stopped": "", "spent_total": 0.04}
{"accepted": 4, "rejected_lines": 0}
```

Quatre mots, douze définitions, quatre appels au faux CLI (candidats, rédaction, résolution, vérification ; la revérification n'avait rien à relire). Chaque appel « coûte » 0,01 $, d'où le total de 0,04 $.

## Avec le vrai modèle

Remplacez les deux premières lignes par votre vraie clé (`export ANTHROPIC_API_KEY=...`) et retirez `CRUCIVERBISTE_CLAUDE_CMD` ; retirez `--no-wikidata` pour obtenir les fiches d'existence. Commencez par `--limit 50`. Le dossier [../docs/USAGE.md](../docs/USAGE.md) donne les coûts mesurés.

## Illustratif : lecture des fichiers

[sample_entries.jsonl](sample_entries.jsonl) montre des entrées après `prepare_items` (avec fiche Wikidata) ; [sample_accepted.jsonl](sample_accepted.jsonl) le résultat de `finalize` ; [sample_report.md](sample_report.md) la façon de présenter un lot à son commanditaire.
