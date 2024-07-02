import os
import time
import requests
import schedule
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import random as r
import datetime
from datetime import date
import asyncio

today = date.today()
yesterday = (today - datetime.timedelta(days=1)).strftime("%d/%m/%Y")

# Load environment variables
load_dotenv()
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CHALLENGE_CHANNEL_ID = int(os.getenv('CHALLENGE_CHANNEL_ID'))
LEADERBOARD_CHANNEL_ID = int(os.getenv("LEADERBOARD_CHANNEL_ID"))

POST_TIME = os.getenv('POST_TIME')

# GeoGuessr API endpoints
SIGNIN_URL = "https://www.geoguessr.com/api/v3/accounts/signin"
MAP_CHALLENGE_URL = "https://www.geoguessr.com/api/v3/challenges"
LEADERBOARD_URL_TEMPLATE = "https://www.geoguessr.com/api/v3/results/highscores/{challenge_token}"

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

current_challenge_token = None

class MyBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def generate_challenge(self):
        maps = ["62a44b22040f04bd36e8a914","63f3ff1e0355e40ded075e0c","64919f3c95165ff26469091a","6165f7176c26ac00016bca3d","643dbc7ccc47d3a344307998","6089bfcff6a0770001f645dd"]
        options = [[True,True,True],[True,False,False],[False,False,False]]

        gamemode = r.choice(options)

        params = {
            "map": r.choice(maps),
            "forbidMoving": gamemode[0],
            "forbidZooming": gamemode[1],
            "forbidRotating": gamemode[2],
            "timeLimit": r.randint(10,100),
            "type": "standard"
        }
        return params

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Logged in as {self.bot.user.name}')
        await bot.tree.sync()

    def create_map_challenge(self):
        signin_payload = {
            "email": EMAIL,
            "password": PASSWORD
        }
        with requests.Session() as session:
            signin_response = session.post(SIGNIN_URL, json=signin_payload)
            signin_response.raise_for_status()

            map_challenge_payload = self.generate_challenge()
            challenge_response = session.post(MAP_CHALLENGE_URL, json=map_challenge_payload)
            challenge_response.raise_for_status()
            challenge_data = challenge_response.json()
            return challenge_data['token']

    def get_leaderboard(self, challenge_token):
        signin_payload = {
            "email": EMAIL,
            "password": PASSWORD
        }
        with requests.Session() as session:
            signin_response = session.post(SIGNIN_URL, json=signin_payload)
            signin_response.raise_for_status()

            leaderboard_url = LEADERBOARD_URL_TEMPLATE.format(challenge_token=challenge_token)
            leaderboard_response = session.get(leaderboard_url)
            leaderboard_response.raise_for_status()
            leaderboard_data = leaderboard_response.json()
            return leaderboard_data['items']

    async def post_map_challenge(self):
        global current_challenge_token
        try:
            current_challenge_token = self.create_map_challenge()
            challenge_url = f"https://www.geoguessr.com/challenge/{current_challenge_token}"

            channel = self.bot.get_channel(CHALLENGE_CHANNEL_ID)
            embed = discord.Embed(title="New GeoGuessr Challenge!", description=f"GeoGuessr Challenge for the specified map: [Play Now]({challenge_url})", color=discord.Color.green())
            embed.set_footer(text="Good luck!")
            await channel.send(embed=embed)
        except Exception as e:
            print(f"Error: {e}")

    async def post_leaderboard(self, interaction):
        try:
            channel = self.bot.get_channel(LEADERBOARD_CHANNEL_ID)
            if current_challenge_token is None:
                await interaction.response.send_message("No challenge has been posted yet.")
                return

            leaderboard_items = self.get_leaderboard(current_challenge_token)
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

    @discord.app_commands.command(name="test")
    async def test(self, interaction: discord.Interaction):
        await self.post_map_challenge()
        await interaction.response.send_message("Test complete: Map challenge posted.")

    @discord.app_commands.command(name="finish")
    async def finish(self, interaction: discord.Interaction):
        await self.post_leaderboard(interaction)

    def schedule_map_challenge(self):
        schedule.every().day.at(POST_TIME).do(lambda: self.bot.loop.create_task(self.post_map_challenge()))

async def setup(bot):
    cog = MyBot(bot)
    await bot.add_cog(cog)
    cog.schedule_map_challenge()

@bot.event
async def on_ready():
    await bot.tree.sync()  # Sync the slash commands with Discord

async def main():
    async with bot:
        await setup(bot)
        await bot.start(DISCORD_TOKEN)

asyncio.run(main())
