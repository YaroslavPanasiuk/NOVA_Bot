from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.db import database
from bot.utils.formatters import format_profile, format_profile_image, format_mentor_profile_view, format_design_preference, format_design_photos
from bot.keyboards.common import mentor_confirm_profile_kb, mentor_confirm_profile_view_kb, confirm_kb, select_design_kb, cancel_registration_kb, menu_kb
from bot.keyboards.admin import select_user_kb
from bot.config import ADMINS
from aiogram import Bot
from bot.utils.files import reupload_as_photo
from bot.utils.validators import instagram_valid, monobank_jar_valid, fundraising_goal_valid
import re
from aiogram.filters import Command
from bot.utils.texts import ALREADY_REGISTERED_PARTICIPANT, MENTOR_INSTAGRAM_PROMPT, INVALID_INSTAGRAM, MENTOR_GOAL_PROMPT, MENTOR_PHOTO_PROMPT, INVALID_NUMBER, SEND_AS_FILE_WARNING, NOT_IMAGE_FILE, PROFILE_SAVED_MENTOR, PROFILE_CANCELLED, MENTOR_NOT_FOUND, NEW_MENTOR_PENDING, MANAGE_PENDING_MENTORS, NO_PARTICIPANTS, MY_PARTICIPANTS_HEADER, CONFIRM_PROFILE, MENTOR_DESCRIPTION_PROMPT, PROFILE_CONFIRMED, CONFIRM_PROFILE_VIEW, INVALID_JAR_URL, MENTOR_JAR_PROMPT, TEAM_BUTTON, PROFILE_VIEW_BUTTON, CHANGE_DESCRIPTION_BUTTON, CHANGE_DESCRIPTION_MSG, NEW_DESCRIPTION_SET, CHANGE_GOAL_BUTTON, NEW_GOAL_SET, CHANGE_INSTAGRAM_BUTTON, NEW_INSTAGRAM_SET, CHANGE_MONOBANK_BUTTON, NEW_MONOBANK_SET, CHANGE_GOAL_MSG, CHANGE_INSTAGRAM_MSG, CHANGE_MONOBANK_MSG, MENTOR_NAME_PROMPT, PENDING_PARTICIPANTS_BUTTON, NOT_ADMIN, NO_PENDING_PARTICIPANTS, USER_NOT_FOUND, PARTICIPANT_APPROVED, YOU_HAVE_BEEN_APPROVED_PARTICIPANT, PARTICIPANT_REJECTED, MENTOR_DESIGN_PROMPT


router = Router()

class MentorProfile(StatesGroup):
    instagram = State()
    name = State()
    fundraising_goal = State()
    photo = State()
    confirm_profile_info = State()
    description = State()
    confirm_profile_view = State()
    monobank_jar = State()
    change_description = State()
    change_goal = State()
    change_monobank = State()
    change_instagram = State()
    design_preference = State()


# Start mentor registration
@router.callback_query(F.data == "role:mentor")
async def start_mentor(callback: CallbackQuery, state: FSMContext):
    kb = cancel_registration_kb()
    await state.set_state(MentorProfile.name)
    await callback.message.answer(MENTOR_NAME_PROMPT, reply_markup=kb)
    await callback.answer()

# Name input
@router.message(MentorProfile.name, F.text)
async def mentor_instagram(message: Message, state: FSMContext):
    await state.update_data(name=message.text, role="mentor")
    await state.set_state(MentorProfile.instagram)
    await database.set_default_name(telegram_id=message.from_user.id, name=message.text)
    await message.answer(MENTOR_INSTAGRAM_PROMPT)

# Instagram input
@router.message(MentorProfile.instagram)
async def mentor_instagram(message: Message, state: FSMContext):
    insta = message.text.strip()
    insta = insta.lstrip('@')

    valid = await instagram_valid(insta)

    if not valid:
        await message.answer(
            INVALID_INSTAGRAM
        )
        return
    await state.update_data(instagram=insta)
    await state.set_state(MentorProfile.fundraising_goal)
    await database.set_instagram(telegram_id=message.from_user.id, instagram=insta)
    await message.answer(MENTOR_GOAL_PROMPT)

