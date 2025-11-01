import discord
import traceback
from discord.ext import commands
from utils.embeds import error_embed, info_embed

DEVELOPER_LOG_CHANNEL_ID = 123456789012345678  # ⬅️ replace this with your private bot-log channel ID

class ErrorHandler(commands.Cog):
    """Global error handler for both prefix and slash commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        await self._handle_error(ctx, error, is_app=False)

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.AppCommandError):
        await self._handle_error(interaction, error, is_app=True)

    async def _handle_error(self, target, error, is_app: bool):
        # --- Ignore harmless errors ---
        if isinstance(error, (commands.CommandNotFound, discord.NotFound)):
            return

        # --- Cooldown error ---
        if isinstance(error, commands.CommandOnCooldown):
            embed = info_embed(f"⏳ Please wait **{error.retry_after:.1f} seconds** before using this again.")
            await self._send_embed(target, embed, is_app)
            return

        # --- Missing user permissions ---
        if isinstance(error, commands.MissingPermissions):
            missing = ", ".join(error.missing_permissions)
            embed = error_embed(f"🚫 You’re missing permissions: `{missing}`.")
            await self._send_embed(target, embed, is_app)
            return

        # --- Missing bot permissions ---
        if isinstance(error, commands.BotMissingPermissions):
            missing = ", ".join(error.missing_permissions)
            embed = error_embed(f"⚠️ I don’t have permissions: `{missing}`.")
            await self._send_embed(target, embed, is_app)
            return

        # --- Missing arguments ---
        if isinstance(error, commands.MissingRequiredArgument):
            embed = error_embed(f"❗ Missing argument: `{error.param.name}`.")
            await self._send_embed(target, embed, is_app)
            return

        # --- Generic fallback ---
        embed = error_embed("⚠️ An unexpected error occurred. The issue has been logged.")
        await self._send_embed(target, embed, is_app)

        # Log to console
        print(f"[⚠️ ERROR] {type(error).__name__}: {error}")
        traceback.print_exc()

        # Send detailed log to developer log channel
        await self._send_dev_log(target, error)

    async def _send_embed(self, target, embed, is_app: bool):
        """Safely send embed to interaction or command context."""
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
        """Send full traceback to dev log channel."""
        try:
            channel = self.bot.get_channel(DEVELOPER_LOG_CHANNEL_ID)
            if not channel:
                print("[ErrorHandler] Developer log channel not found.")
                return

            tb_text = "".join(traceback.format_exception(type(error), error, error.__traceback__))
            context_info = (
                f"**User:** {getattr(target.user if hasattr(target, 'user') else target.author, 'mention', 'Unknown')}\n"
                f"**Command:** {getattr(target.command, 'name', 'Slash Command')}\n"
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

async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))