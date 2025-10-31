# cogs/help.py
import discord
from discord.ext import commands
from discord import app_commands

# Role allowed to see restricted commands
ADMIN_ROLE_ID = 1431189241685344348

class HelpDropdown(discord.ui.Select):
    def __init__(self, bot, is_admin: bool):
        self.bot = bot
        options = [
            discord.SelectOption(label="🏠 Home", description="Overview of Elura Utility"),
            discord.SelectOption(label="💰 Economy", description="Earn, spend, and check balances"),
            discord.SelectOption(label="🎉 Fun", description="Play with fun and interactive commands"),
            discord.SelectOption(label="🌐 Translate", description="Translate messages instantly"),
            discord.SelectOption(label="👋 Welcomer", description="Setup welcome messages"),
            discord.SelectOption(label="🔨 Punishments", description="Moderation and punishments"),
            discord.SelectOption(label="🔢 Counting", description="Global counting system"),
            discord.SelectOption(label="🔒 Privacy", description="View Elura’s data & privacy policy"),
        ]
        if is_admin:
            options.append(discord.SelectOption(label="🛡️ Restricted", description="Developer & Admin commands"))

        super().__init__(placeholder="Select a category…", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(color=discord.Color.blurple())
        selection = self.values[0]

        if selection == "🏠 Home":
            embed.title = "✨ Elura Utility – Help Center"
            embed.description = (
                "Welcome to **Elura Utility**, your all-in-one professional bot.\n\n"
                "Use the dropdown below to browse command categories.\n"
                "Elura is built by **r4e**, designed for modern Discord management and fun."
            )

        elif selection == "💰 Economy":
            embed.title = "💰 Economy Commands"
            embed.add_field(name="/balance", value="Check your balance", inline=False)
            embed.add_field(name="/daily", value="Claim your daily reward", inline=False)
            embed.add_field(name="/pay", value="Send credits to another user", inline=False)

        elif selection == "🎉 Fun":
            embed.title = "🎉 Fun Commands"
            embed.add_field(name="/ryder", value="Summon Ryder for a fun response", inline=False)
            embed.add_field(name="/elpaco", value="Play a random fun action", inline=False)
            embed.add_field(name="/meme", value="Fetch a random meme", inline=False)

        elif selection == "🌐 Translate":
            embed.title = "🌐 Translate Commands"
            embed.add_field(name="/translate", value="Translate text between languages", inline=False)
            embed.add_field(name="/autotranslate", value="Enable auto-translation in a channel", inline=False)

        elif selection == "👋 Welcomer":
            embed.title = "👋 Welcomer Commands"
            embed.add_field(name="/setwelcome", value="Set a welcome message", inline=False)
            embed.add_field(name="/previewwelcome", value="Preview your welcome embed", inline=False)

        elif selection == "🔨 Punishments":
            embed.title = "🔨 Punishment Commands"
            embed.add_field(name="/warn", value="Warn a user", inline=False)
            embed.add_field(name="/mute", value="Mute a user temporarily", inline=False)
            embed.add_field(name="/ban", value="Ban a user", inline=False)
            embed.add_field(name="/unban", value="Unban a user", inline=False)

        elif selection == "🔢 Counting":
            embed.title = "🔢 Counting Commands"
            embed.add_field(name="/setcountingchannel", value="Set the counting channel (Admin only)", inline=False)
            embed.add_field(name="/resetcount", value="Reset the counting progress (Admin only)", inline=False)
            embed.add_field(name="How to play", value="Users count one by one without repeating!", inline=False)

        elif selection == "🔒 Privacy":
            embed.title = "🔒 Privacy & Data"
            embed.description = (
                "Elura keeps your data **safe and minimal**.\n"
                "No personal data is stored beyond what’s required for features.\n"
                "Use `/privacy` for full details."
            )

        elif selection == "🛡️ Restricted":
            embed.title = "🛡️ Restricted Admin Commands"
            embed.description = "Visible only to Elura’s management (r4e team)."
            embed.add_field(name="/setcountingchannel", value="Assign counting channel", inline=False)
            embed.add_field(name="/resetcount", value="Reset counting system", inline=False)
            embed.add_field(name="/privacy", value="Edit privacy settings", inline=False)
            embed.add_field(name="/systemstatus", value="Check bot’s system status", inline=False)
            embed.add_field(name="/maintenance", value="Toggle maintenance mode", inline=False)
            embed.color = discord.Color.gold()

        await interaction.response.edit_message(embed=embed)

class HelpView(discord.ui.View):
    def __init__(self, bot, is_admin: bool):
        super().__init__(timeout=None)
        self.add_item(HelpDropdown(bot, is_admin))

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Display all available Elura commands.")
    async def help(self, interaction: discord.Interaction):
        is_admin = any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles)
        embed = discord.Embed(
            title="✨ Elura Utility – Help Center",
            description="Use the dropdown below to explore categories.",
            color=discord.Color.blurple()
        )
        embed.set_footer(text="Built with precision by r4e • Elura Utility © 2025")
        view = HelpView(self.bot, is_admin)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))