
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot.handlers.admin import refresh_jars_silent
from pytz import timezone

scheduler = AsyncIOScheduler(timezone=timezone("Europe/Kyiv"))

def init_jar_refresh_tasks(bot):
    scheduler.add_job(refresh_jars_silent, "cron", hour="0,7,9,11,13,15,17,19,20,21,22,23")
    scheduler.start()

def list_jobs():
    jobs = scheduler.get_jobs()
    return jobs
