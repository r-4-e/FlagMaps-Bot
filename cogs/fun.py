import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
from utils.embeds import elura_embed

class Fun(commands.Cog):
    """Professional, high-quality entertainment commands for Elura."""
    def __init__(self, bot):
        self.bot = bot

    # 🎲 Coin Flip
    @app_commands.command(name="coinflip", description="Flip a coin — heads or tails?")
    async def coinflip(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = elura_embed("🪙 Flipping...", "The coin is spinning in the air...")
        msg = await interaction.followup.send(embed=embed)
        await asyncio.sleep(2)
        result = random.choice(["Heads", "Tails"])
        color = discord.Color.gold() if result == "Heads" else discord.Color.blue()
        final = elura_embed("🪙 Coin Flip Result", f"**{result}!**", color=color)
        await msg.edit(embed=final)

    # 🎯 Rock-Paper-Scissors
    @app_commands.command(name="rps", description="Play rock-paper-scissors with Elura.")
    async def rps(self, interaction: discord.Interaction):
        options = ["🪨 Rock", "📜 Paper", "✂️ Scissors"]

        view = discord.ui.View(timeout=15)
        for opt in options:
            view.add_item(discord.ui.Button(label=opt.split()[1], emoji=opt[0]))

        async def button_callback(interact: discord.Interaction):
            user_choice = interact.data['custom_id'] if 'custom_id' in interact.data else interact.data['component_type']
            bot_choice = random.choice(options)
            result_embed = elura_embed("🎯 Rock Paper Scissors", f"You chose: **{user_choice}**\nElura chose: **{bot_choice}**")

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
            child.custom_id = f"{child.emoji} {child.label}"

        embed = elura_embed("🎮 Rock Paper Scissors", "Choose your move:")
        await interaction.response.send_message(embed=embed, view=view)

    # 💬 Random Quote
    @app_commands.command(name="quote", description="Get a random motivational or famous quote.")
    async def quote(self, interaction: discord.Interaction):
        quotes = [
            ("“The best way to predict the future is to invent it.”", "— Alan Kay"),
            ("“Success is not final, failure is not fatal: It is the courage to continue that counts.”", "— Winston Churchill"),
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

async def setup(bot):
    await bot.add_cog(Fun(bot))