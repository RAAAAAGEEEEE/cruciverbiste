# Journal des changements

Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/), versionnement [SemVer](https://semver.org/lang/fr/).

## [0.1.0] - 2026-10-16

Première version publique (alpha).

### Ajouté
- Consignes de rédaction (français et anglais), niveaux porte / moyen / mur.
- Étapes `candidates`, `draft-new`, `draft-extra`, `solve`, `verify` (`scripts/run_stage.py`), en lots, avec reprise et plafond de dépense en dollars.
- Assemblage (`scripts/combine.py`) : lint, résolution à l'aveugle, vérification, revérification des corrections, bilan accepté / rejeté.
- Préparation des candidats avec fiche Wikidata (`scripts/prepare_items.py`, `scripts/wikidata.py`).
- Registre des coûts et rapport (`scripts/ledger_report.py`).
- Références sur les techniques des verbicrucistes, la difficulté et la tension de partie.
- 29 tests hors ligne avec un faux CLI `claude`.
