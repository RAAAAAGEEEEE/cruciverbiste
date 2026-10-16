# Architecture

Voir aussi : [USAGE.md](USAGE.md) (commandes), [CONFIGURATION.md](CONFIGURATION.md) (options), [../references/proven-workflow.md](../references/proven-workflow.md) (d'où vient la méthode).

## Vue d'ensemble

```
candidats -> prepare_items -> draft-new / draft-extra -> solve-input -> solve
          -> verify-input -> verify -> fix-input -> verify (revérification) -> finalize
```

Chaque flèche est un fichier JSONL (un objet JSON par ligne, UTF-8). Les étapes qui appellent un modèle (`candidates`, `draft-*`, `solve`, `verify`) passent par `scripts/run_stage.py`, les étapes gratuites par `scripts/combine.py` et `scripts/prepare_items.py`. Aucune étape ne modifie la base du projet : la dernière sortie (`accepted.jsonl`) est à fusionner par vos soins (voir [USAGE.md](USAGE.md)).

## Composants

| Fichier | Rôle |
|---|---|
| `scripts/llm.py` | appelle `claude -p --bare` (clé de `ANTHROPIC_API_KEY` uniquement, aucun outil, aucune session), journalise chaque appel dans un registre JSONL, refuse de partir si le plafond est atteint, réessaie deux fois |
| `scripts/run_stage.py` | une étape à modèle : lots, travailleurs parallèles, reprise (les `id` déjà écrits sont sautés), budget |
| `scripts/prepare_items.py` | normalise les candidats (A à Z), filtre la longueur, écarte les doublons et les mots existants, ajoute la fiche Wikidata (CC0) |
| `scripts/wikidata.py` | recherche d'une entité par `wbsearchentities`, cache local, pause entre requêtes |
| `scripts/lint_clues.py` | contrôle mécanique : longueur, fuite de la réponse ou d'un dérivé, doublon, ponctuation |
| `scripts/combine.py` | `solve-input`, `verify-input`, `fix-input`, `finalize` : tout ce qui relie les étapes, sans appel au modèle |
| `scripts/ledger_report.py` | totaux du registre par étape et par modèle, reste sous le plafond |
| `prompts/` | consignes aux modèles (`rules.md` et `rules.en.md` : règles de rédaction partagées) |
| `references/` | savoir-faire lu par l'humain ou par Claude, pas par les scripts |
| `tests/` | tests hors ligne avec un faux CLI (`fake_claude.py`) |

## Formats

**Candidat** (`candidates` écrit, `prepare_items` lit) : `{"theme", "domain", "form", "hint"}`.

**Entrée** (`prepare_items` écrit) : `{"id", "answer", "display", "domain", "source": {"qid", "description"}}`. `answer` est la réponse sans accent ni espace ; `display` est la graphie lisible si elle contient espace ou trait d'union (elle donne le motif de longueur « 4,5 » ou « 6-3 »). Pour compléter un mot existant (`draft-extra`), l'entrée porte aussi `clues`, la liste `{"level", "text"}` déjà en place.

**Brouillon** (`draft-new` / `draft-extra` écrit) : `draft-new` → `{"id", "familiarity", "clues": [{"level", "text"}]}` ; `draft-extra` → `{"id", "new": [...]}` ; ou `{"id", "skip": "raison"}` si le rédacteur renonce.

**À résoudre** (`combine.py solve-input`) : `{"id": "RÉPONSE#niveau#n", "domain", "pattern", "text"}`. Le prompt n'affiche jamais la réponse.

**Résolu** (`solve`) : `{"id", "guesses": [...]}`.

**À vérifier** (`combine.py verify-input`) : `{"id", "answer", "display", "domain", "level", "text", "others", "guesses", "source"}` où `others` sont les autres définitions du mot.

**Verdict** (`verify`) : `{"id", "v": "ok" | "fix" | "drop", "text"?, "why"?, "cause"?: "fait" | "ambigu" | "autre"}`.

**Accepté** (`finalize` écrit `accepted.jsonl`) : `{"id", "answer", "display", "domain", "clues": [{"level", "text"}], "familiarity"?, "source"?}`. **Rejeté** (`rejected.jsonl`) : `{"id", "reason", "text"?, "cause"?}`.

## Règles de décision de `finalize`

1. Une définition qui échoue au lint est rejetée.
2. Sans verdict (résolution ou vérification absente), elle est rejetée.
3. `drop` la rejette ; en mode `new`, un `drop` de cause `fait` retire **tout le mot**, sauf avec `--keep-on-doubt`.
4. `fix` remplace le texte, à condition que le nouveau texte passe le lint et, avec `--recheck`, que la revérification réponde `ok`.
5. En mode `new`, un mot garde au moins deux définitions dont une de niveau 1 ou 2 (`--min-clues` change le minimum) ; en mode `extra`, une définition suffit.

## Choix de conception

- **Résolveur indépendant** du rédacteur et aveugle : la cause la plus fréquente d'ambiguïté est invisible pour qui connaît la réponse (voir [../references/uniqueness.md](../references/uniqueness.md)).
- **Vérificateur plus capable** que le rédacteur, mais appelé une fois par lot : c'est l'étape la plus chère, donc la dernière.
- **Revérification des corrections** : un `fix` n'a été relu par personne.
- **Plafond avant chaque appel** : des appels déjà partis en parallèle peuvent le dépasser de quelques centimes.
- **Reprise** : relancer la même commande ne traite que les `id` absents de la sortie.
- **Pas d'état caché** : tout est dans les fichiers JSONL et dans le registre.
