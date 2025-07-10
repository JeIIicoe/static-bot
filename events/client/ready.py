# events/client/ready.py

def setup(bot):
    @bot.event
    async def on_ready():
        print(f"[EVENT] Bot is ready as {bot.user}")
