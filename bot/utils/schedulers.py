
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot.handlers.admin import refresh_jars_silent
from pytz import timezone

scheduler = AsyncIOScheduler(timezone=timezone("Europe/Kyiv"))

def init_jar_refresh_tasks(bot):
    scheduler.add_job(refresh_jars_silent, "cron", hour="0")
    scheduler.start()

def list_jobs():
    jobs = scheduler.get_jobs()
    return jobs
