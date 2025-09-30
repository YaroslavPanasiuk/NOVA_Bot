from aiogram import Dispatcher
from . import start, mentor, participant, admin  # import all router modules

def register_handlers(dp: Dispatcher):
    dp.include_router(start.router)
    dp.include_router(mentor.router)
    dp.include_router(participant.router)
    dp.include_router(admin.router)
