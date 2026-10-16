# Journal des changements

Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/), versionnement [SemVer](https://semver.org/lang/fr/).

## [0.1.4] - 2026-10-17

### Corrigé
- Un `drop` sans cause, ou avec une cause imprévue (« Fait », « factuel »), ne retirait pas le mot en mode `new` : seules `ambigu` et `autre` l'épargnent maintenant. La cause est normalisée en minuscules.
- Une fiche sans champ `exact` n'est plus acceptée comme preuve d'existence.
- Documentation : message de plafond réel, sortie d'erreur UTF-8, chemins de `USAGE.md` (`$SKILL`), exemple de sortie complet, règle 3 d'ARCHITECTURE.

### Modifié
- 37 tests.

## [0.1.3] - 2026-10-17

### Corrigé
- Un verdict de vérification inconnu ou incomplet (« doute », « fix » sans texte, « drop » sans cause) était accepté : il est maintenant rejeté et, en mode `new`, retire le mot comme un doute factuel. Les verdicts sont normalisés en minuscules.
- Une réponse du modèle qui n'est pas un tableau JSON, ou des définitions mal typées, font échouer le lot (signalé, repris à la relance) au lieu de planter l'étape ; `candidates` affiche aussi un message clair dans ce cas.
- Une coupure de connexion pendant la recherche Wikidata est classée « injoignable ».
- Le tiret long du contrôle mécanique est écrit en échappement Unicode dans le code et le test.
- Documentation : alias de libellé pour `exact`, portée de `--rules`, dossier de travail hors du dépôt, essais répétés sur erreur d'API, `source` dans l'exemple de sortie.

### Modifié
- 36 tests.

## [0.1.2] - 2026-10-17

### Corrigé
- Une fiche Wikidata approximative (nom non identique, par exemple « Comète de Hal » -> comète de Halley) n'est plus acceptée comme preuve d'existence : l'entrée est rejetée (« fiche Wikidata non concordante »). Une panne réseau de Wikidata a sa propre raison (« injoignable »).
- `run_stage.py candidates` affiche un message clair (code de sortie 1) au lieu d'une trace Python quand l'appel au modèle échoue.
- `combine.py fix-input` accepte `--max-len` (80 par défaut) comme les autres sous-commandes.
- Documentation alignée sur les messages réels (dépannage), l'effet des options sur `candidates`, les essais répétés sur erreur d'API, le champ `exact`, un dossier de travail hors du dépôt.

### Modifié
- 33 tests.

## [0.1.1] - 2026-10-17

### Corrigé
- `prepare_items` cherchait dans Wikidata l'indice descriptif du modèle (« Orion constellation ») au lieu de la graphie du candidat : 13 candidats sur 20 étaient écartés à tort (lot réel du 16/10/2026). Il cherche maintenant la graphie et utilise l'indice et la rubrique pour départager les homonymes.

### Ajouté
- Les fiches homonymes (jusqu'à trois) sont transmises au rédacteur et au vérificateur, qui ne rejette plus une définition parce qu'elle ne correspond pas à la fiche choisie.

- Une mise à jour du CLI `claude` pendant un long traitement (binaire momentanément introuvable) faisait planter l'étape ; elle est maintenant réessayée (jusqu'à quatre fois, au lieu de deux).

- Une réponse du modèle suivie d'un second tableau ou d'une note (« Extra data ») faisait échouer un lot entier ; seul le premier JSON est lu maintenant.

### Modifié
- 32 tests au lieu de 29.

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
