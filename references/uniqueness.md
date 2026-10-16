# Une seule réponse possible

Une définition qui admet deux réponses de même longueur est la cause la plus fréquente de frustration dans un jeu à réponse unique. Voir aussi [clue-craft.md](clue-craft.md).

## Les quatre sources d'ambiguïté

1. **Catégorie trop large.** « Planète à anneaux » convient à quatre planètes du système solaire. Correction : un trait qui isole (« Sixième planète à partir du Soleil »).
2. **Même longueur, même rubrique.** « Elle brille sans produire de lumière » convient à LUNE et à MARS (quatre lettres chacune). Correction : ajouter ce qui exclut l'autre (« ... et tourne autour de nous »).
3. **Graphies et versions.** Nom original ou localisé, singulier ou pluriel, avec ou sans article. Correction : préciser « en version française », « nom original », « au pluriel ».
4. **Homonymes.** Deux sens du même mot dans la même rubrique. Correction : situer par l'œuvre, le domaine ou l'époque.

## Les trois filtres de ce skill

1. **Lint mécanique** (gratuit) : fuite de la réponse ou d'un dérivé, longueur, doublon.
2. **Résolution à l'aveugle** : un modèle voit seulement rubrique, motif de longueur et définition, et propose jusqu'à trois réponses. Une définition de niveau 1 dont la réponse n'est pas proposée est écartée ; pour les autres niveaux la liste est transmise au vérificateur.
3. **Vérification** : un second modèle, qui voit la réponse et les propositions du résolveur, juge si une autre proposition est défendable (alors la définition est ambiguë), vérifie le fait, la fuite et le style, et rend `ok`, `fix` ou `drop`.

## Pourquoi un résolveur séparé

Le rédacteur connaît la réponse et la lit dans sa propre phrase ; il ne voit pas les autres lectures. Un résolveur indépendant les trouve. Sur un projet de jeu de mots croisés d'environ 3 000 mots (octobre 2026), la résolution à l'aveugle a signalé entre 3 et 6 % des définitions, le plus souvent par une réponse concurrente de même longueur que la précision « en version française » levait (voir [proven-workflow.md](proven-workflow.md)).

## Motif de longueur

Pour une réponse en plusieurs mots, le motif (« 4,5 » ou « 6-3 ») est donné au résolveur et, dans un jeu, au joueur : il élimine beaucoup de concurrents. Il faut donc le fournir au résolveur exactement comme le joueur le verra (`display` dans les entrées).
