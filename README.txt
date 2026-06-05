Docker Setup:

apt update && apt upgrade -y

apt install -y ca-certificates curl gnupg

install -m 0755 -d /etc/apt/keyrings

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
  > /etc/apt/sources.list.d/docker.list

apt update

apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin



Upload:

mkdir athene-bot

cd athene-bot


Project Structure:

athene-bot/
 ├── bot.py
 ├── cogs/
 ├── utils/
 ├── requirements.txt
 ├── Dockerfile
 ├── docker-compose.yml
 └── .env



 env:

 DISCORD_TOKEN=your_discord_bot_token



 docker-compose.yaml:

 version: "3.9"

services:

  lavalink:
   version: "3.9"

services:

  lavalink:
    image: fredboat/lavalink:latest
    container_name: lavalink
    environment:
      - LAVALINK_SERVER_PASSWORD=youshallnotpass
    ports:
      - "2333:2333"

    restart: unless-stopped

  bot:
    build: .
    container_name: discord-bot
    depends_on:
      - lavalink

    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - LAVALINK_URI=http://lavalink:2333
      - LAVALINK_PASSWORD=youshallnotpass

    
  bot:
    build: .
    container_name: discord-bot
    depends_on:
      - lavalink

    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - LAVALINK_URI=http://lavalink:2333
      - LAVALINK_PASSWORD=youshallnotpass

    restart: unless-stopped



Start up:

docker compose up --build -d