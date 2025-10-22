
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot.handlers.admin import refresh_jars_progress
from pytz import timezone

scheduler = AsyncIOScheduler(timezone=timezone("Europe/Kyiv"))

def init_jar_refresh_tasks(bot):
    scheduler.add_job(refresh_jars_progress, "cron", hour="0", args=[bot])
    scheduler.start()

def list_jobs():
    jobs = scheduler.get_jobs()
    return jobs
