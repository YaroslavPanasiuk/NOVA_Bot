from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.db import database
from bot.utils.formatters import format_profile
from bot.keyboards.common import mentor_carousel_kb, participant_confirm_profile_kb, confirm_data_processing_kb
import re
from bot.utils.validators import instagram_valid, monobank_jar_valid, fundraising_goal_valid
from bot.utils.files import reupload_as_photo
from bot.utils.texts import PARTICIPANT_INSTAGRAM_PROMPT, INVALID_INSTAGRAM, PARTICIPANT_GOAL_PROMPT, INVALID_NUMBER, SEND_AS_FILE_WARNING, NOT_IMAGE_FILE, PROFILE_SAVED_PARTICIPANT, PROFILE_CANCELLED, NO_MENTORS_AVAILABLE, NEW_PARTICIPANT_JOINED, MANAGE_YOUR_GROUP, PARTICIPANT_SELECT_MENTOR_PROMPT, PARTICIPANT_PHOTO_PROMPT, SELECTED_MENTOR, CONFIRM_PROFILE, PROFILE_CONFIRMED, INVALID_JAR_URL, PARTICIPANT_JAR_PROMPT, CONFIRM_DATA_PROCESSING, PARTICIPANT_REGISTRATION_END, MENTOR_BUTTON, PARTICIPANT_NAME_PROMPT

router = Router()

class ParticipantProfile(StatesGroup):
    select_mentor = State()
    name = State()
    instagram = State()
    fundraising_goal = State()
    photo = State()
    confirm_profile = State()
    monobank_jar = State()
    confirm_data_processing = State()


@router.callback_query(F.data == "role:participant")
async def start_participant(callback: CallbackQuery, state: FSMContext):
    mentors = await database.get_mentors()
    if not mentors:
        await callback.message.answer(NO_MENTORS_AVAILABLE)
        return

    # store mentors list in FSM
    await state.update_data(mentors=mentors, current_index=0, role="participant")

    first_mentor = mentors[0]
    text = first_mentor.get("description", "No description provided.")
    kb = mentor_carousel_kb(0, len(mentors), first_mentor["telegram_id"])

    await state.set_state(ParticipantProfile.select_mentor)
    await callback.message.answer(PARTICIPANT_SELECT_MENTOR_PROMPT)
    if first_mentor.get("photo_url"):
        photo = await reupload_as_photo(callback.bot, first_mentor.get("photo_url"))
    else:
        photo = FSInputFile("resources/default.png", filename="no-profile-picture.png")
    await callback.message.answer_photo(photo=photo, caption=text, reply_markup=kb, parse_mode="HTML")

    await callback.answer()

@router.callback_query(F.data.startswith("mentor_select:"))
async def mentor_select(callback: CallbackQuery, state: FSMContext):
    mentor_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    await state.update_data(mentor_id=mentor_id)
    await database.set_mentor(telegram_id=user_id, mentor=mentor_id)

    await database.set_participant_mentor(user_id, mentor_id)
    
    await callback.message.edit_reply_markup()
    mentor = await database.get_user_by_id(mentor_id)
    text = f"{SELECTED_MENTOR} {mentor.get('default_name') or ''})!"
    await callback.message.answer(text, parse_mode="HTML")
    await state.set_state(ParticipantProfile.name)
    await callback.message.answer(PARTICIPANT_NAME_PROMPT)
    await callback.answer()


@router.callback_query(F.data.startswith("mentor_nav:"))
async def mentor_navigation(callback: CallbackQuery, state: FSMContext):
    _, direction, index = callback.data.split(":")
    index = int(index)

    data = await state.get_data()
    mentors = data.get("mentors", [])
    if not mentors:
        return await callback.answer(NO_MENTORS_AVAILABLE, show_alert=True)

    # calculate new index
    if direction == "left":
        new_index = (index - 1) % len(mentors)
    else:  # right
        new_index = (index + 1) % len(mentors)

    await state.update_data(current_index=new_index)
    mentor = mentors[new_index]

    text = mentor.get("description", "No description provided.")
    kb = mentor_carousel_kb(new_index, len(mentors), mentor["telegram_id"])

    if mentor.get("photo_url"):
        photo = await reupload_as_photo(callback.bot, mentor.get("photo_url"))
    else:
        photo = FSInputFile("resources/default.png", filename="no-profile-picture.png")
    await callback.message.edit_media(
        media=InputMediaPhoto(media=photo, caption=text, parse_mode="HTML" ), 
        reply_markup=kb
    )
    await callback.answer()

