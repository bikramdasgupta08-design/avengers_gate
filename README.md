# Avengers Mate 🛡️

A simple tournament helper bot for one Discord server, built with Python + discord.py.

## What it can do

| Command | What it does |
|---|---|
| `/tourney rules` | Pick a channel, write up to 5 rules, and post a clean rules embed. That channel also becomes the bot's ping channel. |
| `/trole` | Pick the role that `/tmembers` will assign. Defaults to Tournament Participants. |
| `/tmembers` | Pick a member and instantly give them the active tournament role. |
| `/alert` | Write a tournament name + message, pick up to 2 roles to ping and up to 10 members. Everyone selected gets a DM with a "View announcement" button, and a public message really pings the role(s). Run it again for the next batch of 10. |
| `/timer` | Enter an IST date (`DD/MM/YYYY`) and time (`HH:MM`), plus who to ping. When it rings, the bot pings them in the ping channel. |

Only people with the admin role can run these commands, and only inside the official server.

> **Why a public ping too?** Discord does not deliver real `@role` notifications inside DMs. So `/alert` sends the DM *and* posts one public message that genuinely pings the role. The DM button links straight to that message.

## 1. Local setup (optional, for testing)

```bash
cd avengers-mate
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Open `.env` and replace `your_bot_token_here` with your bot token from the Discord Developer Portal. Then:

```bash
python bot.py
```

You should see `Logged in as Avengers Mate#...`.

## 2. GitHub

```bash
git init
git add .
git commit -m "Avengers Mate bot"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

Make sure `.env` is **not** committed. Add a `.gitignore` with:

```
.env
venv/
__pycache__/
*.pyc
```

## 3. Render deployment

1. Go to [Render Dashboard](https://dashboard.render.com) → **New + → Web Service**.
2. Connect your GitHub repo.
3. Settings:
   - **Runtime:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
   - **Plan:** Free (or paid if you want timers to never miss)
4. Add environment variables:

   | Key | Value |
   |---|---|
   | `DISCORD_TOKEN` | Your bot token (keep this secret) |
   | `GUILD_ID` | `1557035700287836170` |
   | `ADMIN_ROLE_ID` | `1003156847475314750` |
   | `PARTICIPANT_ROLE_ID` | `1573531215129219182` |

   (The `render.yaml` file in this folder already sets the IDs for you if you use a Blueprint.)

5. Create the service. Render will run the bot and keep port `10000` (or its own `PORT`) alive via a tiny `/health` page.

## 4. Invite the bot

In Discord Developer Portal → **OAuth2 → URL Generator**:
- Scopes: `bot`, `applications.commands`
- Permissions: **Send Messages**, **Embed Links**, **Manage Roles**, **Mention @everyone, users and roles**

Open the generated URL and invite it to the official server.

**Important:** In **Server Settings → Roles**, drag the bot's role **above** "Tournament Participants". A bot can only assign roles lower than its own.

No privileged gateway intents (Presence / Server Members / Message Content) need to be enabled in the Developer Portal.

## 5. First-time use

1. Use `/tourney rules` once in your rules channel. This also tells the bot where to post pings.
2. Use `/trole` if you ever want to change the role given by `/tmembers`.
3. Use `/tmembers` to add participants.
4. On tournament day, use `/alert` (max 10 members per use).
5. Use `/timer` for IST reminders.

## Good to know

- Slash commands sync automatically to the official server on every start, so you don't need a separate deploy command.
- State is intentionally in-memory: after a Render restart, `/trole` goes back to the default participants role, the ping channel is forgotten until you run `/tourney rules` again, and pending timers are cleared. Set them again after a restart.
- On Render's free plan the service can sleep when idle. A keep-alive ping (e.g. UptimeRobot hitting your Render URL every few minutes) helps, but a paid plan is the only guarantee for alarms that must fire exactly on time.
- If a member's DMs are closed, `/alert` reports how many DMs failed — the public role ping still goes through.
