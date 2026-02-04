# Discord Scoreboard Bot

Discord Bot zur Anzeige von Spielerstatistiken für Hell Let Loose Server mit CRCON Integration.

## Features

- 📊 Automatisches Tracking von Spielerstatistiken (Kills, Deaths, K/D, Streaks, etc.)
- 🔄 Automatisches monatliches Reset der Statistiken
- 📈 Multi-Server Support
- 🎯 Mehrere Ranking-Kategorien

## Installation auf Linux Server mit PM2

### Voraussetzungen

```bash
# Python 3.11+ installieren
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Node.js und PM2 installieren
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g pm2
```

### Setup

1. **Repository klonen:**
```bash
git clone <your-repo-url>
cd Scoreboard
```

2. **Python Virtual Environment erstellen:**
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Dependencies installieren:**
```bash
pip install -r requirements.txt
```

4. **.env Datei erstellen:**
```bash
nano .env
```

Füge folgende Variablen ein:
```env
DISCORD_BOT_TOKEN=your_bot_token
DISCORD_CHANNEL_ID=your_channel_id
CRCON_TOKEN=your_crcon_token
CRCON_URL_SERVER1=https://your-server1-url
# Optional:
# CRCON_URL_SERVER2=https://your-server2-url
# CRCON_URL_SERVER3=https://your-server3-url
```

5. **Logs Verzeichnis erstellen:**
```bash
mkdir -p logs
```

6. **Mit PM2 starten:**
```bash
# Im Virtual Environment interpreter verwenden
pm2 start ecosystem.config.js --interpreter ./venv/bin/python3

# ODER global installiert:
pm2 start ecosystem.config.js
```

### PM2 Befehle

```bash
# Bot starten
pm2 start ecosystem.config.js

# Bot stoppen
pm2 stop discord-scoreboard-bot

# Bot neustarten
pm2 restart discord-scoreboard-bot

# Logs anzeigen
pm2 logs discord-scoreboard-bot

# Status anzeigen
pm2 status

# Bot aus PM2 entfernen
pm2 delete discord-scoreboard-bot

# PM2 beim Systemstart automatisch starten
pm2 startup
pm2 save
```

## Struktur

```
.
├── main.py                 # Haupt Bot-Datei
├── requirements.txt        # Python Dependencies
├── ecosystem.config.js     # PM2 Konfiguration
├── .env                    # Umgebungsvariablen (nicht in Git)
├── data/                   # Daten-Verzeichnis
│   ├── monthly_stats.json
│   ├── multi_ranking_message_ids.json
│   └── last_log_ids.json
└── logs/                   # Log-Dateien (PM2)
```

## Optimierungen für PM2

- ✅ Graceful shutdown bei SIGTERM/SIGINT
- ✅ Proper logging mit Python logging module
- ✅ Error handling und recovery
- ✅ Automatischer Neustart bei Fehlern
- ✅ Memory limit (500MB)
- ✅ Strukturiertes Log-Management
