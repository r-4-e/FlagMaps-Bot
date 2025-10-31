import discord
from discord.ext import commands
from discord import app_commands
from googletrans import Translator
from utils.embeds import elura_embed

translator = Translator()

class Translate(commands.Cog):
    """Translate text between languages automatically."""
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="translate", description="Translate text to a specific language (auto-detect source).")
    async def translate(self, interaction: discord.Interaction, text: str, target_language: str):
        """Translates text to the desired language."""
        await interaction.response.defer(thinking=True)
        try:
            result = translator.translate(text, dest=target_language)
            embed = elura_embed(
                "🌍 Translation Complete",
                f"**From:** `{result.src}` → **To:** `{result.dest}`\n\n"
                f"**Original:**\n{text}\n\n"
                f"**Translated:**\n{result.text}"
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = elura_embed("⚠️ Translation Error", f"An error occurred:\n`{e}`", color=discord.Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Translate(bot))