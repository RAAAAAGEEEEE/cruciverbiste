# Journal des changements

Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/), versionnement [SemVer](https://semver.org/lang/fr/).

## [0.1.1] - 2026-10-17

### Corrigé
- `prepare_items` cherchait dans Wikidata l'indice descriptif du modèle (« Orion constellation ») au lieu de la graphie du candidat : 13 candidats sur 20 étaient écartés à tort (lot réel du 16/10/2026). Il cherche maintenant la graphie et utilise l'indice et la rubrique pour départager les homonymes.

### Ajouté
- Les fiches homonymes (jusqu'à trois) sont transmises au rédacteur et au vérificateur, qui ne rejette plus une définition parce qu'elle ne correspond pas à la fiche choisie.

### Modifié
- 30 tests au lieu de 29 (ajout du départage des homonymes).

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
