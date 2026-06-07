# DiscordBot

A self-hosted Discord bot built with Discord.py, Wavelink, and Lavalink.

## Features

### Music

* YouTube Music search and playback
* Playlist support
* Queue management
* Interactive player controls
* Previous track support
* Shuffle, loop, skip, stop
* Lavalink-powered audio streaming

### Quotes

* Save quotes to a SQLite database
* Category-based quote retrieval
* Random quote responses
* Raw message trigger support

### Utility Commands

* Dice rolling
* Help commands
* Server configuration

### Markov Brain (Optional)

* Learns from server messages
* Generates Markov-chain text
* Per-server training
* Channel locking support
* Persistent memory storage

---

# Requirements

* Python 3.11+
* Java 17+ (for Lavalink)
* Docker and Docker Compose (recommended)

---

# Installation

## Clone Repository

```bash
git clone https://github.com/UncleanlyCleric/DiscordBot.git
cd DiscordBot
```

---

## Create Environment

```bash
python -m venv venv
source venv/bin/activate
```

Windows:

```powershell
venv\Scripts\activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Discord Bot Setup

## Create Bot Application

1. Open Discord Developer Portal
2. Create New Application
3. Create Bot
4. Copy Bot Token

Enable:

* Message Content Intent
* Server Members Intent (optional)
* Presence Intent (optional)

---

## Invite Bot

Use the generated OAuth URL with:

* bot
* applications.commands

permissions.

---

# Environment Variables

Create a `.env` file:

```env
DISCORD_TOKEN=YOUR_TOKEN_HERE

LAVALINK_URI=http://lavalink:2333
LAVALINK_PASSWORD=youshallnotpass
```

---

# Lavalink Setup

The repository includes:

```text
lavalink/
├── application.yaml
└── Lavalink.jar

plugins/
├── lavasrc.jar
└── youtube.jar
```

These provide:

* YouTube support
* YouTube Music support
* Additional source resolution

---

## Docker Start

```bash
docker compose up -d
```

View logs:

```bash
docker compose logs -f
```

Rebuild:

```bash
docker compose up --build -d
```

Stop:

```bash
docker compose down
```

---

# Running Without Docker

Start Lavalink:

```bash
java -jar lavalink/Lavalink.jar
```

Start bot:

```bash
python bot.py
```

---

# Commands

## Music

```text
/play <song>
/playlist <url>
/skip
/stop
/pause
/resume
/queue
```

---

## Quotes

Examples:

```text
!yes
!no
```

Retrieve random quotes from configured categories.

---

## Configuration

View current settings:

```text
/config
```

Set DJ role:

```text
/ set_dj_role
```

Set Markov channel:

```text
/ set_markov_channel
```

Enable/disable Markov learning:

```text
/ toggle_markov_training
```

---

# Data Storage

## SQLite

Quote data:

```text
data/quotes.db
```

## Markov

Per-guild brain files:

```text
data/markov_<guild_id>.json.gz
```

---

# Project Structure

```text
DiscordBot/
├── bot.py
├── cogs/
│   ├── admin.py
│   ├── config.py
│   ├── dice.py
│   ├── help.py
│   ├── logger.py
│   ├── markov.py
│   ├── music.py
│   └── quotes.py
│
├── music/
│   ├── guild_music.py
│   ├── manager.py
│   ├── playlist_converter.py
│   └── utils.py
│
├── ui/
│   └── player.py
│
├── utils/
│   ├── config.py
│   ├── db.py
│   ├── logger.py
│   ├── quotes_store.py
│   └── resolver.py
│
├── data/
├── lavalink/
├── plugins/
└── docker-compose.yml
```

---

# Notes

* Lavalink must be running before music playback will function.
* Markov functionality is optional and can be disabled entirely.
* Music playback uses Wavelink and Lavalink rather than Discord voice clients directly.
* Data is persisted locally and survives restarts.

---

# License

Personal project. Modify and use as desired.
