from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from bot.db import database
from decimal import Decimal
from bot.utils.formatters import format_profile, format_profile_image, format_mentor_profile_view, format_design_preference, format_design_photos
from bot.keyboards.common import mentor_confirm_profile_kb, mentor_confirm_profile_view_kb, confirm_kb, select_design_kb, cancel_registration_kb, menu_kb
from bot.keyboards.admin import select_user_kb
from bot.config import ADMINS
from aiogram import Bot
from bot.utils.files import reupload_as_photo
from bot.utils.spreadsheets import export_users_to_sheet
from bot.utils.validators import instagram_valid, monobank_jar_valid, fundraising_goal_valid
from bot.utils.texts import *


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

    valid = instagram_valid(insta)

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
    valid = fundraising_goal_valid(text)
    if not valid:
        await message.answer(INVALID_NUMBER)
        return
    if Decimal(text) < 50000:
        return await message.answer(GOAL_TOO_LOW.format(min='50000'))
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

    valid = monobank_jar_valid(message.text)

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
    file_id = message.document.file_id

    try:
        # Try reuploading as a photo
        compressed_id = await reupload_as_photo(message.bot, file_id)

        await state.update_data(photo_url=file_id)
        await database.set_uncompressed_photo(telegram_id=message.from_user.id, file_id=file_id)
        await database.set_compressed_photo(telegram_id=message.from_user.id, file_id=compressed_id)

        await database.update_status(message.from_user.id, "pending")
        await state.set_state(MentorProfile.confirm_profile_info)

        photo = await format_profile_image(message.from_user.id)
        text = await format_profile(message.from_user.id)
        text += CONFIRM_PROFILE

        await message.answer_document(
            document=photo,
            caption=text,
            reply_markup=mentor_confirm_profile_kb(),
            parse_mode="HTML"
        )

    except TelegramBadRequest as e:
        error_text = str(e)
        if "file is too big" in error_text:
            await message.answer("⚠️ Файл завеликий. Будь ласка, завантаж зображення менше 20 МБ.")
        elif "PHOTO_INVALID_DIMENSIONS" in error_text:
            await message.answer("⚠️ Недопустимі розміри зображення. Спробуй інше фото.")
        elif "IMAGE_PROCESS_FAILED" in error_text:
            await message.answer("⚠️ Не вдалося обробити зображення. Переконайся, що це справжнє фото (JPEG або PNG).")
        else:
            # For any other Telegram Bad Request
            await message.answer(f"⚠️ Помилка під час обробки зображення. Спробуй інше фото")

    except Exception as e:
        # Catch unexpected exceptions (e.g. network, DB)
        await message.answer("❌ Сталася неочікувана помилка при обробці фото.")
        print("Error during mentor_photo_file:", e)

# Confirm mentor profile
@router.callback_query(MentorProfile.confirm_profile_info, F.data.startswith("mentor_confirm_profile:"))
async def mentor_confirm(callback: CallbackQuery, state: FSMContext):
    confirm_str = callback.data.split(":")[1]
    if confirm_str == "yes":
        await state.set_state(MentorProfile.confirm_profile_view)
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n" + PROFILE_CONFIRMED, reply_markup=None, parse_mode="HTML")
        await callback.message.answer(CONFIRM_PROFILE_VIEW)
        photo, text, type = await format_mentor_profile_view(callback.from_user.id)
        kb = mentor_confirm_profile_kb()
        if type == 'animation':
            await callback.message.answer_animation(animation=photo, caption=text, reply_markup=kb, parse_mode="HTML")
        if type == 'video':
            await callback.message.answer_video(video=photo, caption=text, reply_markup=kb, parse_mode="HTML")
        if type == 'photo':
            await callback.message.answer_photo(photo=photo, caption=text, reply_markup=kb, parse_mode="HTML")
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
        await export_users_to_sheet()
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
        text += f"• {p.get('default_name', '')} (@{p.get('username', '')}): {p.get('jar_amount', '')} / {p.get('fundraising_goal', '')}₴, <a href='{p.get('jar_url', '')}'>банка</a>\n"
        if len(text) > 5000:
            await message.answer(text, parse_mode='html')
            text = ""
    await message.answer(text, parse_mode='html')


@router.message((F.text == "/profile_view" ) | ( F.text == PROFILE_VIEW_BUTTON))
async def show_my_profile_view(message: Message):
    telegram_id = message.from_user.id    
    photo, text, type = await format_mentor_profile_view(telegram_id)
    kb = mentor_confirm_profile_view_kb()
    if type == 'animation':
        await message.answer_animation(animation=photo, caption=text, parse_mode="HTML")
    if type == 'video':
        await message.answer_video(video=photo, caption=text, parse_mode="HTML")
    if type == 'photo':
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
    valid = fundraising_goal_valid(text, 50000)
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
    valid = monobank_jar_valid(message.text)

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

    valid = instagram_valid(insta)

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
    await database.update_created_at(participant_id)
    await export_users_to_sheet()
    await callback.bot.send_message(chat_id=participant_id, text=YOU_HAVE_BEEN_APPROVED_PARTICIPANT)
    await callback.answer("Approved ✅")



@router.callback_query(F.data.startswith("approve_participant:") & F.data.endswith(":no"))
async def reject_participant(callback: CallbackQuery):
    user = await database.get_user_by_id(callback.from_user.id)
    if not (user['role'] == 'mentor' and user['status'] == 'approved'):
        return await callback.answer(NOT_ADMIN)

    participant_id = int(callback.data.split(":")[1])
    await database.update_status(participant_id, "declined")
    await callback.bot.send_message(chat_id=participant_id, text=YOU_HAVE_BEEN_APPROVED_PARTICIPANT)
    await callback.answer("Rejected ❌")


