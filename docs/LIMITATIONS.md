# Limites

Voir aussi : [PRIVACY_AND_SECURITY.md](PRIVACY_AND_SECURITY.md), [../README.md](../README.md).

Statut : alpha, version 0.1.1 (17/10/2026).

## Exactitude des faits

- Les modèles n'ont **pas d'accès au web** pendant la rédaction ni la vérification (le CLI est lancé sans outil). La fiche Wikidata prouve l'existence d'une entité, pas l'exactitude d'un fait de la définition.
- La vérification par un second modèle réduit le risque d'erreur factuelle sans l'éliminer. Les erreurs d'un modèle ne sont pas toutes visibles à un autre modèle.
- **Un échantillon humain est indispensable** avant toute publication : relire au moins les définitions de niveau 3 et tous les faits chiffrés ou datés.
- Les faits qui changent avec le temps sont à éviter ; les règles du skill le demandent mais ne le garantissent pas.

## Qualité selon la langue et le domaine

- Testé en français ; une règle d'écriture en anglais est fournie mais n'a pas été mesurée. Les autres langues demandent un fichier de règles et un test.
- Les domaines pointus ou récents (jeux, séries, culture de niche) sont les plus exposés aux erreurs et aux graphies divergentes.
- Les jeux de mots et fausses pistes de niveau 3 sont la partie la moins fiable : à relire un par un.

## Périmètre

- Le skill ne construit pas de grille et ne place pas de mots.
- Il n'écrit pas dans la base de votre projet : un adaptateur est à écrire (voir [USAGE.md](USAGE.md)).
- La mesure du niveau de difficulté réel vient du jeu (taux de réussite), pas du skill.

## Coûts

- Les coûts de la section « Coûts mesurés » de [USAGE.md](USAGE.md) viennent d'un seul lot de 50 mots ; ils varient avec le thème, la longueur des définitions et les tarifs de l'API.
- Le plafond est vérifié avant chaque appel : des appels parallèles déjà partis peuvent le dépasser de quelques centimes.

## Technique

- Dépend du format de sortie JSON du CLI `claude -p` ; un changement de ce format peut casser `llm.py`.
- Wikidata : une recherche par terme peut choisir la mauvaise entité homonyme ; la rubrique et la description sont transmises au rédacteur pour qu'il renonce en cas de doute.
- Aucun contrôle d'orthographe indépendant.

## Hors périmètre de cette version

Recherche web pendant la vérification, adaptateurs de formats, mesure en jeu : voir la feuille de route du [README](../README.md).
