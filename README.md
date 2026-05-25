# 🛡️ Anti-Raid Bot Discord

Bot Discord qui détecte et bannit automatiquement les utilisateurs qui rejoignent trop de salons vocaux en peu de temps (comportement de type DDOS/raid vocal).

-----

## ⚙️ Installation

### 1. Cloner le repo

```bash
git clone https://github.com/TON_PSEUDO/anti-raid-bot.git
cd anti-raid-bot
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Configurer le bot

Ouvre `bot.py` et remplace les valeurs en haut du fichier :

```python
TOKEN          = "TON_TOKEN_ICI"
OWNER_ID       = TON_ID_DISCORD
LOG_CHANNEL_ID = ID_DU_SALON_LOGS
```

> Tu peux trouver ton token sur le [Discord Developer Portal](https://discord.com/developers/applications)

### 4. Lancer le bot

```bash
python bot.py
```

-----

## 🤖 Commandes

> ⚠️ Toutes les commandes sont **réservées à l’owner** (ID configuré dans `bot.py`)

|Commande                    |Description                      |
|----------------------------|---------------------------------|
|`!limit on`                 |Active la surveillance vocale    |
|`!limit off`                |Désactive la surveillance vocale |
|`!limit <nombre> <secondes>`|Configure le seuil de détection  |
|`!limitinfo`                |Affiche la configuration actuelle|

**Exemples :**

```
!limit on
!limit off
!limit 3 6       → ban si 3 vocaux différents en 6s
!limit 5 10      → ban si 5 vocaux différents en 10s
```

-----

## 📋 Système de logs

Quand un ban est déclenché, le bot envoie automatiquement un embed dans le salon de logs configuré :

```
🚨 DÉTECTION DDOS

username / (id) à tenté de ddos, il a été banni.
Heure : HH:MM:SS
Date : DD/MM/YYYY
```

-----

## 🔐 Permissions requises pour le bot

- `Ban Members`
- `View Channels`

Le rôle du bot doit être **au-dessus** des rôles des membres qu’il peut bannir.

-----

## 📁 Structure du projet

```
anti-raid-bot/
├── bot.py              # Code principal
├── requirements.txt    # Dépendances Python
├── .env.example        # Exemple de fichier d'environnement
├── .gitignore          # Fichiers ignorés par Git
└── README.md           # Ce fichier
```
