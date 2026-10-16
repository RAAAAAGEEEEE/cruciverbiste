# Exemple de rapport de lot (illustratif)

Voir aussi : [walkthrough.md](walkthrough.md), [../SKILL.md](../SKILL.md).

Les nombres ci-dessous sont **inventés pour illustrer la forme du rapport** ; ils ne proviennent d'aucun lot réel. Pour des mesures réelles, voir « Coûts mesurés » dans [../docs/USAGE.md](../docs/USAGE.md).

## Lot test, thème « astronomie », 50 mots

**Résultat** : 50 mots proposés, 46 entrés après `prepare_items` (4 écartés : 2 sans fiche Wikidata, 1 doublon, 1 longueur hors bornes). 138 définitions rédigées, 131 passent le lint, 126 sont résolues à l'aveugle, 119 sont acceptées après vérification et revérification. 3 mots retirés pour doute factuel.

**Coût** : total 1,12 $ pour ce lot (rédaction 0,11 $, résolution 0,10 $, vérification 0,85 $, revérification 0,06 $) ; extrapolation pour 1 000 mots : environ 24 $ à ±30 %.

**Rejets typiques à lire** :

| Définition | Cause | Remède |
|---|---|---|
| « Elle brille sans produire de lumière » | `ambigu` : LUNE ou MARS (4 lettres) | ajouter « et tourne autour de nous » |
| « Planète à anneaux » | `ambigu` : plusieurs planètes | un trait qui isole (« Sixième planète à partir du Soleil ») |
| une date de lancement | `fait` : non vérifiable | retirer le chiffre ou le mot |

**Blocage** : aucun.

**À faire avant fusion** : relire au moins tous les niveaux 3 et les faits chiffrés ; fusionner avec l'adaptateur du projet ; lancer la validation du projet.
