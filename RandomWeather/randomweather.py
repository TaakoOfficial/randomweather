from redbot.core import commands, Config
from redbot.core.i18n import Translator  # Edited by Taako
from discord.ext import tasks  # Edited by Taako
import discord
import pytz
from datetime import datetime, timedelta
from typing import Optional
from .weather_utils import generate_weather, create_weather_embed
from .time_utils import get_system_time_and_timezone, validate_timezone, calculate_next_refresh_time  # Edited by Taako
import logging

_ = Translator("RandomWeather", __file__)  # Edited by Taako

class WeatherCog(commands.Cog):
    """A cog for generating random daily weather updates."""

    __author__ = ["Taako"]
    __version__ = "2.0.0"

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        default_guild = {
            "role_id": None,
            "channel_id": None,
            "tag_role": False,
            "refresh_interval": None,
            "refresh_time": "0000",
            "time_zone": "America/Chicago",
            "show_footer": True,
            "embed_color": 0xFF0000,
            "last_refresh": 0,
        }
        self.config.register_guild(**default_guild)
        self.bot.loop.create_task(self._startup_debug())
        self._refresh_weather_loop.start()

    async def _startup_debug(self):
        """Log debug information when the cog is loaded."""
        await self.bot.wait_until_ready()
        logging.info(f"WeatherCog loaded in {len(self.bot.guilds)} guilds.")

    @tasks.loop(minutes=1)
    async def _refresh_weather_loop(self):
        """Task loop to post daily weather updates."""
        all_guilds = await self.config.all_guilds()
        for guild_id, guild_settings in all_guilds.items():
            refresh_interval = guild_settings.get("refresh_interval")
            refresh_time = guild_settings.get("refresh_time")
            time_zone = validate_timezone(guild_settings.get("time_zone", "UTC"))
            last_refresh = guild_settings.get("last_refresh", 0)

            try:
                next_post_time = calculate_next_refresh_time(
                    last_refresh, refresh_interval, refresh_time, time_zone
                )

                if datetime.now(pytz.timezone(time_zone)) >= next_post_time:
                    await self._post_weather_update(guild_id, guild_settings)
            except Exception as e:
                logging.error(f"Error in weather update loop for guild {guild_id}: {e}")

    async def _post_weather_update(self, guild_id: int, guild_settings: dict):
        """Post a weather update to the configured channel for a specific guild."""
        channel_id = guild_settings.get("channel_id")
        if not channel_id:
            logging.debug(f"No channel configured for guild {guild_id}. Skipping.")
            return

        time_zone = guild_settings.get("time_zone", "UTC")
        weather_data = generate_weather(time_zone)
        embed = create_weather_embed(weather_data, guild_settings)

        channel = self.bot.get_channel(channel_id)
        if channel:
            await channel.send(embed=embed)
            await self.config.guild_from_id(guild_id).last_refresh.set(datetime.now().timestamp())
            logging.info(f"Weather update sent to channel {channel.name} in guild {guild_id}.")
        else:
            logging.warning(f"Channel {channel_id} not found for guild {guild_id}.")

    @_refresh_weather_loop.before_loop
    async def before_refresh_weather_loop(self):
        """Wait until the bot is ready before starting the loop."""
        await self.bot.wait_until_ready()

    @_refresh_weather_loop.error
    async def _refresh_weather_loop_error(self, error: Exception):
        """Handle errors in the weather update loop."""
        logging.error(f"Error in weather update loop: {error}")

    @commands.group(name="rweather", invoke_without_command=True)
    async def rweather(self, ctx: commands.Context):
        """Main command group for RandomWeather."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @rweather.command(name="setchannel")
    async def set_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the channel for weather updates."""
        await self.config.guild(ctx.guild).channel_id.set(channel.id)
        await ctx.send(f"Weather updates will now be sent to: {channel.mention}")

    @rweather.command(name="setrole")
    async def set_role(self, ctx: commands.Context, role: discord.Role):
        """Set the role to be tagged for weather updates."""
        await self.config.guild(ctx.guild).role_id.set(role.id)
        await ctx.send(f"Weather updates will now tag the role: {role.name}")

    @rweather.command(name="toggle_role")
    async def toggle_role(self, ctx: commands.Context):
        """Toggle whether the role should be tagged in weather updates."""
        tag_role = await self.config.guild(ctx.guild).tag_role()
        await self.config.guild(ctx.guild).tag_role.set(not tag_role)
        status = "enabled" if not tag_role else "disabled"
        await ctx.send(f"Role tagging has been {status}.")

    @rweather.command(name="setrefresh")
    async def set_refresh(self, ctx: commands.Context, value: str):
        """Set how often the weather should refresh or specify a time (e.g., `10m` or `1830`)."""
        time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}

        if value.isdigit() and len(value) == 4:
            await self.config.guild(ctx.guild).refresh_time.set(value)
            await self.config.guild(ctx.guild).refresh_interval.set(None)
            await ctx.send(f"Weather will now refresh daily at {value} (military time).")
        elif value[-1] in time_units:
            try:
                unit = value[-1]
                interval = int(value[:-1])
                refresh_interval = interval * time_units[unit]
                await self.config.guild(ctx.guild).refresh_interval.set(refresh_interval)
                await self.config.guild(ctx.guild).refresh_time.set(None)
                await ctx.send(f"Weather will now refresh every {value}.")
            except (ValueError, IndexError):
                await ctx.send("Invalid format. Use a number followed by s (seconds), m (minutes), h (hours), or d (days).")
        else:
            await ctx.send("Invalid format. Use a valid military time (e.g., 1830) or an interval (e.g., 10m, 1h).")

    @rweather.command(name="set_embed_color")
    async def set_embed_color(self, ctx: commands.Context, color: discord.Color):
        """Set the embed color for weather updates dynamically."""
        await self.config.guild(ctx.guild).embed_color.set(color.value)
        await ctx.send(f"Embed color updated to: {color}")

    @rweather.command(name="set_time_zone")
    async def set_time_zone(self, ctx: commands.Context, time_zone: str):
        """Remove the set_time_zone command as the bot will now use the system's timezone."""
        await ctx.send("Setting the timezone is no longer supported. The bot will use the system's timezone.")

    @rweather.command(name="info")
    async def info(self, ctx: commands.Context):
        """View the current settings for weather updates."""  # Edited by Taako
        guild_settings = await self.config.guild(ctx.guild).all()  # Edited by Taako
        embed_color = discord.Color(guild_settings.get("embed_color", 0xFF0000))  # Edited by Taako
        refresh_interval = guild_settings.get("refresh_interval")  # Edited by Taako
        refresh_time = guild_settings.get("refresh_time")  # Edited by Taako
        last_refresh = guild_settings.get("last_refresh", 0)  # Edited by Taako

        # Use the system's timezone for all time-related calculations  # Edited by Taako
        now, system_time_zone = get_system_time_and_timezone()  # Edited by Taako
        time_until_next_refresh_str = "❌ Not set"  # Edited by Taako
        try:
            next_post_time = calculate_next_refresh_time(
                last_refresh, refresh_interval, refresh_time, system_time_zone  # Edited by Taako
            )
            # Ensure both are timezone-aware  # Edited by Taako
            if next_post_time is not None and hasattr(next_post_time, 'tzinfo') and next_post_time.tzinfo is not None:
                if now.tzinfo is None:
                    import pytz  # Edited by Taako
                    now = pytz.timezone(system_time_zone).localize(now)
                time_until_next_refresh = (next_post_time - now).total_seconds()
                if time_until_next_refresh > 0:
                    days, remainder = divmod(time_until_next_refresh, 86400)
                    hours, remainder = divmod(remainder, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    time_until_next_refresh_str = (
                        (f"{int(days)}d " if days else "") +
                        (f"{int(hours)}h " if hours else "") +
                        (f"{int(minutes)}m " if minutes else "") +
                        (f"{int(seconds)}s" if seconds else "")
                    ).strip()
                else:
                    time_until_next_refresh_str = "❌ Not set"  # Edited by Taako
            else:
                time_until_next_refresh_str = "❌ Error"  # Edited by Taako
        except Exception as e:
            logging.error(f"Error calculating next refresh time: {e}")  # Edited by Taako
            time_until_next_refresh_str = "❌ Error"  # Edited by Taako

        # Determine current season  # Edited by Taako
        month = now.month  # Edited by Taako
        if month in [12, 1, 2]:
            current_season = "❄️ Winter"  # Edited by Taako
        elif month in [3, 4, 5]:
            current_season = "🌸 Spring"  # Edited by Taako
        elif month in [6, 7, 8]:
            current_season = "☀️ Summer"  # Edited by Taako
        else:
            current_season = "🍂 Autumn"  # Edited by Taako

        # Get channel and role  # Edited by Taako
        channel = self.bot.get_channel(guild_settings.get("channel_id")) if guild_settings.get("channel_id") else None  # Edited by Taako
        role = ctx.guild.get_role(guild_settings.get("role_id")) if guild_settings.get("role_id") else None  # Edited by Taako

        # Get the current time in the system's timezone  # Edited by Taako
        current_time = now.strftime('%Y-%m-%d %H:%M:%S')  # Edited by Taako

        embed = discord.Embed(
            title=_("🌦️ RandomWeather Settings"),
            color=embed_color
        )  # Edited by Taako
        embed.add_field(name=_("🔄 Refresh Mode:"), value="⏱️ Interval: {} seconds".format(refresh_interval) if refresh_interval else "🕒 Military Time: {}".format(refresh_time) if refresh_time else "❌ Not set", inline=True)  # Edited by Taako
        embed.add_field(name=_("⏳ Time Until Next Refresh:"), value=time_until_next_refresh_str, inline=True)  # Edited by Taako
        embed.add_field(name=_("🕰️ Current Time:"), value=current_time, inline=True)  # Edited by Taako
        embed.add_field(name=_("📢 Channel:"), value=channel.mention if channel else "❌ Not set", inline=True)  # Edited by Taako
        embed.add_field(name=_("🏷️ Role Tagging:"), value="✅ Enabled" if guild_settings.get("tag_role") else "❌ Disabled", inline=True)  # Edited by Taako
        embed.add_field(name=_("🔖 Tag Role:"), value=role.name if role else "❌ Not set", inline=True)  # Edited by Taako
        embed.add_field(name=_("🎨 Embed Color:"), value=str(embed_color), inline=True)  # Edited by Taako
        embed.add_field(name=_("📜 Footer:"), value="✅ Enabled" if guild_settings.get("show_footer") else "❌ Disabled", inline=True)  # Edited by Taako
        embed.add_field(name=_("🌱 Current Season:"), value=current_season, inline=True)  # Edited by Taako

        await ctx.send(embed=embed)  # Edited by Taako

    @rweather.command(name="force")
    @commands.admin_or_permissions(administrator=True)
    async def force_post(self, ctx: commands.Context) -> None:
        """Force post a weather update to the configured channel immediately."""
        guild_settings = await self.config.guild(ctx.guild).all()
        channel_id = guild_settings.get("channel_id")
        if not channel_id:
            await ctx.send("No channel configured for weather updates.")
            return
        try:
            await self._post_weather_update(ctx.guild.id, guild_settings)
            await ctx.send("Weather update posted.")
        except Exception as e:
            logging.error(f"Error in force post: {e}")
            await ctx.send(f"Failed to post weather update: {e}")
