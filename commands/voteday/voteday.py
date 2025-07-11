import os
import json
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
SAVED_DAYS_FILE = os.path.join(DATA_DIR, "saved_days.json")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

RAID_ROLE_ID = 1350916461467664535

class VoteView(discord.ui.View):
    def __init__(self, days, user_data, vote_data, save_callback, disable_buttons=False):
        super().__init__(timeout=None)
        self.days = days
        self.user_data = user_data
        self.vote_data = vote_data
        self.save_callback = save_callback

        for day in self.days:
            self.add_item(self.create_button(day, disable_buttons))

    def create_button(self, day, disable):
        class DayButton(discord.ui.Button):
            def __init__(self_inner):
                super().__init__(label=day, style=discord.ButtonStyle.primary, disabled=disable)

            async def callback(self_inner, interaction: discord.Interaction):
                user_id = str(interaction.user.id)
                if user_id not in self.user_data:
                    await interaction.response.send_message("❌ You must register before voting.", ephemeral=True)
                    return

                self.vote_data.setdefault(day, [])
                if user_id in self.vote_data[day]:
                    self.vote_data[day].remove(user_id)
                else:
                    self.vote_data[day].append(user_id)

                self.save_callback()

                embed = generate_embed(self.user_data, self.vote_data)

                all_voters = set()
                for votes in self.vote_data.values():
                    all_voters.update(votes)
                if all_voters == set(self.user_data.keys()):
                    # All registered users have voted
                    chosen_day = max(self.vote_data.items(), key=lambda item: len(item[1]))[0]
                    embed.set_footer(text=f"✅ All votes submitted. Raid scheduled: {chosen_day}")
                    await interaction.message.channel.send(f"<@&{RAID_ROLE_ID}> Raid scheduled for **{chosen_day}**! 📅")
                    view = VoteView(self.days, self.user_data, self.vote_data, self.save_callback, disable_buttons=True)
                    await interaction.response.edit_message(embed=embed, view=view)
                else:
                    await interaction.response.edit_message(embed=embed, view=self)

        return DayButton()

def generate_embed(user_data, vote_data):
    embed = discord.Embed(title="🗳️ Raid Day Voting", color=discord.Color.blurple())
    embed.set_footer(text="Click buttons to toggle votes. You may vote for multiple days.")

    registered_ids = set(user_data.keys())
    all_voters = set()

    for day, votes in vote_data.items():
        names = [f"💙 {user_data[uid]['character_name']}" for uid in votes if uid in user_data]
        all_voters.update(votes)
        embed.add_field(name=day, value="\n".join(names) or "No votes", inline=False)

    non_voters = [f"🔴 {user_data[uid]['character_name']}" for uid in registered_ids - all_voters]
    embed.add_field(name="❌ Not Voted Yet", value="\n".join(non_voters) or "None", inline=False)
    return embed

class VoteDay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="voteday", description="Start a vote for best raid day (next 7 days).")
    async def voteday(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        try:
            with open(USERS_FILE, "r") as f:
                user_data = json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load users.json: {e}")
            await interaction.followup.send("❌ Couldn't load registered users.")
            return

        today = datetime.utcnow()
        days = [(today + timedelta(days=i)).strftime("%A (%Y-%m-%d)") for i in range(7)]

        if os.path.exists(SAVED_DAYS_FILE):
            with open(SAVED_DAYS_FILE, "r") as f:
                vote_data = json.load(f)
        else:
            vote_data = {day: [] for day in days}

        def save_votes():
            with open(SAVED_DAYS_FILE, "w") as f:
                json.dump(vote_data, f, indent=2)

        embed = generate_embed(user_data, vote_data)
        view = VoteView(days, user_data, vote_data, save_votes)
        await interaction.followup.send(embed=embed, view=view)

    async def cog_load(self):
        guild = discord.Object(id=int(os.getenv("GUILD_ID")))
        self.bot.tree.add_command(self.voteday, guild=guild)

async def setup(bot):
    await bot.add_cog(VoteDay(bot))
