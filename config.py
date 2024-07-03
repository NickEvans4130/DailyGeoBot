import os
import json
from dotenv import load_dotenv
import datetime
from datetime import date

# Load environment variables
load_dotenv()
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
POST_TIME = os.getenv('POST_TIME')

# Load or initialize configuration
config_file = 'config.json'
if os.path.exists(config_file):
    with open(config_file, 'r') as f:
        config = json.load(f)
else:
    config = {
        "CHALLENGE_CHANNEL_ID": int(os.getenv('CHALLENGE_CHANNEL_ID')),
        "LEADERBOARD_CHANNEL_ID": int(os.getenv("LEADERBOARD_CHANNEL_ID")),
        "POST_TIME": POST_TIME,
        "RANDOM_SETTINGS": True,
        "DISABLE_MOVING": False
    }

today = date.today()
yesterday = (today - datetime.timedelta(days=1)).strftime(r"%d/%m/%Y")
