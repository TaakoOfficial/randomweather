import random
import discord  # Edited by Taako
from redbot.core import commands, Config  # Edited by Taako
import asyncio  # Edited by Taako
from datetime import datetime, timedelta  # Edited by Taako
import pytz  # Edited by Taako
from redbot.core.utils.chat_formatting import humanize_list  # Edited by Taako
from discord.ext import tasks  # Edited by Taako
from .file_utils import read_last_posted, write_last_posted  # Edited by Taako
from .weather_utils import generate_weather, create_weather_embed  # Edited by Taako
import logging  # Edited by Taako

# Configure logging for debugging  # Edited by Taako
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')  # Edited by Taako

class WeatherCog(commands.Cog):
    """A cog for generating random daily weather."""  # Edited by Taako

    # Edited by Taako
    def __init__(self, bot):
        self._bot = bot  # Store the bot instance  # Edited by Taako
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)  # Edited by Taako
        default_guild = {
            "role_id": None,  # Role ID for tagging  # Edited by Taako
            "channel_id": None,  # Channel ID for updates  # Edited by Taako
            "tag_role": False,  # Whether to tag the role  # Edited by Taako
            "refresh_interval": None,  # Refresh interval in seconds  # Edited by Taako
            "refresh_time": "0000",  # Default to military time 00:00 (midnight)  # Edited by Taako
            "time_zone": "America/Chicago",  # Default to Central Time (America/Chicago)  # Edited by Taako
            "show_footer": True,  # Whether to show the footer in embeds  # Edited by Taako
            "embed_color": 0xFF0000,  # Default embed color (red)  # Edited by Taako
            "last_refresh": 0,  # Timestamp of the last refresh (default: 0)  # Edited by Taako
        }  # Edited by Taako
        self.config.register_guild(**default_guild)  # Edited by Taako

        # Generate initial weather using the default time zone  # Edited by Taako
        default_time_zone = default_guild["time_zone"]  # Edited by Taako
        self._current_weather = generate_weather(default_time_zone)  # Pass default time zone  # Edited by Taako
        self._refresh_weather_loop.start()  # Start the task loop on cog initialization  # Edited by Taako

    async def _post_weather_update(self):
        """Post weather updates to the configured channel."""  # Edited by Taako
        all_guilds = await self.config.all_guilds()  # Edited by Taako
        for guild_id, guild_settings in all_guilds.items():
            channel_id = guild_settings["channel_id"]  # Edited by Taako
            if not channel_id:
                logging.debug(f"[DEBUG] No channel configured for guild {guild_id}. Skipping.")  # Edited by Taako
                continue  # Edited by Taako

            time_zone = guild_settings.get("time_zone", "UTC")  # Default to UTC if not set  # Edited by Taako
            try:
                self._current_weather = generate_weather(time_zone)  # Generate weather  # Edited by Taako
                embed = create_weather_embed(self._current_weather, guild_settings)  # Create embed  # Edited by Taako

                channel = self._bot.get_channel(channel_id)  # Edited by Taako
                if channel:
                    await channel.send(embed=embed)  # Send the embed  # Edited by Taako
                    logging.info(f"Weather update sent to channel {channel.name} in guild {guild_id}.")  # Edited by Taako
                else:
                    logging.warning(f"[WARNING] Channel {channel_id} not found for guild {guild_id}.")  # Edited by Taako
            except Exception as e:
                logging.error(f"[ERROR] Failed to post weather update for guild {guild_id}: {e}")  # Edited by Taako

    async def cog_load(self):
        """Start the weather update loop without triggering an immediate post."""  # Edited by Taako
        logging.debug("Starting cog_load method.")  # Edited by Taako
        if not self._refresh_weather_loop.is_running():
            logging.debug("Starting weather update loop.")  # Edited by Taako
            self._refresh_weather_loop.start()  # Edited by Taako

    def cog_unload(self):
        """Clean up tasks when the cog is unloaded."""  # Edited by Taako
        logging.debug("Unloading cog and stopping weather update loop.")  # Edited by Taako
        self._refresh_weather_loop.cancel()  # Stop the weather update loop  # Edited by Taako

    def _get_current_season(self, time_zone):
        """Determine the current season based on the time zone and date."""  # Edited by Taako
        now = datetime.now(pytz.timezone(time_zone))
        month = now.month
        day = now.day

        if (month == 12 and day >= 21) or (1 <= month <= 2) or (month == 3 and day < 20):
            return "Winter"
        elif (month == 3 and day >= 20) or (4 <= month <= 5) or (month == 6 and day < 21):
            return "Spring"
        elif (month == 6 and day >= 21) or (7 <= month <= 8) or (month == 9 and day < 22):
            return "Summer"
        elif (month == 9 and day >= 22) or (10 <= month <= 11) or (month == 12 and day < 21):
            return "Autumn"
        return "Unknown"

    @tasks.loop(minutes=1)  # Check every minute to ensure timely posting  # Edited by Taako
    async def _refresh_weather_loop(self):
        """Task loop to post daily weather updates."""  # Edited by Taako
        all_guilds = await self.config.all_guilds()  # Edited by Taako
        for guild_id, guild_settings in all_guilds.items():
            channel_id = guild_settings["channel_id"]  # Edited by Taako
            if not channel_id:
                continue  # Edited by Taako

            time_zone = guild_settings["time_zone"] or "UTC"  # Default to UTC if not set  # Edited by Taako
            tz = pytz.timezone(time_zone)  # Edited by Taako
            now = datetime.now(tz)  # Get the current time in the timezone  # Edited by Taako

            refresh_interval = guild_settings.get("refresh_interval")  # Edited by Taako
            refresh_time = guild_settings.get("refresh_time")  # Edited by Taako

            if refresh_interval:
                # Calculate the next post time based on the interval  # Edited by Taako
                last_posted = read_last_posted()  # Edited by Taako
                if last_posted:
                    last_posted_dt = datetime.fromisoformat(last_posted).astimezone(tz)  # Edited by Taako
                    next_post_time = last_posted_dt + timedelta(seconds=refresh_interval)  # Edited by Taako
                else:
                    next_post_time = now + timedelta(seconds=refresh_interval)  # Default to now + interval if no last_posted exists  # Edited by Taako
            elif refresh_time:
                # Calculate the next post time based on the specific time  # Edited by Taako
                target_time = datetime.strptime(refresh_time, "%H%M").replace(
                    tzinfo=tz, year=now.year, month=now.month, day=now.day
                )  # Edited by Taako
                if now >= target_time:  # If the target time has already passed today  # Edited by Taako
                    target_time += timedelta(days=1)  # Move to the next day  # Edited by Taako
                next_post_time = target_time  # Edited by Taako
            else:
                # Default to 00:00 daily if no interval or time is set  # Edited by Taako
                next_post_time = now.replace(hour=0, minute=0, second=0) + timedelta(days=1)  # Edited by Taako

            # Debug logging to track loop behavior  # Edited by Taako
            logging.debug(f"[DEBUG] Current time: {now}")  # Edited by Taako
            logging.debug(f"[DEBUG] Next post time: {next_post_time}")  # Edited by Taako

            # Check if it's time to post  # Edited by Taako
            if now >= next_post_time:  # Edited by Taako
                logging.debug("[DEBUG] It's time to post the weather update.")  # Edited by Taako
                # Generate and send the weather update  # Edited by Taako
                weather_data = self._generate_weather_data()  # Edited by Taako
                embed = discord.Embed(
                    title="🌦️ Today's Weather",  # Edited by Taako
                    description=weather_data,
                    color=discord.Color.blue()  # Default color  # Edited by Taako
                )
                channel = self._bot.get_channel(channel_id)  # Edited by Taako
                if channel:
                    logging.debug(f"[DEBUG] Sending weather update to channel: {channel.name}")  # Edited by Taako
                    await channel.send(embed=embed)  # Edited by Taako
                    write_last_posted()  # Log the last posted time after sending the embed  # Edited by Taako
                else:
                    logging.debug("[DEBUG] Channel not found or invalid.")  # Edited by Taako

                # Update the next post time after posting  # Edited by Taako
                if refresh_interval:
                    next_post_time = now + timedelta(seconds=refresh_interval)  # Edited by Taako
                elif refresh_time:
                    next_post_time = target_time + timedelta(days=1)  # Move to the next day for time-based refresh  # Edited by Taako

    @_refresh_weather_loop.error
    async def _refresh_weather_loop_error(self, error):
        """Handle errors in the weather update loop and restart it if necessary."""  # Edited by Taako
        logging.error(f"Error in weather update loop: {error}")  # Edited by Taako
        if not self._refresh_weather_loop.is_running():
            logging.debug("Restarting weather update loop after error.")  # Edited by Taako
            self._refresh_weather_loop.start()  # Edited by Taako

    @_refresh_weather_loop.before_loop
    async def before_refresh_weather_loop(self):
        """Wait until the bot is ready before starting the loop."""  # Edited by Taako
        logging.debug("Waiting for bot to be ready before starting loop.")  # Edited by Taako
        await self._bot.wait_until_ready()  # Edited by Taako

    @commands.group(name="rweather", invoke_without_command=True)
    async def rweather(self, ctx):
        """Main rweather command."""
        # Edited by Taako
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)  # Show the help menu if no subcommand is provided

    @rweather.command(name="setchannel")
    async def set_channel(self, ctx, channel: discord.TextChannel):
        """Set the channel for weather updates."""  # Edited by Taako
        await self.config.guild(ctx.guild).channel_id.set(channel.id)  # Edited by Taako
        await ctx.send(f"Weather updates will now be sent to: {channel.mention}")  # Edited by Taako

    @rweather.command(name="force")
    async def force(self, ctx):
        """Force a weather update for the day."""  # Edited by Taako
        guild_settings = await self.config.guild(ctx.guild).all()  # Edited by Taako
        time_zone = guild_settings["time_zone"]  # Edited by Taako
        self._current_weather = generate_weather(time_zone)  # Edited by Taako
        embed = create_weather_embed(self._current_weather, guild_settings)  # Edited by Taako
        role_mention = f"<@&{guild_settings['role_id']}>" if guild_settings["role_id"] and guild_settings["tag_role"] else ""  # Edited by Taako
        channel_id = guild_settings["channel_id"]  # Edited by Taako
        if channel_id:  # Edited by Taako
            channel = self._bot.get_channel(channel_id)  # Edited by Taako
            if channel:  # Edited by Taako
                await channel.send(content=role_mention, embed=embed)  # Edited by Taako
                await ctx.send(f"Weather update sent to {channel.mention}.")  # Edited by Taako
            else:  # Edited by Taako
                await ctx.send("The set channel is invalid. Please set a valid channel.")  # Edited by Taako
        else:  # Edited by Taako
            await ctx.send(embed=embed)  # Edited by Taako

    @rweather.command(name="setrole")
    async def set_role(self, ctx, role: discord.Role):
        """Set the role to be tagged for weather updates."""  # Edited by Taako
        await self.config.guild(ctx.guild).role_id.set(role.id)  # Edited by Taako
        await ctx.send(f"Weather updates will now tag the role: {role.name}")  # Edited by Taako

    @rweather.command(name="toggle_role")
    async def toggle_role(self, ctx):
        """Toggle whether the role should be tagged in weather updates."""  # Edited by Taako
        tag_role = await self.config.guild(ctx.guild).tag_role()  # Edited by Taako
        await self.config.guild(ctx.guild).tag_role.set(not tag_role)  # Edited by Taako
        status = "enabled" if not tag_role else "disabled"  # Edited by Taako
        await ctx.send(f"Role tagging has been {status}.")  # Edited by Taako

    @rweather.command(name="toggle_refresh_mode")
    async def toggle_refresh_mode(self, ctx):
        """Toggle between interval-based and military time refresh modes."""  # Edited by Taako
        guild_settings = await self.config.guild(ctx.guild).all()  # Edited by Taako
        if guild_settings["refresh_interval"]:  # Edited by Taako
            await self.config.guild(ctx.guild).refresh_interval.set(None)  # Edited by Taako
            await self.config.guild(ctx.guild).refresh_time.set("0000")  # Default to midnight  # Edited by Taako
            await ctx.send("Switched to military time refresh mode (default: 00:00).")  # Edited by Taako
        else:  # Edited by Taako
            await self.config.guild(ctx.guild).refresh_time.set(None)  # Edited by Taako
            await self.config.guild(ctx.guild).refresh_interval.set(3600)  # Default to 1 hour  # Edited by Taako
            await ctx.send("Switched to interval-based refresh mode (default: 1 hour).")  # Edited by Taako

    @rweather.command(name="info")
    async def info(self, ctx):
        """View the current settings for weather updates."""  # Edited by Taako
        try:
            guild_settings = await self.config.guild(ctx.guild).all()  # Edited by Taako
            embed_color = discord.Color(guild_settings.get("embed_color", 0xFF0000))  # Edited by Taako
            show_footer = guild_settings.get("show_footer", True)  # Edited by Taako
            time_zone = guild_settings.get("time_zone", "UTC")  # Edited by Taako
            current_season = self._get_current_season(time_zone)  # Edited by Taako

            # Calculate time until the next refresh  # Edited by Taako
            now = datetime.now(pytz.timezone(time_zone))  # Current time in the guild's time zone  # Edited by Taako
            refresh_interval = guild_settings.get("refresh_interval")  # Edited by Taako
            refresh_time = guild_settings.get("refresh_time")  # Edited by Taako
            next_refresh = None  # Edited by Taako

            if refresh_interval:  # Edited by Taako
                last_refresh = guild_settings.get("last_refresh", 0)  # Edited by Taako
                next_refresh = datetime.fromtimestamp(last_refresh, pytz.timezone(time_zone)) + timedelta(seconds=refresh_interval)  # Edited by Taako
                if next_refresh < now:  # If the next refresh time is in the past  # Edited by Taako
                    next_refresh = now + timedelta(seconds=refresh_interval)  # Recalculate to the next valid interval  # Edited by Taako
            elif refresh_time:  # Edited by Taako
                target_time = datetime.strptime(refresh_time, "%H%M").replace(  # Edited by Taako
                    tzinfo=pytz.timezone(time_zone),  # Edited by Taako
                    year=now.year,  # Edited by Taako
                    month=now.month,  # Edited by Taako
                    day=now.day,  # Edited by Taako
                )  # Edited by Taako
                if now >= target_time:  # If the target time has already passed today  # Edited by Taako
                    target_time += timedelta(days=1)  # Move to the next day  # Edited by Taako
                next_refresh = target_time  # Edited by Taako

            time_until_refresh_str = "Not scheduled"  # Edited by Taako
            if next_refresh:  # Edited by Taako
                time_until_refresh = next_refresh - now  # Edited by Taako
                days, seconds = divmod(time_until_refresh.total_seconds(), 86400)  # Edited by Taako
                hours, remainder = divmod(seconds, 3600)  # Edited by Taako
                minutes, seconds = divmod(remainder, 60)  # Edited by Taako

                time_components = []  # Edited by Taako
                if days > 0:  # Edited by Taako
                    time_components.append(f"{int(days)}d")  # Edited by Taako
                if hours > 0:  # Edited by Taako
                    time_components.append(f"{int(hours)}h")  # Edited by Taako
                time_components.append(f"{int(minutes):02}m")  # Always include minutes  # Edited by Taako
                time_components.append(f"{int(seconds):02}s")  # Always include seconds  # Edited by Taako
                time_until_refresh_str = " ".join(time_components)  # Edited by Taako

            embed = discord.Embed(
                title="🌦️ RandomWeather Settings",  # Edited by Taako
                color=embed_color  # Use the configured embed color  # Edited by Taako
            )  # Edited by Taako
            embed.add_field(
                name="📅 Refresh Mode",  # Edited by Taako
                value=(
                    f"**Interval**: {guild_settings['refresh_interval']} seconds"  # Edited by Taako
                    if guild_settings.get("refresh_interval")  # Edited by Taako
                    else f"**Time**: {guild_settings['refresh_time']} (military time)"  # Edited by Taako
                ),  # Edited by Taako
                inline=False,  # Edited by Taako
            )  # Edited by Taako
            embed.add_field(
                name="⏳ Time Until Next Refresh",  # Edited by Taako
                value=time_until_refresh_str,  # Show time until the next refresh  # Edited by Taako
                inline=False,  # Edited by Taako
            )  # Edited by Taako
            embed.add_field(
                name="🌍 Time Zone",  # Edited by Taako
                value=guild_settings.get("time_zone", "Not set"),  # Edited by Taako
                inline=False,  # Edited by Taako
            )  # Edited by Taako
            embed.add_field(
                name="📢 Channel",  # Edited by Taako
                value=(
                    f"<#{guild_settings['channel_id']}>" if guild_settings.get("channel_id") else "Not set"  # Edited by Taako
                ),  # Edited by Taako
                inline=False,  # Edited by Taako
            )  # Edited by Taako
            embed.add_field(
                name="🔔 Role Tagging",  # Edited by Taako
                value="Enabled" if guild_settings.get("tag_role") else "Disabled",  # Edited by Taako
                inline=True,  # Edited by Taako
            )  # Edited by Taako
            embed.add_field(
                name="👥 Tag Role",  # Edited by Taako
                value=(
                    f"<@&{guild_settings['role_id']}>" if guild_settings.get("role_id") else "Not set"  # Edited by Taako
                ),  # Edited by Taako
                inline=True,  # Edited by Taako
            )  # Edited by Taako
            embed.add_field(
                name="🎨 Embed Color",  # Edited by Taako
                value=str(embed_color),  # Edited by Taako
                inline=False,  # Edited by Taako
            )  # Edited by Taako
            embed.add_field(
                name="📄 Footer",  # Edited by Taako
                value="Enabled" if show_footer else "Disabled",  # Edited by Taako
                inline=False,  # Edited by Taako
            )  # Edited by Taako
            embed.add_field(
                name="🍂 Current Season",  # Edited by Taako
                value=current_season,  # Display the current season  # Edited by Taako
                inline=False,  # Edited by Taako
            )  # Edited by Taako
            embed.set_footer(text="RandomWeather by Taako")  # Edited by Taako
            await ctx.send(embed=embed)  # Edited by Taako
        except Exception as e:
            logging.error(f"[ERROR] Failed to retrieve settings for guild {ctx.guild.id}: {e}")  # Edited by Taako
            await ctx.send("An error occurred while retrieving the settings. Please try again later.")  # Edited by Taako

    @rweather.command(name="setrefresh")
    async def set_refresh(self, ctx, value: str):
        """Set how often the weather should refresh or specify a time (e.g., `10m` or `1830`)."""  # Edited by Taako
        time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}  # Edited by Taako

        if value.isdigit() and len(value) == 4:  # Handle specific time in military format (e.g., 1830)  # Edited by Taako
            await self.config.guild(ctx.guild).refresh_time.set(value)  # Edited by Taako
            await self.config.guild(ctx.guild).refresh_interval.set(None)  # Edited by Taako
            await ctx.send(f"Weather will now refresh daily at {value} (military time).")  # Edited by Taako
        elif value[-1] in time_units:  # Handle interval-based input (e.g., 10m, 1h)  # Edited by Taako
            try:
                unit = value[-1]  # Edited by Taako
                interval = int(value[:-1])  # Edited by Taako
                refresh_interval = interval * time_units[unit]  # Edited by Taako
                await self.config.guild(ctx.guild).refresh_interval.set(refresh_interval)  # Edited by Taako
                await self.config.guild(ctx.guild).refresh_time.set(None)  # Edited by Taako
                await ctx.send(f"Weather will now refresh every {value}.")  # Edited by Taako
                # Update the next refresh time to match the new interval  # Edited by Taako
                now = datetime.now()  # Edited by Taako
                next_refresh = now + timedelta(seconds=refresh_interval)  # Edited by Taako
                await self.config.guild(ctx.guild).last_refresh.set(next_refresh.timestamp())  # Edited by Taako
            except (ValueError, IndexError):  # Edited by Taako
                await ctx.send("Invalid format. Use a number followed by s (seconds), m (minutes), h (hours), or d (days).")  # Edited by Taako
        else:
            await ctx.send("Invalid format. Use a valid military time (e.g., 1830) or an interval (e.g., 10m, 1h).")  # Edited by Taako

    @rweather.command(name="set_embed_color")
    async def set_embed_color(self, ctx, color: discord.Color):
        """Set the embed color for weather updates dynamically."""  # Edited by Taako
        await self.config.guild(ctx.guild).embed_color.set(color.value)  # Edited by Taako
        await ctx.send(f"Embed color updated to: {color}")  # Edited by Taako

    @rweather.command(name="set_time_zone")
    async def set_time_zone(self, ctx, time_zone: str):
        """Set the time zone for weather updates dynamically."""  # Edited by Taako
        if time_zone in pytz.all_timezones:  # Edited by Taako
            await self.config.guild(ctx.guild).time_zone.set(time_zone)  # Edited by Taako
            await ctx.send(f"Time zone updated to: {time_zone}")  # Edited by Taako
        else:
            await ctx.send("Invalid time zone. Please provide a valid time zone.")  # Edited by Taako
