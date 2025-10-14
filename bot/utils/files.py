from io import BytesIO
from aiogram.types import BufferedInputFile
from aiogram import Bot
from bot.config import DB_CHAT_ID

async def reupload_as_photo(bot: Bot, file_id: str):
    file = await bot.get_file(file_id)
    downloaded_file = await bot.download_file(file.file_path)
    photo = BufferedInputFile(downloaded_file.read(), filename="image.jpg")
    sent_message = await bot.send_photo(chat_id=DB_CHAT_ID, photo=photo)
    new_file_id = sent_message.photo[-1].file_id
    return new_file_id
