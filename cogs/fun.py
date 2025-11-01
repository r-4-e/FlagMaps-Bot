import os
import random
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from supabase import create_client, Client
from utils.embeds import elura_embed

# ------------------- Supabase Connection -------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


class Fun(commands.Cog):
    """🎉 Fun & interactive commands for your community."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🎲 Coin Flip
    @app_commands.command(name="coinflip", description="Flip a coin — heads or tails?")
    async def coinflip(self, interaction: discord.Interaction):
        await interaction.response.defer()
        msg = await interaction.followup.send(embed=elura_embed("🪙 Flipping...", "The coin spins in the air..."))
        await asyncio.sleep(2)
        result = random.choice(["Heads", "Tails"])
        color = discord.Color.gold() if result == "Heads" else discord.Color.blurple()
        await msg.edit(embed=elura_embed("🪙 Coin Flip Result", f"**{result}!**", color=color))

    # 🎯 Rock Paper Scissors
    @app_commands.command(name="rps", description="Play Rock-Paper-Scissors with the bot!")
    async def rps(self, interaction: discord.Interaction):
        options = ["🪨 Rock", "📜 Paper", "✂️ Scissors"]

        view = discord.ui.View(timeout=15)
        for opt in options:
            emoji, label = opt.split()
            button = discord.ui.Button(label=label, emoji=emoji)
            button.custom_id = opt
            view.add_item(button)

        async def button_callback(interact: discord.Interaction):
            user_choice = interact.data["custom_id"]
            bot_choice = random.choice(options)

            result_embed = elura_embed(
                "🎯 Rock Paper Scissors",
                f"You chose: **{user_choice}**\nElura chose: **{bot_choice}**"
            )

            if user_choice == bot_choice:
                result_embed.color = discord.Color.yellow()
                result_embed.add_field(name="Result", value="🤝 It's a tie!")
            elif (user_choice == "🪨 Rock" and bot_choice == "✂️ Scissors") or \
                 (user_choice == "📜 Paper" and bot_choice == "🪨 Rock") or \
                 (user_choice == "✂️ Scissors" and bot_choice == "📜 Paper"):
                result_embed.color = discord.Color.green()
                result_embed.add_field(name="Result", value="🎉 You win!")
            else:
                result_embed.color = discord.Color.red()
                result_embed.add_field(name="Result", value="😢 You lost!")

            await interact.response.edit_message(embed=result_embed, view=None)

        for child in view.children:
            child.callback = button_callback

        embed = elura_embed("🎮 Rock Paper Scissors", "Choose your move below:")
        await interaction.response.send_message(embed=embed, view=view)

    # 💬 Random Quote
    @app_commands.command(name="quote", description="Get a random motivational or famous quote.")
    async def quote(self, interaction: discord.Interaction):
        quotes = [
            ("“The best way to predict the future is to invent it.”", "— Alan Kay"),
            ("“Success is not final, failure is not fatal: it is the courage to continue that counts.”", "— Winston Churchill"),
            ("“In the middle of difficulty lies opportunity.”", "— Albert Einstein"),
            ("“Don’t watch the clock; do what it does. Keep going.”", "— Sam Levenson"),
            ("“Dream big. Start small. Act now.”", "— Robin Sharma")
        ]
        quote, author = random.choice(quotes)
        embed = elura_embed("💬 Random Quote", f"{quote}\n{author}")
        await interaction.response.send_message(embed=embed)

    # 🎰 Slot Machine
    @app_commands.command(name="slots", description="Spin the slot machine!")
    async def slots(self, interaction: discord.Interaction):
        emojis = ["🍒", "🍋", "🍇", "🍉", "⭐", "💎"]
        await interaction.response.defer()
        msg = await interaction.followup.send(embed=elura_embed("🎰 Spinning...", "Good luck! 🍀"))
        await asyncio.sleep(2)
        result = [random.choice(emojis) for _ in range(3)]
        display = " | ".join(result)

        if len(set(result)) == 1:
            text = f"{display}\n\n💎 **Jackpot! You win!**"
            color = discord.Color.gold()
        elif len(set(result)) == 2:
            text = f"{display}\n\n⭐ **Close! You got two matching!**"
            color = discord.Color.green()
        else:
            text = f"{display}\n\n😢 Better luck next time!"
            color = discord.Color.red()

        await msg.edit(embed=elura_embed("🎰 Slot Machine", text, color=color))


async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))