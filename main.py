import os
import time
import requests
import schedule
import discord
from discord.ext import commands
from dotenv import load_dotenv
import random as r
import datetime
from datetime import date

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

def generate_challenge():
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

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

def create_map_challenge():
    signin_payload = {
        "email": EMAIL,
        "password": PASSWORD
    }
    with requests.Session() as session:
        signin_response = session.post(SIGNIN_URL, json=signin_payload)
        signin_response.raise_for_status()

        map_challenge_payload = generate_challenge()
        challenge_response = session.post(MAP_CHALLENGE_URL, json=map_challenge_payload)
        challenge_response.raise_for_status()
        challenge_data = challenge_response.json()
        return challenge_data['token']

def get_leaderboard(challenge_token):
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

async def post_map_challenge():
    global current_challenge_token
    try:
        current_challenge_token = create_map_challenge()
        challenge_url = f"https://www.geoguessr.com/challenge/{current_challenge_token}"

        channel = bot.get_channel(CHALLENGE_CHANNEL_ID)
        await channel.send(f"GeoGuessr Challenge for the specified map: {challenge_url}")
    except Exception as e:
        print(f"Error: {e}")

async def post_leaderboard(ctx):
    try:
        channel = bot.get_channel(LEADERBOARD_CHANNEL_ID)
        if current_challenge_token is None:
            await ctx.send("No challenge has been posted yet.")
            return

        leaderboard_items = get_leaderboard(current_challenge_token)
        if not leaderboard_items:
            await channel.send("No leaderboard data available.")
            return

        leaderboard_message = f"Leaderboard for {yesterday}:\n"
        for item in leaderboard_items:
            player_name = item['playerName']
            total_score = item['totalScore']
            leaderboard_message += f"{player_name}: {total_score} points\n"

        await channel.send(leaderboard_message)
    except Exception as e:
        print(f"Error: {e}")
        await ctx.send("Error retrieving leaderboard.")

@bot.command(name='test')
async def test(ctx):
    await post_map_challenge()
    await ctx.send("Test complete: Map challenge posted.")

@bot.command(name='finish')
async def finish(ctx):
    await post_leaderboard(ctx)

def schedule_map_challenge():
    schedule.every().day.at(POST_TIME).do(lambda: bot.loop.create_task(post_map_challenge()))

schedule_map_challenge()

bot.run(DISCORD_TOKEN)

while True:
    schedule.run_pending()
    time.sleep(1)
