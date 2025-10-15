from io import BytesIO
from aiogram.types import BufferedInputFile
from aiogram import Bot
from bot.config import DB_CHAT_ID
from bot.db import database
from aiogram.types import FSInputFile
from pathlib import Path
import os

async def reupload_as_photo(bot: Bot, file_id: str):
    file = await bot.get_file(file_id)
    downloaded_file = await bot.download_file(file.file_path)
    photo = BufferedInputFile(downloaded_file.read(), filename="image.jpg")
    sent_message = await bot.send_photo(chat_id=DB_CHAT_ID, photo=photo)
    new_file_id = sent_message.photo[-1].file_id
    return new_file_id

async def init_resources(bot: Bot):
    for photo in os.listdir("resources/photos"):
        filename = Path(photo).stem
        file_path = os.path.join("resources/photos", photo)
        if os.path.isfile(file_path):
            file_to_send = FSInputFile(file_path, filename=photo)
            compressed = await bot.send_photo(DB_CHAT_ID, file_to_send, caption=filename)
            uncompressed = await bot.send_document(DB_CHAT_ID, file_to_send, caption=filename)
            await database.add_file(name=f"{filename}_uncompressed", file_id=uncompressed.document.file_id, type="photo_uncompressed")
            await database.add_file(name=f"{filename}_compressed", file_id=compressed.photo[-1].file_id, type="photo_compressed")

    for video in os.listdir("resources/videos"):
        filename = Path(video).stem
        file_path = os.path.join("resources/videos", video)
        if os.path.isfile(file_path):
            file_to_send = FSInputFile(file_path, filename=video)
            msg = await bot.send_video(DB_CHAT_ID, file_to_send, caption=filename)
            await database.add_file(name=f"{filename}", file_id=msg.video.file_id, type="video")

    for animation in os.listdir("resources/animations"):
        filename = Path(animation).stem
        file_path = os.path.join("resources/animations", animation)
        if os.path.isfile(file_path):
            file_to_send = FSInputFile(file_path, filename=animation)
            msg = await bot.send_animation(DB_CHAT_ID, file_to_send, caption=filename)
            await database.add_file(name=f"{filename}", file_id=msg.animation.file_id, type="animation")

