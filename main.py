import asyncio
from .discord_bot import bot, setup
from .config import DISCORD_TOKEN

async def main():
    async with bot:
        await setup(bot)
        await bot.start(DISCORD_TOKEN)

asyncio.run(main())
