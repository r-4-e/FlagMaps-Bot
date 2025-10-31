import discord
from discord.ext import commands
from discord import app_commands
from supabase import create_client, Client
import os

# Load Supabase credentials from environment
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ========== INTERACTIVE VIEW ==========
class SetupView(discord.ui.View):
    def __init__(self, bot: commands.Bot, guild_id: int):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        self.settings = {
            "welcome_channel": None,
            "logs_channel": None,
            "language": "English",
            "punishment_channel": None,
            "economy_enabled": False,
            "message_counter": False
        }

    # -------------------------------
    @discord.ui.select(
        placeholder="🌍 Choose Bot Language",
        options=[
            discord.SelectOption(label="English", description="Default"),
            discord.SelectOption(label="Hindi", description="हिन्दी"),
            discord.SelectOption(label="Spanish", description="Español")
        ]
    )
    async def select_language(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.settings["language"] = select.values[0]
        await interaction.response.send_message(
            f"✅ Language set to **{select.values[0]}**", ephemeral=True
        )

    # -------------------------------
    @discord.ui.button(label="🎉 Set Welcome Channel", style=discord.ButtonStyle.primary)
    async def set_welcome_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Mention the **welcome channel** (e.g. #welcome):", ephemeral=True
        )

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        msg = await self.bot.wait_for("message", check=check)
        if msg.channel_mentions:
            self.settings["welcome_channel"] = msg.channel_mentions[0].id
            await msg.reply(f"🎉 Welcome channel set to {msg.channel_mentions[0].mention}", mention_author=False)
        else:
            await msg.reply("❌ Invalid channel mention.")

    # -------------------------------
    @discord.ui.button(label="🧾 Set Logs Channel", style=discord.ButtonStyle.blurple)
    async def set_logs_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Mention the **logs channel**:", ephemeral=True
        )

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        msg = await self.bot.wait_for("message", check=check)
        if msg.channel_mentions:
            self.settings["logs_channel"] = msg.channel_mentions[0].id
            await msg.reply(f"🧾 Logs channel set to {msg.channel_mentions[0].mention}", mention_author=False)
        else:
            await msg.reply("❌ Invalid channel mention.")

    # -------------------------------
    @discord.ui.button(label="🛑 Set Punishment Channel", style=discord.ButtonStyle.red)
    async def set_punishment_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Mention the **punishment log channel**:", ephemeral=True
        )

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        msg = await self.bot.wait_for("message", check=check)
        if msg.channel_mentions:
            self.settings["punishment_channel"] = msg.channel_mentions[0].id
            await msg.reply(f"🛑 Punishment channel set to {msg.channel_mentions[0].mention}", mention_author=False)
        else:
            await msg.reply("❌ Invalid channel mention.")

    # -------------------------------
    @discord.ui.button(label="💰 Toggle Economy", style=discord.ButtonStyle.green)
    async def toggle_economy(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.settings["economy_enabled"] = not self.settings["economy_enabled"]
        status = "enabled ✅" if self.settings["economy_enabled"] else "disabled ❌"
        await interaction.response.send_message(f"💰 Economy system {status}", ephemeral=True)

    # -------------------------------
    @discord.ui.button(label="💬 Toggle Message Counter", style=discord.ButtonStyle.secondary)
    async def toggle_counter(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.settings["message_counter"] = not self.settings["message_counter"]
        status = "enabled ✅" if self.settings["message_counter"] else "disabled ❌"
        await interaction.response.send_message(f"💬 Message counter {status}", ephemeral=True)

    # -------------------------------
    @discord.ui.button(label="✅ Finish Setup", style=discord.ButtonStyle.success)
    async def finish_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        supabase.table("guild_settings").upsert({
            "guild_id": str(self.guild_id),
            "welcome_channel": self.settings["welcome_channel"],
            "logs_channel": self.settings["logs_channel"],
            "language": self.settings["language"],
            "punishment_channel": self.settings["punishment_channel"],
            "economy_enabled": self.settings["economy_enabled"],
            "message_counter": self.settings["message_counter"]
        }).execute()

        embed = discord.Embed(
            title="✅ Elura Setup Complete",
            description=(
                "Your server is now connected to Elura!\n\n"
                f"**Language:** {self.settings['language']}\n"
                f"**Welcome Channel:** <#{self.settings['welcome_channel']}>\n"
                f"**Logs Channel:** <#{self.settings['logs_channel']}>\n"
                f"**Punishment Channel:** <#{self.settings['punishment_channel']}>\n"
                f"**Economy:** {'Enabled' if self.settings['economy_enabled'] else 'Disabled'}\n"
                f"**Message Counter:** {'Enabled' if self.settings['message_counter'] else 'Disabled'}"
            ),
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)
        self.stop()


# ========== MAIN COG ==========
class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Run the Elura Setup Wizard for your server.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="⚙️ Elura Setup Wizard",
            description="Welcome to **Elura**, your premium server assistant.\n\nUse the buttons below to configure the bot settings for this server.",
            color=discord.Color.blurple()
        )
        embed.set_footer(text="Made with 💙 by r4e")

        view = SetupView(self.bot, interaction.guild.id)
        await interaction.response.send_message(embed=embed, view=view)

    @setup.error
    async def setup_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "❌ You need **Administrator** permissions to run setup.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"⚠️ Unexpected error: {error}", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Setup(bot))