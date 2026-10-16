# Installation

Voir aussi : [CONFIGURATION.md](CONFIGURATION.md), [USAGE.md](USAGE.md), [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Prérequis

- Python 3.10 ou plus. Les scripts n'utilisent que la bibliothèque standard.
- Le CLI Claude Code (`claude`) installé et dans le `PATH` : https://claude.com/claude-code
- Une clé d'API Anthropic (facturation à l'usage, indépendante d'un abonnement). Les scripts appellent `claude --bare`, qui n'utilise **que** `ANTHROPIC_API_KEY`.
- Accès réseau sortant vers l'API Anthropic et vers `www.wikidata.org` (cette dernière seulement pour `prepare_items`).

## Installation comme skill Claude Code

Skill personnel (disponible dans tous vos projets) :

```bash
git clone https://github.com/RAAAAAGEEEEE/cruciverbiste.git ~/.claude/skills/cruciverbiste
```

Skill d'un seul projet :

```bash
git clone https://github.com/RAAAAAGEEEEE/cruciverbiste.git .claude/skills/cruciverbiste
```

Sous Windows, `~` est votre dossier utilisateur (`C:\Users\<vous>`). Au prochain démarrage de Claude Code, le skill `cruciverbiste` apparaît dans la liste des skills.

## Installation autonome (sans Claude Code interactif)

Les scripts sont utilisables seuls : clonez le dépôt n'importe où et lancez `python3 scripts/run_stage.py ...`. Voir [USAGE.md](USAGE.md).

## Vérifier l'installation

```bash
cd ~/.claude/skills/cruciverbiste
python3 -m unittest discover -s tests
```

Résultat attendu : `OK` en fin de sortie, sans clé d'API ni réseau (les tests utilisent un faux CLI).

## Fournir la clé

```bash
export ANTHROPIC_API_KEY="..."   # votre clé, jamais dans un fichier du dépôt
```

Sous PowerShell : `$env:ANTHROPIC_API_KEY = "..."`. Un modèle de fichier d'environnement est fourni dans [../.env.example](../.env.example) pour les outils qui chargent un `.env` ; ne le committez jamais rempli (le `.gitignore` exclut `.env`).

## Désinstallation

Supprimez le dossier du skill. Rien d'autre n'est écrit ailleurs sur la machine ; les registres et les JSONL sont dans les dossiers que vous avez choisis.
