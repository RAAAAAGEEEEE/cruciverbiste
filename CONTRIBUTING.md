# Contribuer

Les contributions sont bienvenues : correction de bogue, nouvelle langue (fichier de règles et exemple), nouvel adaptateur de format, amélioration des références avec une source datée.

## Avant d'ouvrir une demande de fusion

1. Lancer les tests : `python3 -m unittest discover -s tests` (hors ligne, aucune clé).
2. Toute modification de comportement met à jour la documentation concernée (`README.md`, `SKILL.md`, `docs/`) et `CHANGELOG.md` dans le même commit.
3. Toute nouvelle option de ligne de commande est décrite dans `docs/CONFIGURATION.md` ; toute nouvelle variable d'environnement aussi, plus `.env.example`.
4. Toute commande ajoutée à la documentation doit avoir été exécutée.
5. Les exemples doivent être génériques : pas de contenu d'un projet en production, pas de donnée personnelle, pas de secret.
6. Une affirmation sur les techniques de mots croisés doit citer une source consultée, avec la date de consultation et un niveau de fiabilité (voir `references/sources.md`).

## Style

Python 3.10+, bibliothèque standard uniquement, fonctions courtes, types annotés. Messages et documentation en français ; une version anglaise des règles de rédaction est maintenue dans `prompts/rules.en.md`.
