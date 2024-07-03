import requests
import random
from .config import EMAIL, PASSWORD, SIGNIN_URL, MAP_CHALLENGE_URL, LEADERBOARD_URL_TEMPLATE, USER_MAPS_URL_TEMPLATE, config

def generate_challenge():
    maps = [
        "62a44b22040f04bd36e8a914",
        "63f3ff1e0355e40ded075e0c",
        "64919f3c95165ff26469091a",
        "6165f7176c26ac00016bca3d",
        "643dbc7ccc47d3a344307998",
        "6089bfcff6a0770001f645dd"
    ]
    
    if config['RANDOM_SETTINGS']:
        options = [[True,True,True],[True,False,False],[False,False,False]]
        gamemode = random.choice(options)
        time_limit = random.randint(10,100)
    else:
        gamemode = [not config['DISABLE_MOVING'], True, True]  # Example fixed settings
        time_limit = 60  # Example fixed time limit

    params = {
        "map": random.choice(maps),
        "forbidMoving": gamemode[0],
        "forbidZooming": gamemode[1],
        "forbidRotating": gamemode[2],
        "timeLimit": time_limit,
        "type": "standard"
    }
    return params

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
