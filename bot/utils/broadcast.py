import asyncio
from aiogram import Bot

async def broadcast_message(bot: Bot, message_text: str, user_list: list[dict], sender_id: int = None, kb = None, type="text", file_id: str = None):
    for i, user in enumerate(user_list):
        try:
            if type == "text":
                await bot.send_message(user['telegram_id'], message_text, reply_markup=kb)
            elif type == "photo":
                await bot.send_photo(user['telegram_id'], photo=file_id, caption=message_text, reply_markup=kb)
            elif type == "video":
                await bot.send_video(user['telegram_id'], video=file_id, caption=message_text, reply_markup=kb)
        except Exception as e:
            print(f"Failed to send message to @{user['username']}: {e}")
            if sender_id:
                await bot.send_message(sender_id, f"⚠️ Не вдалося надіслати повідомлення користувачу @{user['username']}: {e}")
        if i % 25 == 0 and i != 0: 
            await asyncio.sleep(1)
    if sender_id:
        await bot.send_message(sender_id, "✅ Повідомлення надіслано всім користувачам.")