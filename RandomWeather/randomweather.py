import random
import discord  # Edited by Taako
from redbot.core import commands
import asyncio  # Edited by Taako

class WeatherCog(commands.Cog):
    """A cog for generating random daily weather."""
    
    # Edited by Taako
    def __init__(self, bot):
        self._bot = bot  # Store the bot instance
        self._current_weather = self._generate_weather()  # Generate initial weather
        self._role_id = None  # Role ID for tagging
        self._channel_id = None  # Channel ID for sending updates
        self._tag_role = False  # Whether to tag the role
        self._refresh_task = None  # Task for automatic weather refresh
        self._refresh_interval = None  # Refresh interval in seconds

    def _generate_weather(self):
        """Generate realistic random weather."""
        # Edited by Taako
        conditions = random.choice(["Clear sky", "Partly cloudy", "Overcast", "Rainy", "Stormy", "Snowy"])

        # Define temperature ranges based on conditions
        if conditions in ["Clear sky", "Partly cloudy"]:
            temperature = random.randint(70, 100)  # Warmer weather
        elif conditions in ["Overcast", "Rainy"]:
            temperature = random.randint(50, 80)  # Cooler weather
        elif conditions == "Stormy":
            temperature = random.randint(60, 85)  # Moderate temperature
        elif conditions == "Snowy":
            temperature = random.randint(20, 40)  # Cold weather
        else:
            temperature = random.randint(30, 100)  # Default fallback

        # Feels like temperature with a slight variation
        feels_like = temperature + random.randint(-3, 3)

        # Wind speed and direction
        if conditions == "Stormy":
            wind_speed = round(random.uniform(15.0, 40.0), 1)  # Strong winds
        elif conditions in ["Rainy", "Snowy"]:
            wind_speed = round(random.uniform(5.0, 20.0), 1)  # Moderate winds
        else:
            wind_speed = round(random.uniform(0.5, 10.0), 1)  # Light winds
        wind_direction = random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"])

        # Pressure
        if conditions == "Stormy":
            pressure = random.randint(950, 1000)  # Low pressure
        elif conditions in ["Rainy", "Snowy"]:
            pressure = random.randint(1000, 1020)  # Moderate pressure
        else:
            pressure = random.randint(1020, 1050)  # High pressure

        # Humidity
        if conditions in ["Rainy", "Stormy", "Snowy"]:
            humidity = random.randint(70, 100)  # High humidity
        else:
            humidity = random.randint(20, 60)  # Low to moderate humidity

        # Visibility
        if conditions == "Clear sky":
            visibility = round(random.uniform(5.0, 6.2), 1)  # High visibility
        elif conditions in ["Partly cloudy", "Overcast"]:
            visibility = round(random.uniform(3.0, 5.0), 1)  # Moderate visibility
        elif conditions in ["Rainy", "Stormy"]:
            visibility = round(random.uniform(0.5, 3.0), 1)  # Low visibility
        elif conditions == "Snowy":
            visibility = round(random.uniform(0.2, 1.5), 1)  # Very low visibility
        else:
            visibility = round(random.uniform(0.5, 6.2), 1)  # Default fallback

        return {
            "temperature": f"{temperature}°F",
            "feels_like": f"{feels_like}°F",
            "conditions": conditions,
            "wind": f"{wind_speed} mph {wind_direction}",
            "pressure": f"{pressure} hPa",
            "humidity": f"{humidity}%",
            "visibility": f"{visibility} miles",  # Updated to miles
        }

    def _get_weather_icon(self, condition):
        """Get an icon URL based on the weather condition."""
        # Edited by Taako
        icons = {
            "Clear sky": "https://cdn-icons-png.flaticon.com/512/869/869869.png",
            "Partly cloudy": "https://cdn-icons-png.flaticon.com/512/1146/1146869.png",
            "Overcast": "https://cdn-icons-png.flaticon.com/512/414/414825.png",
            "Rainy": "https://cdn-icons-png.flaticon.com/512/1163/1163626.png",
            "Stormy": "https://cdn-icons-png.flaticon.com/512/4668/4668778.png",  # Updated icon for Stormy
            "Snowy": "https://cdn-icons-png.flaticon.com/512/642/642102.png",
        }
        return icons.get(condition, "https://cdn-icons-png.flaticon.com/512/869/869869.png")  # Default icon

    def _create_weather_embed(self, weather_data, guild_id=None):
        """Create a Discord embed for the weather data."""
        # Edited by Taako
        icon_url = self._get_weather_icon(weather_data["conditions"])
        embed = discord.Embed(
            title="🌤️ Today's Weather", 
            color=discord.Color.red()  # Set embed color to red
        )
        embed.add_field(name="🌡️ Temperature", value=weather_data["temperature"], inline=True)
        embed.add_field(name="🌡️ Feels Like", value=weather_data["feels_like"], inline=True)
        embed.add_field(name="🌥️ Conditions", value=weather_data["conditions"], inline=False)
        embed.add_field(name="💨 Wind", value=weather_data["wind"], inline=True)
        embed.add_field(name="💧 Humidity", value=weather_data["humidity"], inline=True)
        embed.add_field(name="👀 Visibility", value=weather_data["visibility"], inline=True)
        embed.set_thumbnail(url=icon_url)  # Add a weather-specific icon

        # Add footer unless the guild ID matches the specified one
        if guild_id != 1277804371878346814:
            embed.set_footer(text="RandomWeather by Taako", icon_url="https://i.imgur.com/3ZQZ3cQ.png")
        
        return embed

    async def _refresh_weather_task(self):
        """Background task to refresh weather at the set interval."""
        # Edited by Taako
        while self._refresh_interval and self._channel_id:
            await asyncio.sleep(self._refresh_interval)
            channel = self._bot.get_channel(self._channel_id)
            if channel:
                embed = self._create_weather_embed(self._current_weather)
                role_mention = f"<@&{self._role_id}>" if self._role_id and self._tag_role else ""
                await channel.send(content=role_mention, embed=embed)

    @commands.group(name="rweather", invoke_without_command=True)
    async def rweather(self, ctx):
        """Main rweather command."""
        # Edited by Taako
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)  # Show the help menu if no subcommand is provided

    @rweather.command()
    async def refresh(self, ctx):
        """Refresh the weather for the day."""
        # Edited by Taako
        self._current_weather = self._generate_weather()
        embed = self._create_weather_embed(self._current_weather, guild_id=ctx.guild.id)
        role_mention = f"<@&{self._role_id}>" if self._role_id and self._tag_role else ""
        if self._channel_id:
            channel = self._bot.get_channel(self._channel_id)
            if channel:
                await channel.send(content=role_mention, embed=embed)
                await ctx.send(f"Weather update sent to {channel.mention}.")
            else:
                await ctx.send("The set channel is invalid. Please set a valid channel.")
        else:
            await ctx.send(embed=embed)

    @rweather.command()
    async def role(self, ctx, role_id: int):
        """Set the role to be tagged for weather updates."""
        # Edited by Taako
        role = ctx.guild.get_role(role_id)
        if role:
            self._role_id = role_id
            await ctx.send(f"Weather updates will now tag the role: {role.name}")
        else:
            await ctx.send("Invalid role ID. Please provide a valid role ID.")

    @rweather.command()
    async def toggle(self, ctx):
        """Toggle whether the role should be tagged in weather updates."""
        # Edited by Taako
        self._tag_role = not self._tag_role
        status = "enabled" if self._tag_role else "disabled"
        await ctx.send(f"Role tagging has been {status}.")

    @rweather.command()
    async def channel(self, ctx, channel_id: int):
        """Set the channel for weather updates."""
        # Edited by Taako
        channel = self._bot.get_channel(channel_id)
        if channel:
            self._channel_id = channel_id
            await ctx.send(f"Weather updates will now be sent to: {channel.mention}")
        else:
            await ctx.send("Invalid channel ID. Please provide a valid channel ID.")

    @rweather.command(name="load")
    async def load_weather(self, ctx):
        """Manually load the current weather."""
        # Edited by Taako
        embed = self._create_weather_embed(self._current_weather, guild_id=ctx.guild.id)
        role_mention = f"<@&{self._role_id}>" if self._role_id and self._tag_role else ""
        if self._channel_id:
            channel = self._bot.get_channel(self._channel_id)
            if channel:
                await channel.send(content=role_mention, embed=embed)
                await ctx.send(f"Weather update sent to {channel.mention}.")
            else:
                await ctx.send("The set channel is invalid. Please set a valid channel.")
        else:
            await ctx.send(embed=embed)

    @rweather.command(name="setrefresh")
    async def set_refresh(self, ctx, interval: str):
        """Set how often the weather should refresh in the set channel."""
        # Edited by Taako
        time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        try:
            unit = interval[-1]
            value = int(interval[:-1])
            if unit not in time_units:
                raise ValueError("Invalid time unit.")
            self._refresh_interval = value * time_units[unit]
            if self._refresh_task:
                self._refresh_task.cancel()
            if self._refresh_interval > 0:
                self._refresh_task = self._bot.loop.create_task(self._refresh_weather_task())
                await ctx.send(f"Weather will now refresh every {interval}.")
            else:
                await ctx.send("Invalid interval. Please provide a positive value.")
        except (ValueError, IndexError):
            await ctx.send("Invalid format. Use a number followed by s (seconds), m (minutes), h (hours), or d (days).")

def setup(bot):
    # Edited by Taako
    bot.add_cog(WeatherCog(bot))
