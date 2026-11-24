# Avengers Mate 🛡️

A simple tournament helper bot for one Discord server, built with Python + discord.py.

## What it can do

| Command | What it does |
|---|---|
| `/tourney rules` | Pick a channel, write up to 5 rules, and post a clean rules embed. That channel also becomes the bot's ping channel. |
| `/trole` | Pick the role that `/tmembers` will assign. Defaults to Tournament Participants. |
| `/tmembers` | Pick a member and instantly give them the active tournament role. |
| `/treset` | Remove the active tournament role from every member who has it (full tournament reset). |
| `/alert` | Write a tournament name + message, pick up to 2 roles to ping and up to 10 members. Everyone selected gets a DM with a "View announcement" button, and a public message really pings the role(s). Run it again for the next batch of 10. |
| `/timer` | Enter an IST date (`DD/MM/YYYY`) and time (`HH:MM`), plus who to ping. When it rings, the bot pings them in the ping channel. |
| `/twhoami` | Diagnostic: shows the user ID, roles, Administrator permission, and the admin role the bot is checking. |

Only inside the official server, and only for the admin role, people with Administrator permission, or the server owner.

> **Why a public ping too?** Discord does not deliver real `@role` notifications inside DMs. So `/alert` sends the DM *and* posts one public message that genuinely pings the role. The DM button links straight to that message.

## 1. Local setup (optional, for testing)

```bash
cd avengers-mate
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Set `DISCORD_TOKEN`, `GUILD_ID`, `ADMIN_ROLE_ID`, and `PARTICIPANT_ROLE_ID` as environment variables (or in a local `.env` file you create yourself, which is gitignored). `GUILD_ID`, `ADMIN_ROLE_ID`, and `PARTICIPANT_ROLE_ID` already have defaults in `config.py`, so only the token is strictly required. Then:

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

   You can set these manually in Render's dashboard, or use the `render.yaml` Blueprint in this folder to prefill the IDs.

   If the bot says `unknown-role`, the `ADMIN_ROLE_ID` doesn't match a real role in your server. Turn on Discord Developer Mode, right-click the admin role → **Copy ID**, and put that value in Render. Then restart the service.

5. Create the service. Render will run the bot and keep port `10000` (or its own `PORT`) alive via a tiny `/health` page.

## 4. Invite the bot

In Discord Developer Portal → **OAuth2 → URL Generator**:
- Scopes: `bot`, `applications.commands`
- Permissions: **Send Messages**, **Embed Links**, **Manage Roles**, **Mention @everyone, users and roles**

Open the generated URL and invite it to the official server.

**Important:** In **Server Settings → Roles**, drag the bot's role **above** "Tournament Participants". A bot can only assign roles lower than its own.

**Required:** In Developer Portal → **Bot → Privileged Gateway Intents**, enable **Server Members Intent**. `/treset` needs it to scan all members and remove the role. Presence and Message Content intents are not needed. After toggling it, restart the Render service so the bot reconnects with the new intent.

## 5. First-time use

1. Use `/tourney rules` once in your rules channel. This also tells the bot where to post pings.
2. Use `/trole` if you ever want to change the role given by `/tmembers`.
3. Use `/tmembers` to add participants.
4. On tournament day, use `/alert` (max 10 members per use).
5. Use `/timer` for IST reminders.
6. After the tournament, use `/treset` to clear the role from everyone.

## Good to know

- All confirmations, errors, and public announcements are sent as embeds. Role/user pings stay in the message text so Discord still delivers real notifications.
- Slash commands sync automatically to the official server on every start, so you don't need a separate deploy command.
- State is intentionally in-memory: after a Render restart, `/trole` goes back to the default participants role, the ping channel is forgotten until you run `/tourney rules` again, and pending timers are cleared. Set them again after a restart.
- On Render's free plan the service can sleep when idle. A keep-alive ping (e.g. UptimeRobot hitting your Render URL every few minutes) helps, but a paid plan is the only guarantee for alarms that must fire exactly on time.
- If a member's DMs are closed, `/alert` reports how many DMs failed — the public role ping still goes through.
