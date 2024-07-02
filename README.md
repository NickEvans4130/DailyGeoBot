# Welcome to DailyGeo!

## What does the bot do?
DailyGeo is a discord bot that will post geoguessr challenges every day at a specified time (might make it so individual server admins can set the time to what best suits them). The bot randomly chooses a gamemode out of moving, no move and nmpz. The time per round is currently randomly selected to be between 10 and 100 seconds although this is also subject to change. 

## How do you set up daily geo? 
First you will need to add DailyGeo to your server via this link `https://discord.com/oauth2/authorize?client_id=1246070988408487987&permissions=215040&scope=bot`
Once the bot is installed, you will need to create a channel for your daily challenge and scoreboard posts. I would recommend these to be both only accessible for server admins and the bot so that it doesn't get filled and people can't find the link. (bot is currently hard coded with IDs but hoping to automate ID setup as per next para) 
Then, run !setupChannels along with the IDs for each channel in the order, daily challenge, scoreboard. For example `!setupChannels 1234567891011 1234567891012` . Since you are using channel IDs, you can name the channel whatever you would like. If you right click a channel and cannot see an option to copy the ID, you need to enable developer mode by going to settings, scrolling down to "Advanced" and enabling "Developer Mode"
![image](https://github.com/NickEvans4130/DailyGeo/assets/105942777/c051bcea-25bc-494d-abb3-27dd41d6ebfb)
