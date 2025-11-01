import discord
from discord.ext import commands
from utils.embeds import error_embed, info_embed

class ErrorHandler(commands.Cog):
    """Global error handler for the bot."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Handles classic prefix command errors (if you use any)."""
        await self._handle_error(ctx, error, is_app=False)

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.AppCommandError):
        """Handles slash command errors."""
        await self._handle_error(interaction, error, is_app=True)

    async def _handle_error(self, target, error, is_app: bool):
        """Internal shared handler for both types."""

        # --- Ignore these ---
        if isinstance(error, (commands.CommandNotFound, discord.NotFound)):
            return

        # --- Cooldown ---
        if isinstance(error, commands.CommandOnCooldown):
            embed = info_embed(f"⏳ Please wait **{error.retry_after:.1f} seconds** before using this again.")
            await self._send_embed(target, embed, is_app)
            return

        # --- Missing Permissions ---
        if isinstance(error, commands.MissingPermissions):
            missing = ", ".join(error.missing_permissions)
            embed = error_embed(f"🚫 You lack the required permissions: `{missing}`.")
            await self._send_embed(target, embed, is_app)
            return

        # --- Bot Missing Permissions ---
        if isinstance(error, commands.BotMissingPermissions):
            missing = ", ".join(error.missing_permissions)
            embed = error_embed(f"⚠️ I don’t have the required permissions: `{missing}`.")
            await self._send_embed(target, embed, is_app)
            return

        # --- Missing Required Argument ---
        if isinstance(error, commands.MissingRequiredArgument):
            embed = error_embed(f"❗ Missing argument: `{error.param.name}`.")
            await self._send_embed(target, embed, is_app)
            return

        # --- Generic fallback ---
        embed = error_embed("An unexpected error occurred. The issue has been logged.")
        await self._send_embed(target, embed, is_app)

        # Also log to console for debugging
        print(f"[⚠️ ERROR] {type(error).__name__}: {error}")

    async def _send_embed(self, target, embed, is_app: bool):
        """Safely sends embed to interaction or context."""
        try:
            if is_app:
                if target.response.is_done():
                    await target.followup.send(embed=embed, ephemeral=True)
                else:
                    await target.response.send_message(embed=embed, ephemeral=True)
            else:
                await target.send(embed=embed)
        except Exception as e:
            print(f"[ErrorHandler] Failed to send error embed: {e}")

async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))