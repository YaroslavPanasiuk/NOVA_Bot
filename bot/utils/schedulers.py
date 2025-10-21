
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot.handlers.admin import refresh_jars_progress
from pytz import timezone

scheduler = AsyncIOScheduler(timezone=timezone("Europe/Kyiv"))

def init_jar_refresh_tasks(bot):
    scheduler.add_job(refresh_jars_progress, "cron", hour="0,7,9,11,13,15,17,19,20,21,22,23", args=[bot])
    scheduler.start()

def list_jobs():
    jobs = scheduler.get_jobs()
    return jobs
