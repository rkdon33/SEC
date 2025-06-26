import discord
from discord.ext import commands
from discord import app_commands
import json
import os

LOG_CHANNELS_FILE = "log_channels.json"

def save_log_channels(log_channels):
    with open(LOG_CHANNELS_FILE, "w") as f:
        json.dump({str(k): v for k, v in log_channels.items()}, f)

def load_log_channels():
    if not os.path.exists(LOG_CHANNELS_FILE):
        return {}
    with open(LOG_CHANNELS_FILE, "r") as f:
        return {int(k): v for k, v in json.load(f).items()}

# Define the group ONCE at the module level
logschannel_group = app_commands.Group(
    name="logschannel",
    description="Log channel management"
)

@logschannel_group.command(name="create", description="Create or set the log channel for this server as #logs-secureaura")
@app_commands.guild_only()
@app_commands.default_permissions(administrator=True)
async def logschannel_create(interaction: discord.Interaction):
    guild = interaction.guild
    bot_member = guild.me
    owner = guild.owner

    log_channel = discord.utils.get(guild.text_channels, name="logs-secureaura")
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        owner: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        bot_member: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }

    if not log_channel:
        log_channel = await guild.create_text_channel("logs-secureaura", overwrites=overwrites, reason="Logs channel for bot security and moderation.")
        await interaction.response.send_message(f"Created and locked log channel: {log_channel.mention}", ephemeral=True)
    else:
        await log_channel.edit(overwrites=overwrites)
        await interaction.response.send_message(f"Log channel set and locked: {log_channel.mention}", ephemeral=True)

    # Save to persistent file
    if not hasattr(interaction.client, "log_channels"):
        interaction.client.log_channels = load_log_channels()
    interaction.client.log_channels[guild.id] = log_channel.id
    save_log_channels(interaction.client.log_channels)

class LogChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not hasattr(bot, "log_channels"):
            bot.log_channels = load_log_channels()

    # Optionally, block prefix command and respond with a hint
    @commands.command(name="logs")
    async def logs_prefix(self, ctx):
        await ctx.send("This command is only available as a slash command: `/logschannel create`.", delete_after=5)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.content.strip().lower().startswith("?logs"):
            try:
                await message.channel.send("Please use the `/logschannel create` slash command for log channel setup.", delete_after=5)
            except Exception:
                pass

    async def cog_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        if isinstance(error, discord.app_commands.errors.MissingPermissions):
            await interaction.response.send_message("You need Administrator permissions to use this command.", ephemeral=True)
        else:
            await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)

    async def cog_load(self):
        # Only add the group if it's not already added
        # But ideally, you should let discord.py handle registration automatically
        # The following is usually NOT necessary if you define the group at the module level!
        if not any(cmd.name == logschannel_group.name for cmd in self.bot.tree.get_commands()):
            self.bot.tree.add_command(logschannel_group)

async def setup(bot):
    await bot.add_cog(LogChannel(bot))