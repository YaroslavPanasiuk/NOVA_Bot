from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asyncpg.exceptions import ForeignKeyViolationError
from bot.db import database
from bot.config import ADMINS
from aiogram.filters import Command
from bot.keyboards.admin import pending_mentors_kb, mentor_action_kb, select_user_kb
from bot.utils.formatters import format_profile, format_user_list, format_design_msg
from bot.utils.texts import NOT_ADMIN, NO_USERS_FOUND, REGISTERED_USERS_HEADER, NO_PENDING_MENTORS, MENTOR_APPROVED, MENTOR_REJECTED, NO_MENTORS_FOUND, REMOVE_USER_USAGE, USER_REMOVED, MENTOR_NOT_FOUND, USER_PROFILE_USAGE, REMOVE_USER_EXCEPTION, MENTOR_HAS_TEAM_EXCEPTION, SELECT_USER, SEND_AS_FILE_WARNING, NOT_IMAGE_FILE, USER_NOT_FOUND, DESIGN_SENT, DESIGN_INSTRUCTIONS, LIST_USERS_BUTTON, PENDING_MENTORS_BUTTON, LIST_MENTORS_BUTTON, REMOVE_USER_BUTTON, USER_PROFILE_BUTTON, SEND_DESIGN_BUTTON, YOU_HAVE_BEEN_APPROVED

router = Router()

class AdminProfile(StatesGroup):
    waiting_for_design = State()

@router.message((F.text == "/list_users" ) | ( F.text == LIST_USERS_BUTTON))
async def list_users_cmd(message: Message):
    # Check if user is admin
    if str(message.from_user.id) not in ADMINS:
        await message.answer(NOT_ADMIN)
        return

    # Fetch users from DB
    text = await format_user_list()

    if not text:
        await message.answer(NO_USERS_FOUND)
        return

    # Split long messages into chunks
    MAX_LEN = 4000
    for i in range(0, len(text), MAX_LEN):
        await message.answer(text[i:i+MAX_LEN])


@router.message((F.text == "/pending_mentors" ) | ( F.text == PENDING_MENTORS_BUTTON))
async def list_pending_mentors(message: Message):
    if str(message.from_user.id) not in ADMINS:
        return await message.answer(NOT_ADMIN)

    mentors = await database.get_pending_mentors()

    if not mentors:
        return await message.answer(NO_PENDING_MENTORS)

    await message.answer(
        "Pending mentors:",
        reply_markup=pending_mentors_kb(mentors)
    )


@router.message((F.text == "/list_mentors" ) | ( F.text == LIST_MENTORS_BUTTON))
async def list_pending_mentors(message: Message):
    # Check if user is admin
    if str(message.from_user.id) not in ADMINS:
        await message.answer(NOT_ADMIN)
        return

    # Fetch users from DB
    mentors = await database.get_mentors()

    if not mentors:
        await message.answer(NO_MENTORS_FOUND)
        return

    # Format output
    text_lines = ["👥 *Registered mentors:*"]
    for u in mentors:
        text_lines.append(
            f"ID: {u['telegram_id']} | Name: {u['first_name']} {u['last_name']} | Username: @{u['username']} | Phone: {u['phone_number']} | Status: {u['status']} | Registaerd at: {u['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
        )

    text = "\n".join(text_lines)

    # Split long messages into chunks
    MAX_LEN = 4000
    for i in range(0, len(text), MAX_LEN):
        await message.answer(text[i:i+MAX_LEN])


