from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.db import database
from bot.utils.formatters import format_temp_profile, format_profile
from bot.keyboards.common import mentor_confirm_profile_kb
from bot.config import ADMINS
from aiogram import Bot
import re
from aiogram.filters import Command
from bot.texts import ALREADY_REGISTERED_PARTICIPANT, MENTOR_INSTAGRAM_PROMPT, INVALID_INSTAGRAM, MENTOR_GOAL_PROMPT, PARTICIPANT_GOAL_PROMPT, INVALID_NUMBER, SEND_AS_FILE_WARNING, NOT_IMAGE_FILE, PROFILE_SAVED_MENTOR, PROFILE_CANCELLED, MENTOR_NOT_FOUND, NEW_MENTOR_PENDING, MANAGE_PENDING_MENTORS, NO_PARTICIPANTS, MY_PARTICIPANTS_HEADER, CONFIRM_PROFILE


router = Router()

class MentorProfile(StatesGroup):
    instagram = State()
    fundraising_goal = State()
    photo = State()
    confirm_profile = State()

# Start mentor registration
@router.callback_query(F.data == "role:mentor")
async def start_mentor(callback: CallbackQuery, state: FSMContext):
    user_role = await database.get_user_by_id(callback.from_user.id)
    if user_role.get("role") == "participant":
        return await callback.answer(ALREADY_REGISTERED_PARTICIPANT, show_alert=True)
    await state.set_state(MentorProfile.instagram)
    await callback.message.answer(MENTOR_INSTAGRAM_PROMPT)
    await callback.answer()

# Instagram input
@router.message(MentorProfile.instagram)
async def mentor_instagram(message: Message, state: FSMContext):
    insta = message.text.strip()
    insta = insta.lstrip('@')
    print(f"Received Instagram: {insta}")

    if not re.match(r'^(?!.*\.\.)(?!\.)(?!.*\.$)[A-Za-z0-9._]{5,30}$', insta):
        await message.answer(
            INVALID_INSTAGRAM
        )
        return
    await state.update_data(instagram=insta, role="mentor")
    await state.set_state(MentorProfile.fundraising_goal)
    await database.set_instagram(telegram_id=message.from_user.id, instagram=insta)
    await message.answer(MENTOR_GOAL_PROMPT)

# Fundraising goal
@router.message(MentorProfile.fundraising_goal)
async def mentor_goal(message: Message, state: FSMContext):
    try:
        goal = float(message.text)
        await state.update_data(fundraising_goal=goal)
        await database.set_goal(telegram_id=message.from_user.id, goal=goal)
        await state.set_state(MentorProfile.photo)
        await message.answer(PARTICIPANT_GOAL_PROMPT)
    except ValueError:
        await message.answer(INVALID_NUMBER)

# Photo
@router.message(MentorProfile.photo, F.photo)
async def mentor_photo_compressed(message: Message, state: FSMContext):
    await message.answer(SEND_AS_FILE_WARNING)
  
@router.message(MentorProfile.photo, F.document)
async def mentor_photo_file(message: Message, state: FSMContext):
    # Accept only images
    if not message.document.mime_type.startswith("image/"):
        await message.answer(NOT_IMAGE_FILE)
        return

    file_id = message.document.file_id
    await state.update_data(photo_url=file_id)
    await database.set_photo(telegram_id=message.from_user.id, file_id=file_id)

    data = await state.get_data()
    await database.update_mentor_status(message.from_user.id, "pending")
    text = await format_temp_profile(message.from_user.id, data)
    text += CONFIRM_PROFILE
    await state.set_state(MentorProfile.confirm_profile)
    await message.answer_document(document=file_id, caption=text, reply_markup=mentor_confirm_profile_kb(), parse_mode="HTML")

# Confirm mentor profile
@router.callback_query(F.data.startswith("mentor_confirm_profile:"))
async def mentor_confirm(callback: CallbackQuery, state: FSMContext):
    confirm_str = callback.data.split(":")[1]
    if confirm_str == "yes":
        data = await state.get_data()
        await database.save_mentor_profile(
            telegram_id=callback.from_user.id,
            instagram=data["instagram"],
            fundraising_goal=data["fundraising_goal"],
            photo_url=data["photo_url"]
        )
        await callback.message.answer(PROFILE_SAVED_MENTOR)
        await notify_admins(callback.message.bot, callback.from_user.id)
    else:
        await callback.message.answer(PROFILE_CANCELLED)
    await state.clear()
    await callback.answer() 


async def notify_admins(bot: Bot, mentor_id: int):
    mentor = await database.get_user_by_id(mentor_id)
    if not mentor:
        print(MENTOR_NOT_FOUND)
        return
    
    text = await format_profile(mentor_id)
    if mentor.get("photo_url"):
        document = mentor["photo_url"]
    else:
        document = FSInputFile("resources/default.png", filename="no-profile-picture.png")
    print("admins", ADMINS)
    for admin_id in ADMINS:
        try:
            await bot.send_message(admin_id, NEW_MENTOR_PENDING)
            await bot.send_document(admin_id, document=document, caption=text, parse_mode="HTML")
            await bot.send_message(admin_id, MANAGE_PENDING_MENTORS)
        except Exception as e:
            print(f"Failed to notify admin {admin_id}: {e}")


@router.message(Command("team"))
async def my_participants(message: Message):
    mentor_id = message.from_user.id
    participants = await database.get_participants_of_mentor(mentor_id)

    if not participants:
        await message.answer(NO_PARTICIPANTS)
        return

    text = MY_PARTICIPANTS_HEADER
    for p in participants:
        text += f"• {p.get('first_name', '')} {p.get('last_name', '')} @{p.get('username', '')} — Instagram: {p.get('instagram', '—')}\n"

    await message.answer(text)

