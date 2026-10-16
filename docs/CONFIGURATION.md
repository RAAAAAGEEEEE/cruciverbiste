# Configuration

Voir aussi : [USAGE.md](USAGE.md), [ARCHITECTURE.md](ARCHITECTURE.md), [../.env.example](../.env.example).

## Variables d'environnement

| Variable | Requise | Rôle |
|---|---|---|
| `ANTHROPIC_API_KEY` | oui, pour toute étape à modèle | clé d'API utilisée par `claude --bare` ; jamais lue ni écrite par les scripts |
| `CRUCIVERBISTE_CLAUDE_CMD` | non | remplace la commande `claude` (binaire hors du `PATH`, ou faux CLI des tests) ; découpée comme un shell |

## `scripts/run_stage.py <étape> [entrée] [sortie]`

Étapes : `candidates`, `draft-new`, `draft-extra`, `solve`, `verify`. Pour `candidates`, la sortie est le premier argument positionnel et s'ajoute à la fin du fichier.

| Option | Défaut | Rôle |
|---|---|---|
| `--ledger` | obligatoire | registre JSONL des coûts |
| `--cap` | obligatoire | plafond cumulé du registre, en dollars |
| `--model` | selon l'étape | `claude-sonnet-5-5` (candidates, draft, solve) ; `claude-opus-5-5` (verify) |
| `--effort` | celui du CLI | `low`, `medium`, `high`, `xhigh`, `max` (réflexion) |
| `--batch` | selon l'étape | entrées par appel : 1, 25, 30, 60, 25 |
| `--workers` | 4 | appels en parallèle |
| `--limit N` | tout | ne traiter que les N premières entrées (lot test) |
| `--constraints` | aucun | fichier texte de consignes propres au projet (voir [../examples/constraints.example.txt](../examples/constraints.example.txt)) |
| `--language` | français | langue des définitions |
| `--rules` | `prompts/rules.md` | fichier de règles de rédaction (rédaction seulement ; le vérificateur applique ses propres règles, dont les 80 caractères) ; `prompts/rules.en.md` est fourni pour l'anglais |
| `--levels` | `1, 2` | niveaux à écrire en `draft-extra` |
| `--theme`, `--domain`, `--count`, `--min-len`, `--max-len`, `--avoid` | `--count 60`, `--min-len 3`, `--max-len 13` | `candidates` : thème, rubrique inscrite sur les candidats (défaut : le thème), nombre, bornes de longueur, liste à éviter |

L'étape `candidates` ignore `--batch`, `--workers`, `--limit`, `--rules` et `--levels`.

## `scripts/prepare_items.py <candidats> <sortie>`

`--existing` (fichier, une réponse A-Z par ligne, pour écarter les mots déjà en base), `--min-len` 3, `--max-len` 13, `--lang` fr (langue des libellés Wikidata), `--cache` (cache JSON des fiches), `--no-wikidata` (déconseillé : sans fiche, le rédacteur n'a plus de preuve d'existence). Écrit aussi `<sortie>.rejects`.

## `scripts/combine.py`

- `solve-input <items> <drafts> <sortie> [rejects] [--max-len 80]`
- `verify-input <items> <drafts> <solved> <sortie> [--dropped f] [--drop-unsolved-level 1 ...] [--max-len 80]`
- `fix-input <verify_in> <verified> <sortie> [--max-len 80]`
- `finalize <items> <drafts> <verified> <accepted> <rejected> [--mode new|extra] [--min-clues N] [--keep-on-doubt] [--recheck f] [--max-len 80]`

## `scripts/lint_clues.py`

`python3 scripts/lint_clues.py <fichier JSONL>` contrôle des définitions seules (options : `--max-len`, défaut 80). Les autres scripts l'appellent déjà.

## `scripts/ledger_report.py <registre> [--cap N]`

Affiche en JSON le total, le détail par étape et par modèle, et le reste sous le plafond.

## Règles de rédaction et consignes du projet

- `prompts/rules.md` (français) et `prompts/rules.en.md` (anglais) : règles communes. Pour une autre langue, copiez-en une et passez-la avec `--rules`, en même temps que `--language`.
- Le fichier de `--constraints` ajoute le contexte propre à votre jeu (public, graphies, interdits). Il est inséré tel quel dans chaque prompt : n'y mettez ni secret ni donnée personnelle.

## Choix de modèle et d'effort

`--effort` n'a pas de valeur par défaut dans les scripts (celle du CLI s'applique) ; les coûts de [USAGE.md](USAGE.md#coûts-mesurés) ont été mesurés avec `--effort medium`, à passer explicitement. Baisser l'effort de rédaction (`medium`) réduit fortement le coût ; baisser celui de la vérification réduit aussi la sévérité (mesuré sur un lot de 50 mots).
