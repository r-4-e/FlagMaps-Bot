import discord
from datetime import datetime

# ───────────────────────────────
# 💎 Universal Embed Generator
# ───────────────────────────────

def elura_embed(title: str = None, description: str = None, color: discord.Color = discord.Color.blurple()):
    """
    Create a consistent embed for Elura/FlagMaps Bot.
    """
    embed = discord.Embed(
        title=title or "",
        description=description or "",
        color=color,
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text="Powered by FlagMaps | Elura Systems", icon_url="https://cdn.discordapp.com/emojis/123456789012345678.webp?size=96&quality=lossless")
    return embed


# ───────────────────────────────
# 🟥 Error Embeds
# ───────────────────────────────

def error_embed(message: str):
    """Return a red error embed."""
    return elura_embed("❌ Error", message, color=discord.Color.red())


# ───────────────────────────────
# 🟩 Success Embeds
# ───────────────────────────────

def success_embed(message: str):
    """Return a green success embed."""
    return elura_embed("✅ Success", message, color=discord.Color.green())


# ───────────────────────────────
# 🟦 Info Embeds
# ───────────────────────────────

def info_embed(message: str):
    """Return a blue info embed."""
    return elura_embed("ℹ️ Information", message, color=discord.Color.blurple())