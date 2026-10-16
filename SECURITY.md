# Sécurité

Ce dépôt n'a ni serveur ni authentification, mais ses scripts appellent l'API Anthropic avec une clé et envoient du texte à des services tiers. Voir [docs/PRIVACY_AND_SECURITY.md](docs/PRIVACY_AND_SECURITY.md) pour le détail.

## Signaler une vulnérabilité

Ouvrez une alerte de sécurité privée depuis l'onglet « Security » du dépôt GitHub (« Report a vulnerability »), sans mettre de secret ni de preuve d'exploitation dans une issue publique. Réponse visée sous 7 jours.

## Rappels

- La clé d'API ne doit jamais être commitée ni affichée ; les scripts ne la lisent ni ne l'écrivent.
- Les fichiers `ledger.jsonl` contiennent des coûts et des noms de modèles, pas de clé.
- Ne soumettez pas de données personnelles ou confidentielles comme réponses ou définitions.
