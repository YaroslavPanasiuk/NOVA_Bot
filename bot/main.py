import asyncio
from aiogram import Bot, Dispatcher
from bot.config import BOT_TOKEN, INIT_RESOURCES_ON_START
from bot.utils.files import init_resources
from bot.utils.logs import setup_logging
from bot.db.database import init_db
from bot.handlers import register_handlers
from bot.db.db_listener import listen_for_changes
from bot.utils.schedulers import init_jar_refresh_tasks

async def main():
    setup_logging()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    register_handlers(dp)
    print("Bot started.")

    await init_db()

    init_jar_refresh_tasks(bot)

    if INIT_RESOURCES_ON_START == 'yes':
        await init_resources(bot)

    listener_task = asyncio.create_task(listen_for_changes())
    bot_task = asyncio.create_task(dp.start_polling(bot))

    await asyncio.gather(listener_task, bot_task)
    print("Bot stopped.")

if __name__ == "__main__":
    asyncio.run(main())


