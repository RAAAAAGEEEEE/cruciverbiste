---
name: cruciverbiste
description: Produit et contrôle des définitions de mots croisés (et de jeux de mots à définitions) avec les techniques des verbicrucistes, pour une langue, un thème et un format de sortie au choix. Trois niveaux de difficulté (porte, moyen, mur), fausses pistes loyales, une seule réponse possible, contrôle mécanique, résolution à l'aveugle par un second modèle, vérification factuelle avec retrait au moindre doute, budget en dollars plafonné. À utiliser pour « écris des définitions de mots croisés », « ajoute des mots et des définitions à ma base », « donne-moi une deuxième définition pour chaque mot », « contrôle ces définitions », « calibre la difficulté et la tension d'une grille ». Ne compose pas la grille elle-même.
---

# cruciverbiste

Version 0.1.2 (17/10/2026). Documentation complète : `README.md` et `docs/`.

## Périmètre

Dans le périmètre :
- rédiger des définitions (porte / moyen / mur) pour des réponses données, dans la langue et sur le thème demandés ;
- proposer des réponses candidates pour un thème, avec une fiche d'existence Wikidata ;
- contrôler des définitions existantes (lint, résolution à l'aveugle, vérification des faits, unicité de la réponse) ;
- conseiller sur la difficulté, le rythme et la tension d'une partie (références dans `references/`).

Hors périmètre :
- construire ou remplir la grille (placement des mots) ;
- publier ou modifier le fichier de production d'un projet : le skill écrit des fichiers JSONL intermédiaires, un adaptateur propre au projet (court, à écrire) fait le pont avec son format ;
- garantir l'exactitude des faits : le contrôle est fait par des modèles sans accès au web, il réduit le risque, il ne l'élimine pas (voir `docs/LIMITATIONS.md`).

## Quand l'utiliser

Déclencheurs : demande de définitions de mots croisés ou de jeu à indices, extension d'une base de mots, deuxième ou troisième définition par mot, audit de définitions, réflexion sur la difficulté d'une grille. Ne pas l'utiliser pour de la rédaction générale (voir un skill de rédaction) ni pour un quiz sans réponse unique.

## Modes d'exécution et ordre

| Mode | Étapes (dans l'ordre) | Quand |
|---|---|---|
| `extra` : nouvelles définitions pour des mots existants | `draft-extra` -> `solve-input` -> `solve` -> `verify-input` -> `verify` -> `fix-input` -> `verify` (revérification) -> `finalize --mode extra` | une base existe, il faut varier les définitions |
| `new` : nouveaux mots | `candidates` -> `prepare_items` (Wikidata) -> `draft-new` -> `solve-input` -> `solve` -> `verify-input` -> `verify` -> `fix-input` -> `verify` -> `finalize --mode new` | il faut de nouvelles réponses |
| `audit` : contrôler des définitions écrites ailleurs | `solve` -> `verify` -> `fix-input` -> `verify` (entrées au format décrit dans `docs/ARCHITECTURE.md`) | relecture d'une base |
| `conseil` : difficulté, rythme, tension | lire `references/difficulty-curve.md` et `references/grid-tension.md` | pas de génération |

Toujours commencer par un lot test (50 entrées), lire le résultat et le coût, puis extrapoler avant le volume (`scripts/ledger_report.py`).

## Entrées et sorties

Entrées : thème ou liste de réponses, langue (`--language`), fichier de consignes du projet (`--constraints`), éventuellement fichier de règles de rédaction (`--rules`, par défaut `prompts/rules.md`, version anglaise `prompts/rules.en.md`), plafond de dépense (`--cap`) et registre des coûts (`--ledger`).
Sorties : fichiers JSONL (`accepted.jsonl`, `rejected.jsonl` avec la raison de chaque rejet) et registre des coûts. Format détaillé dans `docs/ARCHITECTURE.md`.

## Procédure (résumé)

1. Lire `prompts/rules.md` et `references/clue-craft.md`, écrire le fichier de consignes du projet (domaine, graphies, interdits).
2. `export` du projet vers des entrées JSONL (adaptateur du projet).
3. Lot test, puis volume avec `scripts/run_stage.py` (reprise possible, plafond en dollars).
4. `scripts/combine.py` pour chaîner lint, résolution à l'aveugle, vérification, revérification des corrections.
5. Relire un échantillon de `accepted.jsonl` soi-même (une dizaine par lot) avant d'injecter dans le projet.
6. Lancer les contrôles du projet (validateur, tests), puis commit.

Réglages recommandés (mesurés le 16/10/2026 sur un lot de 50 mots, voir `docs/USAGE.md`) : rédaction Sonnet effort `medium`, résolution à l'aveugle Sonnet `medium`, vérification Opus `medium`.

## Niveaux de preuve d'une définition acceptée

1. lint mécanique (longueur, fuite de la réponse, doublon, tiret long) ;
2. résolue à l'aveugle (la réponse figure parmi les propositions d'un résolveur qui ne la voit pas) ;
3. vérifiée par un second modèle (fait, unicité, fuite) ;
4. pour une correction : revérifiée après correction ;
5. pour un mot nouveau : fiche Wikidata (identifiant conservé) ;
6. échantillon relu par un humain.
Le skill n'affirme jamais « exact » : il dit quels niveaux ont été franchis.

## Comportement de repli

- Plafond de dépense atteint : arrêt avant l'appel suivant, état conservé, relance possible.
- Lot en échec (JSON illisible, erreur d'API) : nouvel essai jusqu'à quatre fois pour une erreur du CLI (délai, binaire introuvable, sortie illisible) ; une réponse du modèle mal formée fait échouer le lot tout de suite, puis lot signalé et sauté ; relancer la même commande ne refait que ce qui manque.
- Fiche Wikidata introuvable : candidat écarté (`--no-wikidata` pour passer outre, déconseillé).
- Doute factuel : l'entrée est retirée, jamais « arrangée ».

## Exemples d'invocation

- « Avec cruciverbiste, écris une deuxième définition de niveau 1 et 2 pour les 300 mots de `words.json`, en français, plafond 8 $ »
- « Propose 200 nouveaux mots sur l'astronomie, 4 à 10 lettres, avec trois définitions chacun »
- « Contrôle les définitions de `mots.csv` : lesquelles ont plusieurs réponses possibles ? »

Exemple de sortie : `examples/sample_report.md`. Exemple complet de bout en bout : `examples/walkthrough.md`.

## Sécurité et confidentialité

Les prompts (réponses, définitions, consignes) partent vers l'API Anthropic via le CLI `claude -p --bare` avec la clé de `ANTHROPIC_API_KEY`. Seul le terme cherché part vers Wikidata. La clé n'est jamais lue, écrite ni affichée par les scripts. Voir `docs/PRIVACY_AND_SECURITY.md`. Procédures PLAN/FIX/VERIFY : sans objet, le skill ne modifie aucun code ni fichier de production (il écrit des JSONL intermédiaires). Ne jamais mettre de données personnelles ni de contenu confidentiel dans les entrées.

## Installation

Personnelle : copier ce dossier dans `~/.claude/skills/cruciverbiste/`. Par projet : `.claude/skills/cruciverbiste/` dans le dépôt. Détail et vérification : `docs/INSTALLATION.md`.

## Tests

`python3 -m unittest discover -s tests` (aucun réseau, aucune clé : un faux CLI `claude` est fourni dans `tests/fake_claude.py`).

## Références et attributions

`references/sources.md` (sources datées avec niveau de fiabilité), `docs/LEGAL_AND_ATTRIBUTION.md`.
