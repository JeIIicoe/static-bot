import random
import os
import discord
from discord.ext import commands
from discord import app_commands

class Hello(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name="hello", description="Say hello!")
    async def hello(self, interaction: discord.Interaction):
        greetings = [
            "Meow :3",
            "I hope you're not getting paid to type that.",
            "I'll say hello back when you get me that 100 parse.",
            "You're fired.",
            "This could've been an email.",
            "Today's kids don't wanna raid from the office...",
            "Did you forget raid food again? Why are you pinging me.",
            "Helen from HR will help you, I'm too busy.",
            "Get back to work those logs won't run themselves!!",
            "I'd get back to raiding if I were you. I've seen your XIVAnalysis."
        ]
        await interaction.response.send_message(random.choice(greetings))

    async def cog_load(self):
        guild = discord.Object(id=int(self.client.guild_id))
        self.client.tree.add_command(self.hello, guild=guild)

async def setup(client):
    client.guild_id = os.getenv("GUILD_ID")
    await client.add_cog(Hello(client))