# Name input
@router.message(ParticipantProfile.name, F.text)
async def mentor_instagram(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(ParticipantProfile.instagram)
    await database.set_default_name(telegram_id=message.from_user.id, name=message.text)
    await message.answer(PARTICIPANT_INSTAGRAM_PROMPT)

# Instagram input
@router.message(ParticipantProfile.instagram)
async def participant_instagram(message: Message, state: FSMContext):
    insta = message.text.strip()
    insta = insta.lstrip('@')

    valid = await instagram_valid(insta)

    if not valid:
        print(insta)
        await message.answer(
            INVALID_INSTAGRAM
        )
        return

    await state.update_data(instagram=insta)
    await database.set_instagram(telegram_id=message.from_user.id, instagram=insta)
    await state.set_state(ParticipantProfile.fundraising_goal)
    await message.answer(PARTICIPANT_GOAL_PROMPT)

# Fundraising goal
@router.message(ParticipantProfile.fundraising_goal)
async def participant_goal(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", ".").lstrip("грн").strip()
    valid = await fundraising_goal_valid(text, 2000)
    if not valid:
        await message.answer(INVALID_NUMBER)
        return
    try:
        goal = float(text)
    except ValueError:
        await message.answer(INVALID_NUMBER)
        return
    await state.update_data(fundraising_goal=goal)
    await database.set_goal(telegram_id=message.from_user.id, goal=goal)
    await state.set_state(ParticipantProfile.monobank_jar)
    await message.answer(PARTICIPANT_JAR_PROMPT)

# Monobank jar
@router.message(ParticipantProfile.monobank_jar)
async def mentor_goal(message: Message, state: FSMContext):

    valid = await monobank_jar_valid(message.text)

    if not valid:
        await message.answer(
            INVALID_JAR_URL
        )
        return
    await state.update_data(jar_url=message.text)
    await state.set_state(ParticipantProfile.photo)
    await database.set_jar(telegram_id=message.from_user.id, jar_url=message.text)
    await message.answer(PARTICIPANT_PHOTO_PROMPT)

# Photo
@router.message(ParticipantProfile.photo, F.photo)
async def participant_photo_compressed(message: Message, state: FSMContext):
    await message.answer(SEND_AS_FILE_WARNING)

# Uncompressed photo (file) handler
@router.message(ParticipantProfile.photo, F.document)
async def participant_photo_file(message: Message, state: FSMContext):
    # Only accept images
    if not message.document.mime_type.startswith("image/"):
        await message.answer(NOT_IMAGE_FILE)
        return

    file_id = message.document.file_id
    await state.update_data(photo_url=file_id)
    await database.set_photo(telegram_id=message.from_user.id, file_id=file_id)

    text = await format_profile(message.from_user.id)
    text += CONFIRM_PROFILE
    await state.set_state(ParticipantProfile.confirm_profile)
    await message.answer_document(document=file_id, caption=text, reply_markup=participant_confirm_profile_kb(),  parse_mode="HTML")

# Confirm participant profile
@router.callback_query(ParticipantProfile.confirm_profile, F.data.startswith("participant_confirm_profile:"))
async def participant_confirm(callback: CallbackQuery, state: FSMContext):
    confirm_str = callback.data.split(":")[1]
    if confirm_str == "yes":
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n" + PROFILE_CONFIRMED, reply_markup=None, parse_mode="HTML")

        await callback.message.answer(CONFIRM_DATA_PROCESSING, reply_markup=confirm_data_processing_kb())
    else:
        await callback.message.answer(PROFILE_CANCELLED)
    await state.set_state(ParticipantProfile.confirm_data_processing)

# Confirm data processing
@router.callback_query(ParticipantProfile.confirm_data_processing, F.data.startswith("confirm_data_processing:"))
async def participant_confirm(callback: CallbackQuery, state: FSMContext):
    confirm_str = callback.data.split(":")[1]
    if confirm_str == "yes":
        data = await state.get_data()
        await callback.message.edit_text(text=callback.message.text + "\n\n" + PROFILE_CONFIRMED, reply_markup=None, parse_mode="HTML")
        await database.save_participant_profile(
            telegram_id=callback.from_user.id,
            mentor_id=data["mentor_id"],
            instagram=data["instagram"],
            fundraising_goal=data["fundraising_goal"],
            photo_url=data["photo_url"]
        )
        await callback.message.answer(PROFILE_SAVED_PARTICIPANT)
        await callback.message.answer(PARTICIPANT_REGISTRATION_END)
        await callback.bot.send_message(data["mentor_id"], NEW_PARTICIPANT_JOINED)
        text = await format_profile(callback.from_user.id)
        await callback.bot.send_document(data["mentor_id"], document=data["photo_url"], caption=text, parse_mode="HTML")
        await callback.bot.send_message(data["mentor_id"], MANAGE_YOUR_GROUP)
    else:
        await callback.message.answer(PROFILE_CANCELLED)
    await state.clear()
    await callback.answer() 


@router.message((F.text.startswith("/mentor") ) | ( F.text == MENTOR_BUTTON))
async def remove_user_cmd(message: Message):
    user = await database.get_user_by_id(message.from_user.id)
    mentor_id = user.get('mentor_id')
    mentor = await database.get_user_by_id(mentor_id)
    text = mentor['description']

    if mentor.get("photo_url"):
        photo = await reupload_as_photo(message.bot, mentor.get("photo_url"))
    else:
        photo = FSInputFile("resources/default.png", filename="no-profile-picture.png")
    await message.answer_photo(photo=photo, caption=text, parse_mode="HTML")