import discord
from discord.ext import commands
from discord import app_commands
from utils.supabase_client import supabase  # shared Supabase connection
import random
from cogs.database import supabase

class Fun(commands.Cog):
    """Fun & interactive commands for entertainment."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🎲 Simple randomizer command
    @app_commands.command(name="coinflip", description="Flip a coin — heads or tails?")
    async def coinflip(self, interaction: discord.Interaction):
        result = random.choice(["🪙 Heads", "🪙 Tails"])
        embed = discord.Embed(
            title="Coin Flip Result",
            description=f"{interaction.user.mention} flipped **{result}**!",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed)

    # 🎯 8Ball command
    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question.")
    async def eight_ball(self, interaction: discord.Interaction, question: str):
        responses = [
            "Yes, definitely!",
            "No chance.",
            "Ask again later.",
            "It is certain.",
            "Very doubtful.",
            "Without a doubt.",
            "Better not tell you now.",
            "Signs point to yes."
        ]
        answer = random.choice(responses)
        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            description=f"**Question:** {question}\n**Answer:** {answer}",
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed)

    # 🐸 Meme fetcher (optional — if you want a fun API)
    @app_commands.command(name="meme", description="Get a random meme from the internet.")
    async def meme(self, interaction: discord.Interaction):
        try:
            # Example of making a Supabase or API call if you store memes in DB
            # This line just shows how you could use Supabase safely
            result = supabase.table("memes").select("*").limit(1).execute()

            meme_url = (
                result.data[0]["url"]
                if result.data and "url" in result.data[0]
                else "https://i.imgur.com/YOj9L9D.png"
            )

            embed = discord.Embed(
                title="😂 Random Meme",
                color=discord.Color.random()
            )
            embed.set_image(url=meme_url)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(
                f"⚠️ Failed to fetch meme: `{e}`", ephemeral=True
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))