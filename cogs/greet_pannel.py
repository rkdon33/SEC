import discord
from discord.ext import commands
from discord import app_commands
import json
import os

GREET_FILE = "greet_settings.json"

def load_greets():
    if not os.path.exists(GREET_FILE):
        return {}
    with open(GREET_FILE, "r") as f:
        return json.load(f)

def save_greets(data):
    with open(GREET_FILE, "w") as f:
        json.dump(data, f, indent=2)

def parse_color(text):
    text = text.strip().lower()
    # Accept formats: "blue", "0x3498db", "#3498db", "3447003", "rgb(52,152,219)"
    named_colors = {
        "blue": 0x3498db,
        "blurple": 0x5865F2,
        "red": 0xe74c3c,
        "green": 0x2ecc71,
        "yellow": 0xf1c40f,
        "orange": 0xe67e22,
        "purple": 0x9b59b6,
        "white": 0xffffff,
        "black": 0x000000,
    }
    if text in named_colors:
        return named_colors[text]
    if text.startswith("0x"):
        try:
            return int(text, 16)
        except:
            return None
    if text.startswith("#"):
        try:
            return int(text[1:], 16)
        except:
            return None
    if text.startswith("rgb"):
        try:
            parts = text.replace("rgb(", "").replace(")", "").split(",")
            r, g, b = [int(x.strip()) for x in parts]
            return (r << 16) + (g << 8) + b
        except:
            return None
    try:
        return int(text)
    except:
        return None

class GreetSetupView(discord.ui.View):
    def __init__(self, cog, author_id):
        super().__init__(timeout=60)
        self.cog = cog
        self.author_id = author_id
        self.value = None

    @discord.ui.button(label="NORMAL", style=discord.ButtonStyle.primary)
    async def normal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(embed=discord.Embed(description="You are not the setup initiator.", color=discord.Color.red()), ephemeral=True)
            return
        self.value = "normal"
        self.stop()

    @discord.ui.button(label="EMBED", style=discord.ButtonStyle.success)
    async def embed_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(embed=discord.Embed(description="You are not the setup initiator.", color=discord.Color.red()), ephemeral=True)
            return
        self.value = "embed"
        self.stop()

class GreetCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup_greet", description="Set up the welcome/greet panel")
    async def setup_greet(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(embed=discord.Embed(description="You need Manage Server permission.", color=discord.Color.red()), ephemeral=True)
            return

        greets = load_greets()
        guild_id = str(interaction.guild_id)
        view = GreetSetupView(self, interaction.user.id)
        embed = discord.Embed(
            title="Welcome Panel Setup",
            description="Choose your welcome message style:\n\n**NORMAL**: Simple text message\n**EMBED**: Rich embed message",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        await view.wait()

        if view.value == "normal":
            await self.normal_flow(interaction)
        elif view.value == "embed":
            await self.embed_flow(interaction)
        else:
            await interaction.followup.send(embed=discord.Embed(description="Setup cancelled.", color=discord.Color.red()), ephemeral=True)

    async def normal_flow(self, interaction):
        def check(m):
            return m.author.id == interaction.user.id and m.channel == interaction.channel
        # Step 1: Ask for message
        embed = discord.Embed(title="Step 1: Welcome Message", description="Please type your welcome message (use `{user}` for mention):", color=discord.Color.blue())
        await interaction.followup.send(embed=embed, ephemeral=True)
        try:
            msg_normal = await self.bot.wait_for('message', timeout=120, check=check)
        except:
            await interaction.followup.send(embed=discord.Embed(description="Setup timed out.", color=discord.Color.red()), ephemeral=True)
            return
        # Step 2: Ask for channel
        embed = discord.Embed(title="Step 2: Channel", description="Please mention the channel for welcome messages (e.g., #general):", color=discord.Color.blue())
        await interaction.followup.send(embed=embed, ephemeral=True)
        try:
            msg_chan = await self.bot.wait_for('message', timeout=60, check=check)
            channel = msg_chan.channel_mentions[0]
        except (IndexError, TimeoutError):
            await interaction.followup.send(embed=discord.Embed(description="Invalid or no channel provided. Setup cancelled.", color=discord.Color.red()), ephemeral=True)
            return
        greets = load_greets()
        greets[str(interaction.guild_id)] = {
            "type": "normal",
            "message": msg_normal.content,
            "channel_id": channel.id
        }
        save_greets(greets)
        await interaction.followup.send(embed=discord.Embed(description=f"Normal welcome message set in {channel.mention}!", color=discord.Color.green()), ephemeral=True)

    async def embed_flow(self, interaction):
        def check(m):
            return m.author.id == interaction.user.id and m.channel == interaction.channel
        # Step 1: Title
        embed = discord.Embed(title="Step 1: Embed Title", description="Please type the EMBED TITLE:", color=discord.Color.blue())
        await interaction.followup.send(embed=embed, ephemeral=True)
        try:
            title_msg = await self.bot.wait_for('message', timeout=120, check=check)
        except:
            await interaction.followup.send(embed=discord.Embed(description="Setup timed out.", color=discord.Color.red()), ephemeral=True)
            return
        # Step 2: Description
        embed = discord.Embed(title="Step 2: Embed Description", description="Please type the EMBED DESCRIPTION:", color=discord.Color.blue())
        await interaction.followup.send(embed=embed, ephemeral=True)
        try:
            desc_msg = await self.bot.wait_for('message', timeout=120, check=check)
        except:
            await interaction.followup.send(embed=discord.Embed(description="Setup timed out.", color=discord.Color.red()), ephemeral=True)
            return
        # Step 3: Footer
        embed = discord.Embed(title="Step 3: Embed Footer (Optional)", description="Please type the EMBED FOOTER (or type `skip`):", color=discord.Color.blue())
        await interaction.followup.send(embed=embed, ephemeral=True)
        try:
            footer_msg = await self.bot.wait_for('message', timeout=60, check=check)
            footer = None if footer_msg.content.lower() == 'skip' else footer_msg.content
        except:
            footer = None
        # Step 4: Image
        embed = discord.Embed(title="Step 4: Embed Image (Optional)", description="Send an image URL for the bottom of the embed (or type `skip`):", color=discord.Color.blue())
        await interaction.followup.send(embed=embed, ephemeral=True)
        try:
            img_msg = await self.bot.wait_for('message', timeout=60, check=check)
            image = None if img_msg.content.lower() == 'skip' else img_msg.content
        except:
            image = None
        # Step 5: Color
        embed = discord.Embed(title="Step 5: Embed Color", description="Please enter a color for the welcome embed (name like `blue`, hex like `#3498db`, or rgb like `rgb(52,152,219)`):", color=discord.Color.blue())
        await interaction.followup.send(embed=embed, ephemeral=True)
        try:
            color_msg = await self.bot.wait_for('message', timeout=60, check=check)
            color_value = parse_color(color_msg.content)
            if color_value is None:
                color_value = 0x3498db  # fallback blue
        except:
            color_value = 0x3498db  # fallback blue
        # Step 6: Channel
        embed = discord.Embed(title="Step 6: Channel", description="Please mention the channel for welcome messages (e.g., #general):", color=discord.Color.blue())
        await interaction.followup.send(embed=embed, ephemeral=True)
        try:
            chan_msg = await self.bot.wait_for('message', timeout=60, check=check)
            channel = chan_msg.channel_mentions[0]
        except (IndexError, TimeoutError):
            await interaction.followup.send(embed=discord.Embed(description="Invalid or no channel provided. Setup cancelled.", color=discord.Color.red()), ephemeral=True)
            return
        greets = load_greets()
        greets[str(interaction.guild_id)] = {
            "type": "embed",
            "title": title_msg.content,
            "description": desc_msg.content,
            "footer": footer,
            "image": image,
            "color": color_value,
            "channel_id": channel.id
        }
        save_greets(greets)
        await interaction.followup.send(embed=discord.Embed(description=f"Embed welcome message set in {channel.mention}!", color=discord.Color.green()), ephemeral=True)

    @app_commands.command(name="greettest", description="Test your current welcome/greet message")
    async def greettest_slash(self, interaction: discord.Interaction):
        await self.send_greet(interaction.guild, interaction.user, interaction.channel)
        await interaction.response.send_message(embed=discord.Embed(description="Greet message sent above!", color=discord.Color.green()), ephemeral=True)

    @commands.command(name="greettest")
    async def greettest_prefix(self, ctx):
        await self.send_greet(ctx.guild, ctx.author, ctx.channel)

    async def send_greet(self, guild, member, target_channel):
        greets = load_greets()
        data = greets.get(str(guild.id))
        if not data:
            await target_channel.send(embed=discord.Embed(description="No greet message is set up for this server.", color=discord.Color.orange()))
            return
        if data["type"] == "normal":
            msg = data["message"].replace("{user}", member.mention)
            await target_channel.send(msg)
        elif data["type"] == "embed":
            embed = discord.Embed(
                title=data["title"].replace("{user}", member.display_name),
                description=data["description"].replace("{user}", member.mention),
                color=data.get("color", 0x3498db)
            )
            if data.get("footer"):
                embed.set_footer(text=data["footer"])
            if data.get("image"):
                embed.set_image(url=data["image"])
            await target_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(GreetCog(bot))