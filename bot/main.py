import asyncio
from aiogram import Bot, Dispatcher
from bot.config import BOT_TOKEN, INIT_RESOURCES_ON_START
from bot.utils.files import init_resources
from bot.utils.logs import setup_logging
from bot.db.database import init_db
from bot.handlers import register_handlers
from bot.db.db_listener import listen_for_changes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot.handlers.admin import refresh_jars_progress

async def main():
    setup_logging()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    register_handlers(dp)
    print("Bot started.")

    await init_db()

    if INIT_RESOURCES_ON_START == 'yes':
        await init_resources(bot)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(refresh_jars_progress, "cron", hour="0,10,15,20", args=[bot])
    scheduler.start()

    listener_task = asyncio.create_task(listen_for_changes())
    bot_task = asyncio.create_task(dp.start_polling(bot))

    await asyncio.gather(listener_task, bot_task)
    print("Bot stopped.")

if __name__ == "__main__":
    asyncio.run(main())


