# Confidentialité et sécurité

Voir aussi : [../SECURITY.md](../SECURITY.md) (signaler une faille), [LIMITATIONS.md](LIMITATIONS.md), [CONFIGURATION.md](CONFIGURATION.md).

## Quelles données sortent, et vers où

| Destination | Données | Quand |
|---|---|---|
| API Anthropic (via le CLI `claude`) | les réponses, rubriques, définitions, consignes du projet (`--constraints`) et règles de rédaction de chaque lot | à chaque étape à modèle |
| `www.wikidata.org` | la graphie du candidat (l'indice du modèle reste local), rien d'autre | `prepare_items`, sauf `--no-wikidata` |

Rien d'autre n'est envoyé nulle part : pas de télémétrie, pas de dépôt de données. Les JSONL et le registre restent sur votre machine.

Ne mettez dans `--constraints`, dans les entrées ou dans les définitions **aucune donnée personnelle ni secret** : tout est transmis au fournisseur du modèle selon ses conditions d'utilisation de l'API.

## Clé d'API

- Lue uniquement par le CLI `claude` depuis la variable `ANTHROPIC_API_KEY` ; les scripts vérifient seulement qu'elle est définie, sans l'afficher ni l'écrire.
- Le mode `--bare` n'utilise ni abonnement, ni fichiers de configuration du CLI, ni hooks, ni sessions enregistrées (`--no-session-persistence`).
- Le CLI est lancé **sans outil** (`--tools ""`) : le modèle ne peut ni lire de fichier, ni exécuter de commande, ni accéder au réseau. Une consigne malveillante glissée dans une entrée ou une réponse de modèle ne peut donc agir que sur le texte renvoyé.
- Ne committez jamais la clé : `.env` est dans `.gitignore`, `.env.example` est vide.

## Sorties de modèle = données non fiables

Les JSONL produits sont des données, pas des instructions. Le skill ne les exécute jamais. Si vous les chargez dans votre jeu ou votre site, échappez-les comme tout texte externe.

## Budget

Le plafond `--cap` limite la dépense cumulée du registre. Un registre supprimé ou un autre fichier remet le compteur à zéro : utilisez le même registre pour toute une session.

## Signaler une vulnérabilité

Voir [../SECURITY.md](../SECURITY.md).
