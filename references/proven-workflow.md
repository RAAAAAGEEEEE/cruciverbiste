# La méthode éprouvée, sous forme générique

Ce skill automatise une méthode appliquée à la main sur un jeu de duel de mots croisés d'environ 3 000 mots (trois grilles de dix mots par partie, trois niveaux de définition), en octobre 2026. Ce fichier la décrit sans reprendre le contenu du projet. Les chiffres sont des mesures de ce projet, pas des garanties.

## Les étapes manuelles d'origine

1. **Rédaction par rubrique.** Des agents rédacteurs écrivent mots et définitions rubrique par rubrique, avec un contrat de style : français naturel, jamais le mot ni un dérivé, 80 caractères au plus, trois définitions par mot (porte, moyen, mur).
2. **Contrôle mécanique.** Script : longueur, fuite de la réponse, doublons, nombre de définitions. Gratuit, toujours en premier.
3. **Résolution à l'aveugle.** Plusieurs agents résolvent chaque définition sans voir la réponse (rubrique et nombre de lettres seulement, identifiants neutres). Taux de définitions signalées sur trois lots : 3,0 %, 4,9 % et 5,8 %. Causes : réponse concurrente de même longueur, précision manquante, fait douteux.
4. **Réécriture.** Précisions du type « en version française » ou « nom original », ajout d'un détail qui exclut le concurrent, ou remplacement de l'angle.
5. **Second contrôle à l'aveugle** sur les seules réécritures.
6. **Relecture complète** par quatre relecteurs qui voient les réponses : faits, accords, rapport avec le thème. Sur environ 3 000 mots, 148 définitions ont été corrigées : 80 sans rapport avec le thème, 22 faits douteux, 12 ambiguës, 35 tournures ou accords. Les faits douteux sont les plus rares mais les plus coûteux.
7. **Retrait sur doute.** Un mot dont un fait ou une graphie est douteux est retiré plutôt que corrigé à l'estime ; les personnes réelles identifiables ne sont pas acceptées comme réponses.
8. **Reclassement en trois niveaux** et vérification de la recette de difficulté des grilles (portes, moyens, murs et pente).

## Ce que le skill automatise

| Étape manuelle | Étape du skill |
|---|---|
| liste de mots par rubrique | `candidates` (ou liste fournie), `prepare_items` (normalisation, doublons, fiche Wikidata) |
| rédaction | `draft-new` (nouveaux mots) ou `draft-extra` (définitions supplémentaires pour des mots existants) |
| contrôle mécanique | `lint_clues.py` appelé par `combine.py solve-input` |
| résolution à l'aveugle | `solve` |
| relecture avec réponses visibles, réécriture | `verify` (modèle plus capable) puis `fix-input` et revérification des corrections |
| retrait sur doute | `finalize` (`--keep-on-doubt` désactive le retrait pour les définitions supplémentaires) |

La **recette de difficulté** (portes, moyens, murs selon la grille) et les règles de croisement ne sont pas dans le pipeline : elles se règlent dans le générateur de grilles du jeu (voir [difficulty-curve.md](difficulty-curve.md)).

## Leçons transférables

- Le résolveur doit être **indépendant** du rédacteur et ne jamais voir la réponse.
- La majorité des corrections sont des **précisions**, pas des réécritures totales.
- Les réécritures sont une source d'erreurs nouvelle : il faut les **revérifier** (le skill le fait).
- Un modèle plus capable pour la vérification coûte plus cher mais invente moins ; faire la rédaction avec un effort de réflexion moyen est nettement moins cher qu'un effort élevé, sans perte visible de qualité mesurée sur un lot de 50 mots (voir [../docs/USAGE.md](../docs/USAGE.md)).
