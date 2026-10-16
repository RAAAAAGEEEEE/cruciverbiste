# cruciverbiste

Skill pour Claude Code : écrire et contrôler des définitions de mots croisés dans la langue et sur le thème de votre choix, avec les techniques des verbicrucistes (le « verbicruciste » est la personne qui écrit les définitions d'une grille).

Statut : **alpha (0.1.5, 17/10/2026)**. Les scripts sont testés hors ligne (38 tests) et le flux complet a été exécuté sur un lot de 50 entrées avec l'API réelle ; il n'a pas encore servi à des volumes publics. Voir [docs/LIMITATIONS.md](docs/LIMITATIONS.md).

## Le problème

Un jeu de mots croisés (ou de quiz à réponse unique) se lasse vite : mêmes mots, mêmes phrases. Écrire des milliers de définitions justes, variées, calibrées en difficulté et sans ambiguïté est long, et un modèle de langage seul invente des faits, laisse fuir la réponse dans l'indice ou propose des définitions qui conviennent à plusieurs mots.

## Pour qui

Créateurs de jeux de mots, de quiz et d'applications d'apprentissage qui maintiennent une base « réponse + définitions », et qui ont une clé d'API Anthropic.

## Ce que ça apporte

- trois niveaux de définition : **porte** (directe), **moyen** (fait précis), **mur** (allusive, mais une seule réponse) ;
- des consignes de rédaction éprouvées (double sens honnête, fausse piste loyale, concordance grammaticale, pas de fuite de la réponse) ;
- un flux en cinq étapes avec contrôles gratuits puis payants : lint mécanique, résolution à l'aveugle, vérification factuelle, revérification des corrections ;
- une fiche d'existence Wikidata (données CC0) pour chaque nouveau mot ;
- un budget en dollars plafonné et un registre des coûts, reprise possible après une panne ;
- des références sur la difficulté, le rythme et la tension d'une partie ([references/](references/)).

## Prérequis

- Python 3.10 ou plus (bibliothèque standard seule, aucune dépendance à installer)
- le CLI [Claude Code](https://claude.com/claude-code) (`claude`) installé
- une clé d'API Anthropic dans la variable d'environnement `ANTHROPIC_API_KEY` (voir [.env.example](.env.example))

## Quickstart

```bash
git clone https://github.com/RAAAAAGEEEEE/cruciverbiste.git
cd cruciverbiste
python3 -m unittest discover -s tests          # 38 tests, hors ligne, aucune clé requise
export ANTHROPIC_API_KEY=...                   # votre clé ; jamais dans un fichier du dépôt
python3 scripts/run_stage.py candidates candidats.jsonl --ledger registre.jsonl --cap 1 \
    --theme "Astronomie" --count 20 --min-len 4 --max-len 10
python3 scripts/prepare_items.py candidats.jsonl entrees.jsonl --lang fr
python3 scripts/run_stage.py draft-new entrees.jsonl brouillons.jsonl --ledger registre.jsonl --cap 2 --effort medium
```

Pour l'installer comme skill Claude Code : [docs/INSTALLATION.md](docs/INSTALLATION.md). Un déroulé complet avec les sorties réelles : [examples/walkthrough.md](examples/walkthrough.md).

## Exemple minimal

Entrée (`entrees.jsonl`, une ligne) :

```json
{"id": "MARS", "answer": "MARS", "display": "", "domain": "astronomie", "source": {"qid": "Q111", "description": "planète du système solaire"}}
```

Sortie acceptée (`accepted.jsonl`, exemple illustratif, voir [examples/](examples/)) :

```json
{"id": "MARS", "answer": "MARS", "display": "", "domain": "astronomie", "source": {"qid": "Q111", "...": "..."}, "familiarity": 1, "clues": [
  {"level": 1, "text": "Planète rouge"},
  {"level": 2, "text": "Quatrième planète à partir du Soleil"},
  {"level": 3, "text": "Dieu romain de la guerre dont une planète prend le nom"}]}
```

## Architecture résumée

`prompts/` (consignes aux modèles) + `scripts/` (appel du modèle avec budget, étapes en lots, assemblage, Wikidata) + `references/` (savoir-faire). Chaque étape lit et écrit du JSONL. Détail : [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Configuration

Langue, rubrique, consignes du projet, règles de rédaction, modèles, effort, plafond de dépense. Détail : [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

## Sécurité et confidentialité

Les entrées sont envoyées à l'API Anthropic ; seul le terme cherché va à Wikidata ; la clé n'est jamais lue par les scripts. Détail : [docs/PRIVACY_AND_SECURITY.md](docs/PRIVACY_AND_SECURITY.md) et [SECURITY.md](SECURITY.md).

## Limites

Pas de recherche web pendant la vérification, donc pas de garantie d'exactitude ; qualité inégale selon la langue et le domaine ; échantillon humain indispensable. Liste honnête : [docs/LIMITATIONS.md](docs/LIMITATIONS.md).

## Feuille de route (non contractuelle)

- vérification adossée à une recherche web ou à une source locale ;
- adaptateurs prêts à l'emploi pour quelques formats courants (CSV, SQLite) ;
- mesure en jeu des définitions (taux de réussite par définition) pour recalibrer les niveaux.

## Documentation

[Installation](docs/INSTALLATION.md) · [Usage](docs/USAGE.md) · [Configuration](docs/CONFIGURATION.md) · [Architecture](docs/ARCHITECTURE.md) · [Dépannage](docs/TROUBLESHOOTING.md) · [Limites](docs/LIMITATIONS.md) · [Confidentialité et sécurité](docs/PRIVACY_AND_SECURITY.md) · [Mentions légales et attributions](docs/LEGAL_AND_ATTRIBUTION.md) · [Journal des changements](CHANGELOG.md) · [Contribuer](CONTRIBUTING.md)

## Licence

MIT, voir [LICENSE](LICENSE).
