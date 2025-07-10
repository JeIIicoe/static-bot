import os
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv
from handlers.handle_commands import load_commands
from handlers.handle_events import load_events

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

if not TOKEN:
    raise ValueError("DISCORD_TOKEN not set in environment")

if not GUILD_ID:
    raise ValueError("GUILD_ID not set in environment")

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
log = logging.getLogger(__name__)

intents = discord.Intents.default()
client = commands.Bot(command_prefix="!", intents=intents)

guild = discord.Object(id=int(GUILD_ID))

@client.event
async def on_ready():
    log.info(f"READY | {client.user} is online.")

    await load_commands(client)
    load_events(client)

    log.info("📦 Attempting to sync commands...")
    try:
        synced = await client.tree.sync(guild=guild)
        log.info(f"✅ Synced {len(synced)} command(s) to guild {GUILD_ID}")
        for cmd in synced:
            log.info(f"  • /{cmd.name} — {cmd.description}")
    except Exception as e:
        log.warning(f"⚠️ Failed to sync commands: {e}")

# Run the bot
client.run(TOKEN)
