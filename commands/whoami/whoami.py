import os
import json
import discord
from discord.ext import commands
from discord import app_commands

from fflogs.utils import (
    get_parses_for_fights,
    get_access_token,
    get_graphql_client
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_FILE = os.path.join(BASE_DIR, "data", "users.json")

CURRENT_SAVAGE_ENCOUNTER_IDS = {
    97: "Dancing Green",
    98: "Sugar Riot",
    99: "Brute Abominator",
    100: "Howling Blade",
}

PREVIOUS_SAVAGE_ENCOUNTER_IDS = {
    93: "Black Cat",
    94: "Honey B. Lovely",
    95: "Brute Bomber",
    96: "Wicked Thunder",
}

ULTIMATE_ENCOUNTER_IDS = {
    1079: "Futures Rewritten",                       # zone 65 (Dawntrail)
    1065: "Dragonsong's Reprise",                    # zone 45 (Endwalker)
    1076: "Dragonsong's Reprise",                    # zone 59 (Dawntrail)
    1068: "The Omega Protocol",                      # zone 53 (Endwalker)
    1077: "The Omega Protocol",                      # zone 59 (Dawntrail)
    1060: "The Unending Coil of Bahamut",            # zone 43
    1073: "The Unending Coil of Bahamut",            # zone 59
    1061: "The Weapon's Refrain",                    # zone 43
    1074: "The Weapon's Refrain",                    # zone 59
    1062: "The Epic of Alexander",                   # zone 43
    1075: "The Epic of Alexander",                   # zone 59
}

class WhoAmI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="whoami", description="View your character and FFLogs data.")
    async def whoami(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        user_id = str(interaction.user.id)

        if not os.path.exists(DATA_FILE):
            await interaction.followup.send("❌ No data file found. Please register first.")
            return

        with open(DATA_FILE, "r") as f:
            users = json.load(f)

        if user_id not in users:
            await interaction.followup.send("❌ You're not registered yet. Please use `/register` first.")
            return

        user_data = users[user_id]
        character_name = user_data["character_name"]
        server = user_data["server"]
        job = user_data["job"]
        fflogs_url = user_data["fflogs"]
        character_id = user_data["character_id"]

        embed = discord.Embed(
            title=f"{character_name} — {job}",
            description=f"Server: **{server}**\n[View on FFLogs]({fflogs_url})",
            color=discord.Color.purple()
        )

        try:
            token = get_access_token()
            client = get_graphql_client(token)
            all_parses = get_parses_for_fights(client, character_id)
        except Exception as e:
            print(f"[ERROR] Failed to fetch parses: {e}")
            await interaction.followup.send("❌ Failed to retrieve FFLogs data.")
            return

        # Helper function for embedding parse data
        def add_parses_to_embed(label: str, ids: dict):
            embed.add_field(name=label, value="\u200b", inline=False)
            for eid, name in ids.items():
                data = all_parses.get(eid)
                if data and data.get("percentile") is not None:
                    pct = int(data['percentile'])
                    embed.add_field(
                        name=name,
                        value=f"**{pct}%** (Spec: {data['spec']}, Kills: {data['kills']})",
                        inline=False
                    )
                else:
                    embed.add_field(name=name, value="No data", inline=False)

        def add_deduplicated_ultimates_to_embed():
            embed.add_field(name="Ultimates", value="\u200b", inline=False)
            aggregated = {}

            for eid, name in ULTIMATE_ENCOUNTER_IDS.items():
                data = all_parses.get(eid)
                if not data:
                    continue

                if name not in aggregated:
                    aggregated[name] = {
                        "percentile": data.get("percentile") or 0,
                        "kills": data.get("kills") or 0,
                        "spec": data.get("spec") or "Unknown"
                    }
                else:
                    # Sum kills, keep highest percentile
                    aggregated[name]["kills"] += data.get("kills") or 0
                    if (data.get("percentile") or 0) > aggregated[name]["percentile"]:
                        aggregated[name]["percentile"] = data.get("percentile")
                        aggregated[name]["spec"] = data.get("spec") or "Unknown"

            for name in sorted(set(ULTIMATE_ENCOUNTER_IDS.values())):
                if name in aggregated:
                    info = aggregated[name]
                    pct = int(info["percentile"])
                    embed.add_field(
                        name=name,
                        value=f"**{pct}%** (Spec: {info['spec']}, Kills: {info['kills']})",
                        inline=False
                    )
                else:
                    embed.add_field(name=name, value="No data", inline=False)

        # Add categories
        add_parses_to_embed("Current Savage Tier", CURRENT_SAVAGE_ENCOUNTER_IDS)
        add_parses_to_embed("Previous Savage Tier", PREVIOUS_SAVAGE_ENCOUNTER_IDS)
        add_deduplicated_ultimates_to_embed()

        await interaction.followup.send(embed=embed, ephemeral=True)

    async def cog_load(self):
        guild = discord.Object(id=int(os.getenv("GUILD_ID")))
        self.bot.tree.add_command(self.whoami, guild=guild)


async def setup(bot):
    await bot.add_cog(WhoAmI(bot))