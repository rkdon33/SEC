import os
import discord
from discord.ext import commands

TOKEN = os.environ['DISCORD_TOKEN']

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="?", intents=intents, case_insensitive=True)
bot.remove_command('help')

# Persistent log channel mapping loaded before extensions
import json
import os as _os

LOG_CHANNELS_FILE = "log_channels.json"

def save_log_channels(log_channels):
    with open(LOG_CHANNELS_FILE, "w") as f:
        json.dump({str(k): v for k, v in log_channels.items()}, f)

def load_log_channels():
    if not _os.path.exists(LOG_CHANNELS_FILE):
        return {}
    with open(LOG_CHANNELS_FILE, "r") as f:
        return {int(k): v for k, v in json.load(f).items()}

bot.log_channels = load_log_channels()

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="Moderating the server!"))
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Error syncing commands: {e}")

# Load cogs
initial_extensions = [
    'cogs.security_feature',
    'cogs.moderation',
    'cogs.msg',
    'cogs.log_channel',
    'cogs.invite_log',
    'cogs.premium_security',
    'cogs.greet_pannel',
    'cogs.help'
]

async def load_extensions():
    for ext in initial_extensions:
        await bot.load_extension(ext)

async def main():
    await load_extensions()
    await bot.start(TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())