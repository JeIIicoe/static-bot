import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import requests
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from dotenv import load_dotenv
from urllib.parse import unquote

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

class Register(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_access_token(self):
        client_id = os.getenv("FFLOGS_CLIENT_ID")
        client_secret = os.getenv("FFLOGS_CLIENT_SECRET")

        response = requests.post("https://www.fflogs.com/oauth/token", data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret
        })

        response.raise_for_status()
        return response.json()["access_token"]

    def get_character_info(self, char_id):
        token = self.get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        query = """
        query ($id: Int!) {
          characterData {
            character(id: $id) {
              name
              server {
                name
              }
            }
          }
        }
        """

        response = requests.post(
            "https://www.fflogs.com/api/v2/client",
            headers=headers,
            json={"query": query, "variables": {"id": char_id}}
        )

        response.raise_for_status()
        data = response.json()
        char = data["data"]["characterData"]["character"]
        if not char:
            raise ValueError("Character not found")

        return char["name"], char["server"]["name"]

    def get_character_info_from_url(self, region, server, name):
        token = self.get_access_token()
        transport = RequestsHTTPTransport(
            url="https://www.fflogs.com/api/v2/client",
            headers={"Authorization": f"Bearer {token}"},
            use_json=True
        )

        client = Client(transport=transport, fetch_schema_from_transport=True)

        query = gql("""
        query ($name: String!, $server: String!, $region: String!) {
          characterData {
            character(name: $name, serverSlug: $server, serverRegion: $region) {
              id
              name
              server { name }
            }
          }
        }
        """)

        variables = {"name": name, "server": server, "region": region.upper()}
        result = client.execute(query, variable_values=variables)
        char = result["characterData"]["character"]
        if not char:
            raise ValueError("Character not found by name")

        return char["id"], char["name"], char["server"]["name"]

    @app_commands.command(name="register", description="Register your character with job and FFLogs link.")
    @app_commands.describe(job="Your main job (e.g. Black Mage)", fflogs_link="Link to your FFLogs character profile")
    async def register(self, interaction: discord.Interaction, job: str, fflogs_link: str):
        try:
            await interaction.response.defer(thinking=True)

            if fflogs_link.startswith("https://www.fflogs.com/character/id/"):
                char_id = int(fflogs_link.split("/")[-1])
                print(f"[DEBUG] Extracted FFLogs character ID: {char_id}")
                name, server = self.get_character_info(char_id)
            elif fflogs_link.startswith("https://www.fflogs.com/character/"):
                parts = fflogs_link.split("/")
                if len(parts) < 7:
                    await interaction.followup.send("❌ FFLogs link seems malformed. Expected format: /character/region/server/name")
                    return

                region = parts[4]
                server = parts[5]
                char_name = unquote(parts[6])
                print(f"[DEBUG] Extracted character: {char_name} on {server} ({region})")
                char_id, name, server = self.get_character_info_from_url(region, server, char_name)
                
            else:
                await interaction.followup.send("❌ Invalid FFLogs link format.")
                return

            print(f"[DEBUG] Retrieved character: {name} on {server}")

            os.makedirs(BASE_DIR, exist_ok=True)
            if not os.path.exists(USERS_FILE):
                with open(USERS_FILE, "w") as f:
                    f.write("{}")

            with open(USERS_FILE, "r") as f:
                raw = f.read().strip()
                users = json.loads(raw) if raw else {}
                if not raw:
                    print("[DEBUG] users.json was empty. Starting fresh.")

            users[str(interaction.user.id)] = {
                "character_name": name,
                "server": server,
                "job": job,
                "fflogs": fflogs_link,
                "character_id": char_id
            }

            with open(USERS_FILE, "w") as f:
                json.dump(users, f, indent=2)
                print(f"[DEBUG] Stored user data for {interaction.user.id} at {USERS_FILE}")

            await interaction.followup.send(
                f"✅ Registered **{name}** on **{server}** as **{job}**!",
                ephemeral=True
            )

        except Exception as e:
            print(f"[ERROR] Exception during registration: {e}")
            try:
                await interaction.followup.send(
                    "❌ Something went wrong while registering. Please try again later.",
                    ephemeral=True
                )
            except discord.NotFound:
                print("[ERROR] Could not send followup — interaction expired.")

    async def cog_load(self):
        guild = discord.Object(id=int(os.getenv("GUILD_ID")))
        self.bot.tree.add_command(self.register, guild=guild)


async def setup(bot):
    await bot.add_cog(Register(bot))
