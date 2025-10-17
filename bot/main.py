import asyncio
from aiogram import Bot, Dispatcher
from bot.config import BOT_TOKEN, INIT_RESOURCES_ON_START
from bot.utils.files import init_resources
from bot.utils.logs import setup_logging
from bot.db.database import init_db
from bot.handlers import register_handlers

async def main():
    setup_logging()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    register_handlers(dp)
    print("Bot started.")

    await init_db()

    if INIT_RESOURCES_ON_START == 'yes':
        await init_resources(bot)
    
    await dp.start_polling(bot)
    print("Bot stopped.")

if __name__ == "__main__":
    asyncio.run(main())
