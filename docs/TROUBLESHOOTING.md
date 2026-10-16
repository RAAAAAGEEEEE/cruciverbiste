# Dépannage

Voir aussi : [USAGE.md](USAGE.md), [CONFIGURATION.md](CONFIGURATION.md), [LIMITATIONS.md](LIMITATIONS.md).

| Symptôme | Cause probable | Que faire |
|---|---|---|
| `ANTHROPIC_API_KEY absente de l'environnement` (étape `candidates` : `échec : ...`, code 1 ; autres étapes : `lot en échec : ...`, code 0) | variable non exportée dans ce terminal | exporter la clé ([INSTALLATION.md](INSTALLATION.md)) ; ne pas la mettre dans un fichier versionné |
| `lot en échec : commande impossible à lancer : [Errno 2] ... 'claude'` (après environ 1 min 15 par lot : 5 tentatives) | CLI non installé ou hors du `PATH` | installer Claude Code, ou définir `CRUCIVERBISTE_CLAUDE_CMD` avec le chemin du binaire |
| `plafond atteint` / `stopped` non vide dans le résumé | le total du registre a atteint `--cap` | relire le coût avec `ledger_report.py`, puis relancer avec un plafond plus haut : la reprise saute ce qui est fait |
| code de sortie 0 malgré un `failed_batches` non nul | `run_stage.py` ne renvoie pas d'erreur pour des lots échoués | lire `failed_batches` dans le résumé JSON, puis relancer |
| `lot en échec : ...` sur la sortie d'erreur | clé ou CLI absent (voir plus haut), erreur d'API répétée, ou réponse du modèle non analysable (JSON tronqué ou texte autour) | relancer la même commande ; si cela se répète, réduire `--batch` |
| un lot écrit moins de lignes que d'entrées | le modèle a omis des `id` | relancer : les `id` absents sont retraités |
| le coût dépasse de quelques centimes le plafond | appels déjà partis en parallèle | normal ; baisser `--workers` pour réduire l'écart |
| `UnicodeEncodeError` sous Windows | page de code non UTF-8 | définir `PYTHONIOENCODING=utf-8` (les scripts reconfigurent déjà la sortie d'erreur) |
| beaucoup de candidats écartés par `prepare_items` | pas de fiche Wikidata, mot déjà en base, ou longueur hors bornes | lire `<sortie>.rejects` ; varier la graphie ou fournir `candidats.jsonl` à la main |
| Wikidata répond lentement ou refuse | limite de débit ou panne | relancer avec `--cache` pour ne pas repasser par les mots déjà cherchés |
| trop de `drop` de cause `ambigu` | rubrique trop large ou longueurs courtes | affiner `--domain`, ajouter des graphies dans `--constraints`, viser des mots plus longs |
| des définitions correctes sont rejetées au lint | le mot de la réponse apparaît dans une expression courante | réécrire l'indice à la main ; le lint est volontairement strict |
| tests en échec | version de Python < 3.10 | `python3 --version` ; puis `python3 -m unittest discover -s tests` (les tests imposent eux-mêmes une fausse clé et un faux CLI) |

Si le problème persiste : ouvrir une issue avec la commande lancée, le résumé affiché et le contenu (sans clé) du registre ; voir [../CONTRIBUTING.md](../CONTRIBUTING.md).
