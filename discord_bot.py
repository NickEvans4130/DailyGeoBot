import discord
from discord.ext import commands
from discord.ext.commands import has_permissions
import asyncio
import random
import string
import json
import requests
from .config import config, EMAIL, PASSWORD, DISCORD_TOKEN, today, yesterday, SIGNIN_URL
from .geoguessr_api import create_map_challenge, get_leaderboard
import schedule

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

current_challenge_token = None

USER_MAPS_URL_TEMPLATE = "https://www.geoguessr.com/api/v3/profiles/maps"

# Function to save user data to JSON
def save_user_data(discord_id, geoguessr_username):
    try:
        with open('user_data.json', 'r') as f:
            user_data = json.load(f)
    except FileNotFoundError:
        user_data = {}

    user_data[discord_id] = geoguessr_username

    with open('user_data.json', 'w') as f:
        json.dump(user_data, f)

# Function to generate a unique key
def generate_unique_key():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

class SyncView(discord.ui.View):
    def __init__(self, bot, geoguessr_username, unique_key):
        super().__init__(timeout=300)
        self.bot = bot
        self.geoguessr_username = geoguessr_username
        self.unique_key = unique_key

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.primary)
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.verify_user(interaction.user, interaction)

    async def verify_user(self, user, interaction):
        try:
            signin_payload = {
                "email": EMAIL,
                "password": PASSWORD
            }
            with requests.Session() as session:
                signin_response = session.post(SIGNIN_URL, json=signin_payload)
                signin_response.raise_for_status()

                maps_response = session.get(USER_MAPS_URL_TEMPLATE)
                maps_response.raise_for_status()
                maps_data = maps_response.json()
                
                # Ensure the structure matches the JSON file
                map_names = [map_data['name'] for map_data in maps_data]
            
                if self.unique_key in map_names:
                    save_user_data(str(user.id), self.geoguessr_username)
                    await interaction.followup.send(f"Your GeoGuessr account has been successfully linked.", ephemeral=True)
                else:
                    await interaction.followup.send("The verification key was not found on your GeoGuessr account. Please try again.", ephemeral=True)
        except Exception as e:
            print(f"Error: {e}")
            await interaction.followup.send("An error occurred during verification. Please try again.", ephemeral=True)


class MyBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Logged in as {self.bot.user.name}')
        await bot.tree.sync()

    async def post_map_challenge(self):
        global current_challenge_token
        try:
            current_challenge_token = create_map_challenge()
            challenge_url = f"https://www.geoguessr.com/challenge/{current_challenge_token}"

            channel = self.bot.get_channel(config['CHALLENGE_CHANNEL_ID'])
            embed = discord.Embed(title="New GeoGuessr Challenge!", description=f"GeoGuessr Challenge for the specified map: [Play Now]({challenge_url})", color=discord.Color.green())
            embed.set_footer(text="Good luck!")
            await channel.send(embed=embed)
        except Exception as e:
            print(f"Error: {e}")

    async def post_leaderboard(self, interaction):
        try:
            channel = self.bot.get_channel(config['LEADERBOARD_CHANNEL_ID'])
            if current_challenge_token is None:
                await interaction.response.send_message("No challenge has been posted yet.")
                return

            leaderboard_items = get_leaderboard(current_challenge_token)
            if not leaderboard_items:
                await channel.send("No leaderboard data available.")
                return

            embed = discord.Embed(title=f"Leaderboard for {yesterday}", color=discord.Color.blue())
            for item in leaderboard_items:
                player_name = item['playerName']
                total_score = item['totalScore']
                embed.add_field(name=player_name, value=f"{total_score} points", inline=False)

            await channel.send(embed=embed)
            await interaction.response.send_message("Leaderboard posted.")
        except Exception as e:
            print(f"Error: {e}")
            await interaction.response.send_message("Error retrieving leaderboard.")

    @discord.app_commands.command(name="sync", description="Link your GeoGuessr account with your Discord account")
    async def sync(self, interaction: discord.Interaction, geoguessr_username: str):
        unique_key = generate_unique_key()
        user = interaction.user

        try:
            await user.send(f"Please set the following key as a map name on your GeoGuessr account: {unique_key}")
            view = SyncView(self.bot, geoguessr_username, unique_key)
            await user.send("Once you've set the key as a map name, click the button below to verify:", view=view)
            await interaction.response.send_message("A verification message has been sent to your DMs.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I couldn't send you a DM. Please make sure your DMs are open.", ephemeral=True)

    @discord.app_commands.command(name="test")
    async def test(self, interaction: discord.Interaction):
        await self.post_map_challenge()
        await interaction.response.send_message("Test complete: Map challenge posted.")

    @discord.app_commands.command(name="finish")
    async def finish(self, interaction: discord.Interaction):
        await self.post_leaderboard(interaction)

    @discord.app_commands.command(name="setup", description="Command for server admins to set the parameters for their challenge.")
    @discord.app_commands.describe(post_time="Enter what time you want the daily challenge to post",
                                   random_settings="Enter whether you want game mode parameters and time to be randomized",
                                   disable_moving="Some people don't like moving, choose 'yes' to disable moving in all challenges.",
                                   challenge_channel="Enter the channel ID for where you want the daily challenge to be posted",
                                   leaderboard_channel="Enter the channel ID for where you want the leaderboard to be posted",
                                   guild_id = "Enter the Server ID for your server"
                                   )
    @discord.app_commands.choices(
        random_settings=[
            discord.app_commands.Choice(name="Yes", value=1),
            discord.app_commands.Choice(name="No", value=2)
        ],
        disable_moving=[
            discord.app_commands.Choice(name="Yes", value=1),
            discord.app_commands.Choice(name="No", value=2)
        ]
    )
    @commands.has_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction, post_time: float, random_settings: int, disable_moving: int, challenge_channel: str, leaderboard_channel: str, guild_id: str):
        config['GUILD_ID'] = guild_id
        config['POST_TIME'] = post_time
        config['CHALLENGE_CHANNEL_ID'] = int(challenge_channel)
        config['LEADERBOARD_CHANNEL_ID'] = int(leaderboard_channel)
        config['RANDOM_SETTINGS'] = random_settings == 1
        config['DISABLE_MOVING'] = disable_moving == 1

        config_file = 'config.json'
        with open(config_file, 'a') as f:
            json.dump(config, f)

        await interaction.response.send_message("Configuration updated successfully.", ephemeral=True)

    def schedule_map_challenge(self):
        schedule.every().day.at(config['POST_TIME']).do(lambda: self.bot.loop.create_task(self.post_map_challenge()))

async def setup(bot):
    cog = MyBot(bot)
    await bot.add_cog(cog)
    cog.schedule_map_challenge()
