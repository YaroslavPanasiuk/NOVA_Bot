from io import BytesIO
from aiogram.types import BufferedInputFile
from aiogram import Bot

async def reupload_as_photo(bot: Bot, file_id: str):
    file = await bot.get_file(file_id)
    downloaded_file = await bot.download_file(file.file_path)
    photo = BufferedInputFile(downloaded_file.read(), filename="image.jpg")
    return photo