@router.callback_query(F.data.startswith("mentor:"))
async def show_mentor(callback: CallbackQuery):
    if str(callback.from_user.id) not in ADMINS:
        return await callback.answer(NOT_ADMIN)

    mentor_id = int(callback.data.split(":")[1])
    mentor = await database.get_user_by_id(mentor_id)

    if not mentor:
        return await callback.answer(MENTOR_NOT_FOUND, show_alert=True)

    text = await format_profile(mentor_id)

    await callback.message.answer(
        text,
        reply_markup=mentor_action_kb(mentor_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("mentor_approve:"))
async def approve_mentor(callback: CallbackQuery):
    if str(callback.from_user.id) not in ADMINS:
        return await callback.answer(NOT_ADMIN)

    mentor_id = int(callback.data.split(":")[1])
    await database.update_mentor_status(mentor_id, "approved")
    await callback.message.edit_text(MENTOR_APPROVED)
    await callback.bot.send_message(chat_id=mentor_id, text=YOU_HAVE_BEEN_APPROVED)
    await callback.answer("Approved ✅")



@router.callback_query(F.data.startswith("mentor_reject:"))
async def reject_mentor(callback: CallbackQuery):
    if str(callback.from_user.id) not in ADMINS:
        return await callback.answer(NOT_ADMIN)

    mentor_id = int(callback.data.split(":")[1])
    await database.delete_user(mentor_id)
    await callback.message.edit_text(MENTOR_REJECTED)
    await callback.answer("Rejected ❌")


@router.message((F.text.startswith("/remove_user") ) | ( F.text == REMOVE_USER_BUTTON))
async def remove_user_cmd(message: Message):
    if str(message.from_user.id) not in ADMINS:
        await message.answer(NOT_ADMIN)
        return
    
    users = await database.get_all_users()
    kb = select_user_kb(users, "delete_user")
    await message.answer(SELECT_USER, reply_markup=kb)


@router.callback_query(F.data.startswith("delete_user:"))
async def remove_user_reply_cmd(callback: CallbackQuery):
    if str(callback.from_user.id) not in ADMINS:
        await callback.answer(NOT_ADMIN)
        return

    parts = callback.data.split(":")
    if len(parts) != 2 or not parts[1].isdigit():
        await callback.answer(REMOVE_USER_USAGE)
        return

    user_id = int(parts[1]) 
    try:
        await database.delete_user(user_id)
        await callback.answer(USER_REMOVED)
    except ForeignKeyViolationError:
        await callback.answer(MENTOR_HAS_TEAM_EXCEPTION, show_alert=True)
    except Exception:
        await callback.answer(REMOVE_USER_EXCEPTION, show_alert=True)


@router.message((F.text.startswith("/user_profile") ) | ( F.text == USER_PROFILE_BUTTON))
async def user_profile_cmd(message: Message):
    if str(message.from_user.id) not in ADMINS:
        await message.answer(NOT_ADMIN)
        return
    
    users = await database.get_all_users()
    kb = select_user_kb(users, "user_profile")
    await message.answer(SELECT_USER, reply_markup=kb)


@router.callback_query(F.data.startswith("user_profile:"))
async def user_profile_reply_cmd(callback: CallbackQuery):
    if str(callback.from_user.id) not in ADMINS:
        await callback.answer(NOT_ADMIN)
        return

    parts = callback.data.split(":")
    if len(parts) != 2 or not parts[1].isdigit():
        await callback.answer(USER_PROFILE_USAGE)
        return

    user_id = int(parts[1]) 
    user = await database.get_user_by_id(user_id)
    text = await format_profile(user_id)

    if user.get("photo_url"):
        document = user["photo_url"]
    else:
        document = FSInputFile("resources/default.png", filename="no-profile-picture.png")
    await callback.message.answer_document(document=document, caption=text, parse_mode="HTML")
    await callback.answer()


@router.message((F.text == "/send_design" ) | ( F.text == SEND_DESIGN_BUTTON))
async def answer_cmd(message: Message):
    if str(message.from_user.id) not in ADMINS:
        await message.answer(NOT_ADMIN)
        return
    
    users = await database.get_all_users()
    kb = select_user_kb(users, "design")
    await message.answer(SELECT_USER, reply_markup=kb)


@router.callback_query(F.data.startswith("page:"))
async def paginate_users(callback: CallbackQuery):
    callback_data = callback.data.split(":")[1]
    page = int(callback.data.split(":")[2])
    users = await database.get_all_users()
    kb = select_user_kb(users, callback=callback_data, page=page)
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("design:"))
async def send_design_cmd(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split(":")[1])
    user = await database.get_user_by_id(user_id)
    await state.update_data(selected_user_id=user_id)
    await state.set_state(AdminProfile.waiting_for_design)
    await callback.message.edit_text(callback.message.text + f"\n\n Ти обрав: {user['first_name']} {user['last_name']}")
    await callback.message.answer(f"✍️ Надішли дизайн поста у форматі файлу для @{user['username']} (відмінити - /cancel)")
    await callback.answer()


@router.message(AdminProfile.waiting_for_design, F.photo)
async def photo_compressed(message: Message, state: FSMContext):
    await message.answer(SEND_AS_FILE_WARNING)


@router.message(AdminProfile.waiting_for_design, F.document)
async def send_design(message: Message, state: FSMContext):
    if not message.document.mime_type.startswith("image/"):
        await message.answer(NOT_IMAGE_FILE)
        return
    
    file_id = message.document.file_id
    data = await state.get_data()
    user_id = data.get("selected_user_id")
    print(user_id)
    user = await database.get_user_by_id(user_id)
    
    if not user:
        await message.answer(USER_NOT_FOUND)
        return

    try:
        caption = await format_design_msg(user)
        await message.bot.send_message(chat_id=user_id, text=DESIGN_SENT)
        await message.bot.send_document(chat_id=user_id, document=file_id, caption=caption)
        await message.bot.send_message(chat_id=user_id, text=DESIGN_INSTRUCTIONS)
        await message.answer("✅ Дизайн надіслано.")
    except Exception as e:
        await message.answer(f"⚠️ Не вдалося надіслати дизайн: {e}")

    await state.clear()