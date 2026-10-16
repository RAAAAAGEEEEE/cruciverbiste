# Usage

Voir aussi : [CONFIGURATION.md](CONFIGURATION.md) (toutes les options), [ARCHITECTURE.md](ARCHITECTURE.md) (formats), [../examples/walkthrough.md](../examples/walkthrough.md) (déroulé), [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

Un dossier de travail neuf par lot : les étapes sautent les `id` déjà présents dans leurs fichiers de sortie. Lancez les scripts avec leur chemin complet depuis un dossier de travail à part, hors du dépôt du skill, pour que les fichiers JSONL produits n'y atterrissent pas (les exemples ci-dessous écrivent dans le dossier courant). Les noms de fichiers sont libres ; ceux-ci sont ceux de l'exemple. Prérequis : `ANTHROPIC_API_KEY` exportée ([INSTALLATION.md](INSTALLATION.md)).

## Règle d'or : un lot test avant le volume

Lancez les étapes sur 50 entrées avec `--limit 50`, lisez les rejets et le coût (`ledger_report.py`), puis extrapolez. Le plafond `--cap` protège le budget mais ne remplace pas ce test.

## Mode `new` : nouveaux mots

```bash
export SKILL=~/.claude/skills/cruciverbiste   # dossier du skill
export L=registre.jsonl            # un seul registre pour toute la session
python3 $SKILL/scripts/run_stage.py candidates candidats.jsonl --ledger $L --cap 50 \
    --theme "Astronomie" --domain "astronomie" --count 60 --min-len 4 --max-len 10 \
    --constraints $SKILL/examples/constraints.example.txt
python3 $SKILL/scripts/prepare_items.py candidats.jsonl entrees.jsonl --existing deja_en_base.txt --lang fr
python3 $SKILL/scripts/run_stage.py draft-new entrees.jsonl brouillons.jsonl --ledger $L --cap 50 --effort medium
python3 $SKILL/scripts/combine.py solve-input entrees.jsonl brouillons.jsonl a_resoudre.jsonl rejets_lint.jsonl
python3 $SKILL/scripts/run_stage.py solve a_resoudre.jsonl resolu.jsonl --ledger $L --cap 50 --effort medium
python3 $SKILL/scripts/combine.py verify-input entrees.jsonl brouillons.jsonl resolu.jsonl a_verifier.jsonl --dropped non_resolues.jsonl
python3 $SKILL/scripts/run_stage.py verify a_verifier.jsonl verdicts.jsonl --ledger $L --cap 50 --effort medium
python3 $SKILL/scripts/combine.py fix-input a_verifier.jsonl verdicts.jsonl a_reverifier.jsonl
python3 $SKILL/scripts/run_stage.py verify a_reverifier.jsonl reverifies.jsonl --ledger $L --cap 50 --effort medium
python3 $SKILL/scripts/combine.py finalize entrees.jsonl brouillons.jsonl verdicts.jsonl acceptes.jsonl rejetes.jsonl \
    --mode new --recheck reverifies.jsonl
python3 $SKILL/scripts/ledger_report.py $L --cap 50
```

`deja_en_base.txt` : une réponse A à Z par ligne (facultatif). `candidates` propose des idées de mots ; vous pouvez aussi écrire vous-même `candidats.jsonl` (une ligne `{"theme", "domain", "form", "hint"}` par mot). `prepare_items` interroge Wikidata, un candidat sans fiche est écarté et listé dans `entrees.jsonl.rejects`.

## Mode `extra` : définitions supplémentaires pour des mots existants

Produisez `entrees.jsonl` à partir de votre base : une ligne `{"id", "answer", "display", "domain", "clues": [{"level", "text"}]}` par mot. Puis les mêmes étapes avec `draft-extra` au lieu de `draft-new` (option `--levels "1, 2"` pour choisir les niveaux) et `finalize --mode extra`. En mode `extra`, seule la définition fautive est retirée : le mot existant reste. (`--keep-on-doubt` ne concerne que le mode `new`.)

## Mode `audit` : contrôler des définitions écrites ailleurs

Fabriquez directement `a_resoudre.jsonl` (`{"id": "REPONSE#niveau#n", "domain", "pattern", "text"}`) et `a_verifier.jsonl`, puis lancez `solve` et `verify`. Lisez les verdicts `fix` et `drop` comme une liste de relecture : le skill ne modifie jamais vos fichiers.

## Reprendre après une panne

Relancez la même commande : seules les entrées absentes de la sortie sont traitées. Un « lot en échec » (réponse du modèle non analysable) est signalé sur la sortie d'erreur ; relancer la commande retente ces lots.

## Fusionner `acceptes.jsonl` dans votre base

Le skill ne connaît pas le format de votre jeu. Écrivez un petit adaptateur : pour chaque ligne acceptée, `clues` donne les définitions `{"level", "text"}`, `answer` la réponse, `display` la graphie, `domain` la rubrique. Contrôlez ensuite avec la validation de votre projet avant de publier.

## Coûts mesurés

Mesures du 16/10/2026 sur 50 mots (94 à 98 définitions), API réelle, `claude-sonnet-5-5` pour rédiger et résoudre, `claude-opus-5-5` pour vérifier. Les coûts viennent du champ `total_cost_usd` du CLI.

| Étape | Réglage | Coût du lot de 50 mots |
|---|---|---|
| rédaction | effort `high` | environ 0,35 $ |
| rédaction | effort `medium` ou `low` | environ 0,05 $ |
| résolution à l'aveugle | `medium` | environ 0,04 $ |
| vérification | `medium` | environ 0,40 $ |
| vérification | `low` | environ 0,18 $, moins sévère |

Extrapolation linéaire (non garantie) : quelques dizaines de dollars pour plusieurs milliers de définitions. Environ un tiers des définitions de nouveaux mots reçoit un `fix` ou un `drop` dans ce lot ; prévoyez donc la revérification dans le budget.
