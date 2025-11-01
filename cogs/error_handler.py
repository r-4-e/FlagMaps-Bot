import discord
import traceback
from discord.ext import commands
from discord import app_commands
from utils.embeds import error_embed, info_embed

DEVELOPER_LOG_CHANNEL_ID = 1430955047524761754  # ⚠️ Replace with your bot-log channel ID


class ErrorHandler(commands.Cog):
    """Global error handler for both prefix and slash commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- Prefix command errors ---
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        await self._handle_error(ctx, error, is_app=False)

    # --- Slash command errors ---
    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error):
        # Ensure compatibility with discord.py 2.3+
        if isinstance(error, app_commands.AppCommandError):
            pass
        await self._handle_error(interaction, error, is_app=True)

    # --- Shared handler ---
    async def _handle_error(self, target, error, is_app: bool):
        """Main centralized error handling logic."""
        # Ignore harmless ones
        if isinstance(error, (commands.CommandNotFound, discord.NotFound)):
            return

        if isinstance(error, commands.CommandOnCooldown):
            embed = info_embed(f"⏳ Please wait **{error.retry_after:.1f} seconds** before using this again.")
            return await self._send_embed(target, embed, is_app)

        if isinstance(error, commands.MissingPermissions):
            missing = ", ".join(error.missing_permissions)
            embed = error_embed(f"🚫 You’re missing permissions: `{missing}`.")
            return await self._send_embed(target, embed, is_app)

        if isinstance(error, commands.BotMissingPermissions):
            missing = ", ".join(error.missing_permissions)
            embed = error_embed(f"⚠️ I don’t have permissions: `{missing}`.")
            return await self._send_embed(target, embed, is_app)

        if isinstance(error, commands.MissingRequiredArgument):
            embed = error_embed(f"❗ Missing argument: `{error.param.name}`.")
            return await self._send_embed(target, embed, is_app)

        # Generic fallback
        embed = error_embed("⚠️ An unexpected error occurred. The issue has been logged.")
        await self._send_embed(target, embed, is_app)

        print(f"[⚠️ ERROR] {type(error).__name__}: {error}")
        traceback.print_exc()

        await self._send_dev_log(target, error)

    async def _send_embed(self, target, embed, is_app: bool):
        """Sends an embed message safely (works for both ctx and interaction)."""
        try:
            if is_app:
                if target.response.is_done():
                    await target.followup.send(embed=embed, ephemeral=True)
                else:
                    await target.response.send_message(embed=embed, ephemeral=True)
            else:
                await target.send(embed=embed)
        except Exception as e:
            print(f"[ErrorHandler] Failed to send embed: {e}")

    async def _send_dev_log(self, target, error):
        """Logs detailed traceback info to the developer log channel."""
        try:
            channel = self.bot.get_channel(DEVELOPER_LOG_CHANNEL_ID)
            if not channel:
                print("[ErrorHandler] Developer log channel not found.")
                return

            tb_text = "".join(traceback.format_exception(type(error), error, error.__traceback__))
            context_info = (
                f"**User:** {getattr(target.user if hasattr(target, 'user') else target.author, 'mention', 'Unknown')}\n"
                f"**Command:** {getattr(getattr(target, 'command', None), 'name', 'Slash Command')}\n"
                f"**Guild:** {getattr(target.guild, 'name', 'DM or Unknown')}\n"
                f"**Error Type:** `{type(error).__name__}`"
            )

            if len(tb_text) > 1800:
                tb_text = tb_text[:1800] + "\n... (truncated)"

            embed = discord.Embed(
                title="⚠️ Error Logged",
                description=f"{context_info}\n\n```py\n{tb_text}\n```",
                color=discord.Color.red()
            )
            await channel.send(embed=embed)

        except Exception as e:
            print(f"[ErrorHandler] Failed to send developer log: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(ErrorHandler(bot))