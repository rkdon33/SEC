import discord
from discord.ext import commands
from discord import app_commands
import random
from collections import defaultdict
from datetime import datetime

SUPPORT_LINK = "https://discord.gg/ERYMCnhWjG"

def get_status_emoji(val):
    return '☑️' if val else '❎'

class SecurityFeature(commands.Cog):
    antinuke_group = app_commands.Group(name="antinuke", description="Enable/disable anti-nuke features")
    antibotadd_group = app_commands.Group(name="antibotadd", description="Enable/disable anti-bot-add features")
    antiraid_group = app_commands.Group(name="antiraid", description="Enable/disable anti-raid features")
    antiall_group = app_commands.Group(name="antiall", description="Enable/disable all anti features")

    def __init__(self, bot):
        self.bot = bot
        self.warn_counts = defaultdict(int)
        self.settings = defaultdict(lambda: {
            "antinuke": True,
            "antibotadd": True,
            "antiraid": True
        })
        self.recent_joins = defaultdict(list)
        self.raid_threshold = 5
        self.raid_interval = 10

    # ----------- SLASH COMMANDS FOR TOGGLING -----------
    @antinuke_group.command(name="enable", description="Enable anti-nuke protections")
    async def antinuke_enable(self, interaction: discord.Interaction):
        g = interaction.guild_id
        self.settings[g]["antinuke"] = True
        embed = self._status_embed(g, "AntiNuke enabled.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @antinuke_group.command(name="disable", description="Disable anti-nuke protections")
    async def antinuke_disable(self, interaction: discord.Interaction):
        g = interaction.guild_id
        self.settings[g]["antinuke"] = False
        embed = self._status_embed(g, "AntiNuke disabled.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @antibotadd_group.command(name="enable", description="Enable anti-bot-add protections")
    async def antibotadd_enable(self, interaction: discord.Interaction):
        g = interaction.guild_id
        self.settings[g]["antibotadd"] = True
        embed = self._status_embed(g, "AntiBotadd enabled.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @antibotadd_group.command(name="disable", description="Disable anti-bot-add protections")
    async def antibotadd_disable(self, interaction: discord.Interaction):
        g = interaction.guild_id
        self.settings[g]["antibotadd"] = False
        embed = self._status_embed(g, "AntiBotadd disabled.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @antiraid_group.command(name="enable", description="Enable anti-raid protections")
    async def antiraid_enable(self, interaction: discord.Interaction):
        g = interaction.guild_id
        self.settings[g]["antiraid"] = True
        embed = self._status_embed(g, "AntiRaid enabled.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @antiraid_group.command(name="disable", description="Disable anti-raid protections")
    async def antiraid_disable(self, interaction: discord.Interaction):
        g = interaction.guild_id
        self.settings[g]["antiraid"] = False
        embed = self._status_embed(g, "AntiRaid disabled.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @antiall_group.command(name="enable", description="Enable all anti features")
    async def antiall_enable(self, interaction: discord.Interaction):
        g = interaction.guild_id
        self.settings[g] = {
            "antinuke": True,
            "antibotadd": True,
            "antiraid": True
        }
        embed = self._status_embed(g, "All features enabled.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @antiall_group.command(name="disable", description="Disable all anti features")
    async def antiall_disable(self, interaction: discord.Interaction):
        g = interaction.guild_id
        self.settings[g] = {
            "antinuke": False,
            "antibotadd": False,
            "antiraid": False
        }
        embed = self._status_embed(g, "All features disabled.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    def _status_embed(self, guild_id, msg):
        st = self.settings[guild_id]
        # Horizontal format
        status_line = (
            f"AntiNuke {get_status_emoji(st['antinuke'])} | "
            f"AntiBotadd {get_status_emoji(st['antibotadd'])} | "
            f"AntiRaid {get_status_emoji(st['antiraid'])}"
        )
        embed = discord.Embed(
            title="SecureAura Anti Features Status",
            description=f"{msg}\n\n{status_line}",
            color=discord.Color.blue()
        )
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Support Server", url=SUPPORT_LINK, style=discord.ButtonStyle.link))
        embed.set_footer(text="Use the slash commands to manage features.")
        return embed

    # ----------- WELCOME EMBED ON BOT JOIN -----------
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        adder = None
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.bot_add):
                adder = entry.user
        except Exception:
            adder = guild.owner

        embed = discord.Embed(
            title="AntiNuke Features Enabled ☑️",
            description=(
                f"Hey, {adder.mention if adder else 'there'}, thanks for using our bot in your server.\n"
                "- Secure Aura is the most powerful nuke controller bot of discord."
            ),
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Support Server", url=SUPPORT_LINK, style=discord.ButtonStyle.link))

        if adder:
            try:
                await adder.send(embed=embed, view=view)
            except Exception:
                pass

        text_channels = [c for c in guild.text_channels if c.permissions_for(guild.me).send_messages]
        if text_channels:
            channel = random.choice(text_channels)
            await channel.send(embed=embed, view=view)

    # ----------- ANTI-NUKE: CHANNEL CREATE/DELETE/BAN -----------
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if not self.settings[channel.guild.id]["antinuke"]:
            return
        await self._handle_channel_event(channel, "create")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if not self.settings[channel.guild.id]["antinuke"]:
            return
        await self._handle_channel_event(channel, "delete")

    async def _handle_channel_event(self, channel, action):
        guild = channel.guild
        entry = None
        try:
            entry = (await guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create if action == "create" else discord.AuditLogAction.channel_delete).flatten())[0]
        except Exception:
            return
        user = entry.user
        bot_member = guild.me
        if user.top_role >= bot_member.top_role:
            return

        key = (guild.id, user.id)
        self.warn_counts[key] += 1

        embed = discord.Embed(
            title="Security Alert",
            description=f"{user.mention} tried to {action} a channel: {getattr(channel, 'mention', channel.name)}",
            color=discord.Color.orange()
        )
        embed.add_field(name="Count", value=str(self.warn_counts[key]))
        embed.set_footer(text=f"User ID: {user.id}")

        log_channel = self._get_log_channel(guild)
        if self.warn_counts[key] < 3:
            await self._log_or_owner_dm(guild, embed, user.mention)
        else:
            try:
                await guild.ban(user, reason="Exceeded channel create/delete limit", delete_message_days=0)
                embed.title = "User Banned"
                embed.color = discord.Color.red()
                embed.description += "\nUser has been banned after 3 warnings."
                await self._log_or_owner_dm(guild, embed, user.mention)
            except Exception:
                pass
            self.warn_counts[key] = 0

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry):
        guild = entry.guild
        if not self.settings[guild.id]["antinuke"]:
            return
        if entry.action in [discord.AuditLogAction.kick, discord.AuditLogAction.ban]:
            bot_member = guild.me
            user = entry.user
            if user.top_role >= bot_member.top_role:
                return
            target = entry.target
            try:
                if entry.action == discord.AuditLogAction.kick:
                    await guild.kick(user, reason="Unauthorized kick attempt")
                elif entry.action == discord.AuditLogAction.ban:
                    await guild.ban(user, reason="Unauthorized ban attempt")
            except Exception:
                pass
            embed = discord.Embed(
                title="Security Action",
                description=f"{user.mention} ({user.id}) attempted to {entry.action.name} {target.mention} and was removed.",
                color=discord.Color.red()
            )
            await self._log_or_owner_dm(guild, embed)

    # ----------- ANTI-BOT-ADD AND ANTI-RAID -----------
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        # Anti-bot-add
        if self.settings[guild.id]["antibotadd"]:
            if member.bot and member != guild.me:
                try:
                    await guild.ban(member, reason="Bot add is disabled by SecureAura.")
                except Exception:
                    pass
                embed = discord.Embed(
                    title="Anti-Botadd Triggered",
                    description=f"Banned bot {member.mention} ({member.id}) as antibotadd is enabled.",
                    color=discord.Color.red()
                )
                await self._log_or_owner_dm(guild, embed)
                return
        # Anti-raid
        if self.settings[guild.id]["antiraid"] and not member.bot:
            now = datetime.utcnow()
            self.recent_joins[guild.id] = [t for t in self.recent_joins[guild.id] if (now - t).total_seconds() < self.raid_interval]
            self.recent_joins[guild.id].append(now)
            if len(self.recent_joins[guild.id]) >= self.raid_threshold:
                # Mass ban all recent joins
                to_ban = []
                for m in guild.members:
                    if not m.bot and m.joined_at and (now - m.joined_at).total_seconds() < self.raid_interval:
                        to_ban.append(m)
                for m in to_ban:
                    try:
                        await guild.ban(m, reason="Anti-raid triggered: suspected raid join.")
                    except Exception:
                        pass
                embed = discord.Embed(
                    title="Anti-Raid Triggered",
                    description=f"Banned {len(to_ban)} members for suspected raid join.",
                    color=discord.Color.red()
                )
                await self._log_or_owner_dm(guild, embed)
                self.recent_joins[guild.id] = []

    # ----------- HELPERS: LOGGING -----------
    def _get_log_channel(self, guild):
        log_channels = getattr(self.bot, "log_channels", {})
        if guild.id in log_channels:
            return guild.get_channel(log_channels[guild.id])
        channel = discord.utils.get(guild.text_channels, name="logs")
        if channel and hasattr(self.bot, "log_channels"):
            self.bot.log_channels[guild.id] = channel.id
        return channel

    async def _log_or_owner_dm(self, guild, embed, mention=None):
        log_channel = self._get_log_channel(guild)
        if log_channel:
            await log_channel.send(embed=embed, content=mention or None)
        else:
            try:
                await guild.owner.send(embed=embed, content=mention or None)
            except Exception:
                pass

async def setup(bot):
    await bot.add_cog(SecurityFeature(bot))