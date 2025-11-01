import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
from utils.embeds import elura_embed
from cogs.database import supabase

class Search(commands.Cog):
    """Modern and privacy-friendly search utilities for Elura."""
    def __init__(self, bot):
        self.bot = bot

    async def fetch_ddg(self, query):
        """Fetch DuckDuckGo Instant Answer API results."""
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_redirect=1&no_html=1"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()

    @app_commands.command(name="search", description="Search the web with Elura’s smart search system.")
    async def search(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        data = await self.fetch_ddg(query)

        title = data.get("Heading") or query.title()
        abstract = data.get("AbstractText", "")
        url = data.get("AbstractURL") or f"https://duckduckgo.com/?q={query.replace(' ', '+')}"
        image = data.get("Image")

        if not abstract:
            abstract = "No direct summary found, but you can click below to explore full results."

        embed = elura_embed(f"🔍 {title}", abstract)
        embed.url = url
        embed.set_footer(text="Powered by DuckDuckGo | Google Search coming soon")
        if image:
            embed.set_thumbnail(url=image)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="wiki", description="Get a quick summary from Wikipedia.")
    async def wiki(self, interaction: discord.Interaction, topic: str):
        await interaction.response.defer()
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic.replace(' ', '_')}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                else:
                    return await interaction.followup.send(embed=elura_embed("⚠️ Not Found", "No results found on Wikipedia."))

        title = data.get("title", topic.title())
        extract = data.get("extract", "No summary available.")
        page_url = data.get("content_urls", {}).get("desktop", {}).get("page", f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}")
        image = data.get("thumbnail", {}).get("source")

        embed = elura_embed(f"📘 {title}", extract)
        embed.url = page_url
        if image:
            embed.set_thumbnail(url=image)
        embed.set_footer(text="From Wikipedia")

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Search(bot))