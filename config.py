"""Configuration + tiny in-memory state for Avengers Mate."""

import os

from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "1557035700287836170"))
ADMIN_ROLE_ID = int(os.getenv("ADMIN_ROLE_ID", "1003156847475314750"))
PARTICIPANT_ROLE_ID = int(os.getenv("PARTICIPANT_ROLE_ID", "1573531215129219182"))
PORT = int(os.getenv("PORT", "10000"))

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing. Copy .env.example to .env and fill it in.")


# Everything here resets when the bot restarts. That is intentional: no database, no setup.
state = {
    "tourney_role_id": PARTICIPANT_ROLE_ID,
    "announcement_channel_id": None,  # set automatically by /tourney rules
    "timers": [],                     # running asyncio tasks
}