# Fundraising goal
@router.message(MentorProfile.fundraising_goal)
async def mentor_goal(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", ".").lstrip("грн").strip()
    valid = await fundraising_goal_valid(text, 50000)
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
    await state.set_state(MentorProfile.monobank_jar)
    await message.answer(MENTOR_JAR_PROMPT)

# Monobank jar
@router.message(MentorProfile.monobank_jar)
async def mentor_goal(message: Message, state: FSMContext):

    valid = await monobank_jar_valid(message.text)

    if not valid:
        await message.answer(
            INVALID_JAR_URL
        )
        return
    await state.update_data(jar_url=message.text)
    await state.set_state(MentorProfile.description)
    await database.set_jar(telegram_id=message.from_user.id, jar_url=message.text)
    await message.answer(MENTOR_DESCRIPTION_PROMPT)

# Description
@router.message(MentorProfile.description, F.text)
async def mentor_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await database.set_description(telegram_id=message.from_user.id, description=message.text)
    await state.set_state(MentorProfile.photo)
    await message.answer(MENTOR_PHOTO_PROMPT)

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
    compressed_id = await reupload_as_photo(message.bot, file_id)
    await state.update_data(photo_url=file_id)
    await database.set_photo(telegram_id=message.from_user.id, file_id=file_id)
    await database.set_photo(telegram_id=message.from_user.id, file_id=compressed_id, type='photo_compressed')

    await database.update_status(message.from_user.id, "pending")
    await state.set_state(MentorProfile.design_preference)
    kb = select_design_kb()
    media = await format_design_photos()
    await message.answer_media_group(media=media, caption=MENTOR_DESIGN_PROMPT, reply_markup=kb)
    await message.answer(MENTOR_DESIGN_PROMPT, reply_markup=kb)

# Design
@router.callback_query(MentorProfile.design_preference, F.data.startswith("design_preference:"))
async def mentor_confirm(callback: CallbackQuery, state: FSMContext):
    design_preference = format_design_preference(callback.data.split(":")[1])
    await database.set_design_preference(callback.from_user.id, design_preference)
    await callback.message.edit_text(callback.message.text + f"\n\nТи обрав: {design_preference}")
    photo = await format_profile_image(callback.from_user.id)
    text = await format_profile(callback.from_user.id)
    text += CONFIRM_PROFILE
    await state.set_state(MentorProfile.confirm_profile_info)
    await callback.message.answer_document(document=photo, caption=text, reply_markup=mentor_confirm_profile_kb(),  parse_mode="HTML")

# Confirm mentor profile
@router.callback_query(MentorProfile.confirm_profile_info, F.data.startswith("mentor_confirm_profile:"))
async def mentor_confirm(callback: CallbackQuery, state: FSMContext):
    confirm_str = callback.data.split(":")[1]
    if confirm_str == "yes":
        await state.set_state(MentorProfile.confirm_profile_view)
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n" + PROFILE_CONFIRMED, reply_markup=None, parse_mode="HTML")

        photo, text = await format_mentor_profile_view(callback.from_user.id)
        await callback.message.answer(CONFIRM_PROFILE_VIEW)
        await callback.message.answer_photo(photo=photo, caption=text, reply_markup=mentor_confirm_profile_view_kb(), parse_mode="HTML")
    else:
        await callback.message.answer(PROFILE_CANCELLED)
        await state.clear()
    await callback.answer() 

# Confirm mentor profile
@router.callback_query(MentorProfile.confirm_profile_view, F.data.startswith("mentor_confirm_profile:"))
async def mentor_confirm(callback: CallbackQuery, state: FSMContext):
    confirm_str = callback.data.split(":")[1]
    if confirm_str == "yes":
        data = await state.get_data()
        await state.set_state(MentorProfile.confirm_profile_view)
        await database.save_mentor_profile(
            telegram_id=callback.from_user.id,
            instagram=data["instagram"],
            fundraising_goal=data["fundraising_goal"],
        )
        await callback.message.edit_reply_markup()
        user = await database.get_user_by_id(callback.from_user.id)
        await callback.message.answer(PROFILE_SAVED_MENTOR, reply_markup=menu_kb(user))
        await notify_admins(callback.message.bot, callback.from_user.id)
    else:
        await callback.message.answer(PROFILE_CANCELLED)
    await callback.answer() 


async def notify_admins(bot: Bot, mentor_id: int):
    mentor = await database.get_user_by_id(mentor_id)
    if not mentor:
        print(MENTOR_NOT_FOUND)
        return
    
    text = await format_profile(mentor_id)
    document = await format_profile_image(mentor_id)
    print("admins", ADMINS)
    for admin_id in ADMINS:
        try:
            await bot.send_message(admin_id, NEW_MENTOR_PENDING)
            await bot.send_document(admin_id, document=document, caption=text, parse_mode="HTML")
            await bot.send_message(admin_id, MANAGE_PENDING_MENTORS)
        except Exception as e:
            print(f"Failed to notify admin {admin_id}: {e}")


@router.message((F.text == "/team" ) | ( F.text == TEAM_BUTTON))
async def my_participants(message: Message):
    mentor_id = message.from_user.id
    participants = await database.get_participants_of_mentor(mentor_id)

    if not participants:
        await message.answer(NO_PARTICIPANTS)
        return

    text = MY_PARTICIPANTS_HEADER
    for p in participants:
        text += f"• {p.get('first_name', '')} {p.get('last_name', '')} @{p.get('username', '')} — Банка: {p.get('jar_url', '—')}\n"

    await message.answer(text)


@router.message((F.text == "/profile_view" ) | ( F.text == PROFILE_VIEW_BUTTON))
async def show_my_profile_view(message: Message):
    telegram_id = message.from_user.id    
    photo, text = await format_mentor_profile_view(telegram_id)
    await message.answer_photo(photo=photo, caption=text, parse_mode="HTML")


@router.message((F.text == "/change_description" ) | ( F.text == CHANGE_DESCRIPTION_BUTTON))
async def change_description(message: Message, state: FSMContext):
    user = await database.get_user_by_id(message.from_user.id)
    await message.answer(CHANGE_DESCRIPTION_MSG.format(current_description=user['description']))
    await state.set_state(MentorProfile.change_description)


@router.message(MentorProfile.change_description, F.text)
async def set_description(message: Message, state: FSMContext):
    await database.set_description(telegram_id=message.from_user.id, description=message.text)
    await state.clear()
    await message.answer(NEW_DESCRIPTION_SET)


@router.message((F.text == "/change_goal" ) | ( F.text == CHANGE_GOAL_BUTTON))
async def change_goal(message: Message, state: FSMContext):
    user = await database.get_user_by_id(message.from_user.id)
    await message.answer(CHANGE_GOAL_MSG.format(current_goal=user['fundraising_goal']))
    await state.set_state(MentorProfile.change_goal)


@router.message(MentorProfile.change_goal, F.text)
async def set_goal(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", ".").lstrip("грн").strip()
    valid = await fundraising_goal_valid(text, 50000)
    if not valid:
        await message.answer(INVALID_NUMBER)
        return
    try:
        goal = float(text)
    except ValueError:
        await message.answer(INVALID_NUMBER)
        return
    await database.set_goal(telegram_id=message.from_user.id, goal=goal)
    await state.clear()
    await message.answer(NEW_GOAL_SET)


@router.message((F.text == "/change_monobank" ) | ( F.text == CHANGE_MONOBANK_BUTTON))
async def change_monobank(message: Message, state: FSMContext):
    user = await database.get_user_by_id(message.from_user.id)
    await message.answer(CHANGE_MONOBANK_MSG.format(current_monobank=user['jar_url']))
    await state.set_state(MentorProfile.change_monobank)


@router.message(MentorProfile.change_monobank, F.text)
async def set_monobank(message: Message, state: FSMContext):
    valid = await monobank_jar_valid(message.text)

    if not valid:
        await message.answer(
            INVALID_JAR_URL
        )
        return
    await database.set_jar(telegram_id=message.from_user.id, jar_url=message.text)
    await state.clear()
    await message.answer(NEW_MONOBANK_SET)


@router.message((F.text == "/change_instagram" ) | ( F.text == CHANGE_INSTAGRAM_BUTTON))
async def change_instagram(message: Message, state: FSMContext):
    user = await database.get_user_by_id(message.from_user.id)
    await message.answer(CHANGE_INSTAGRAM_MSG.format(current_instagram=user['instagram']))
    await state.set_state(MentorProfile.change_instagram)


@router.message(MentorProfile.change_instagram, F.text)
async def set_instagram(message: Message, state: FSMContext):
    insta = message.text.strip()
    insta = insta.lstrip('@')

    valid = await instagram_valid(insta)

    if not valid:
        await message.answer(
            INVALID_INSTAGRAM
        )
        return
    await database.set_instagram(telegram_id=message.from_user.id, instagram=message.text)
    await state.clear()
    await message.answer(NEW_INSTAGRAM_SET)


@router.message((F.text == "/pending_participants" ) | ( F.text == PENDING_PARTICIPANTS_BUTTON))
async def list_pending_participants(message: Message):
    user = await database.get_user_by_id(message.from_user.id)
    if not (user['role'] == 'mentor' and user['status'] == 'approved'):
        return await message.answer(NOT_ADMIN)

    participants = await database.get_pending_participants(user['telegram_id'])

    if not participants:
        return await message.answer(NO_PENDING_PARTICIPANTS)

    await message.answer(
        "Учасники, які очікують затвердження:",
        reply_markup=select_user_kb(participants, 'select_participant')
    )

@router.callback_query(F.data.startswith("select_participant:"))
async def select_participant(callback: CallbackQuery):
    user = await database.get_user_by_id(callback.from_user.id)
    if not (user['role'] == 'mentor' and user['status'] == 'approved'):
        return await callback.answer(NOT_ADMIN)

    participant_id = int(callback.data.split(":")[1])
    participant = await database.get_user_by_id(participant_id)

    if not participant:
        return await callback.answer(USER_NOT_FOUND, show_alert=True)

    text = await format_profile(participant_id)
    document = await format_profile_image(participant_id)

    await callback.message.answer_document(
        document=document,
        caption=text,
        reply_markup=confirm_kb(f'approve_participant:{participant_id}'),
        parse_mode="HTML"
    )
    await callback.message.edit_reply_markup()
    await callback.answer()


@router.callback_query(F.data.startswith("approve_participant:") & F.data.endswith(":yes"))
async def approve_participant(callback: CallbackQuery):
    user = await database.get_user_by_id(callback.from_user.id)
    print(callback.data)
    if not (user['role'] == 'mentor' and user['status'] == 'approved'):
        return await callback.answer(NOT_ADMIN)

    participant_id = int(callback.data.split(":")[1])
    await database.update_status(participant_id, "approved")
    await callback.message.edit_text(PARTICIPANT_APPROVED)
    await callback.bot.send_message(chat_id=participant_id, text=YOU_HAVE_BEEN_APPROVED_PARTICIPANT)
    await callback.answer("Approved ✅")



@router.callback_query(F.data.startswith("approve_participant:") & F.data.endswith(":no"))
async def reject_participant(callback: CallbackQuery):
    user = await database.get_user_by_id(callback.from_user.id)
    if not (user['role'] == 'mentor' and user['status'] == 'approved'):
        return await callback.answer(NOT_ADMIN)

    participant_id = int(callback.data.split(":")[1])
    await database.update_status(participant_id, "declined")
    await callback.message.edit_text(PARTICIPANT_REJECTED)
    await callback.bot.send_message(chat_id=participant_id, text=YOU_HAVE_BEEN_APPROVED_PARTICIPANT)
    await callback.answer("Rejected ❌")