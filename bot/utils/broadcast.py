import asyncio
from aiogram import Bot

async def broadcast_message(bot: Bot, message_text: str, user_list: list[dict], sender_id: int = None):
    for i, user in enumerate(user_list):
        try:
            await bot.send_message(user['telegram_id'], message_text)
        except Exception as e:
            print(f"Failed to send message to @{user['username']}: {e}")
            if sender_id:
                await bot.send_message(sender_id, f"⚠️ Не вдалося надіслати повідомлення користувачу @{user['username']}: {e}")
        if i % 25 == 0 and i != 0: 
            await asyncio.sleep(1)
    if sender_id:
        await bot.send_message(sender_id, "✅ Повідомлення надіслано всім користувачам.")