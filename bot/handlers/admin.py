from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from asyncpg.exceptions import ForeignKeyViolationError
from bot.db import database
from bot.config import ADMINS
from aiogram.filters import Command
from bot.keyboards.admin import pending_mentors_kb, mentor_action_kb
from bot.utils.formatters import format_profile, format_user_list
from bot.texts import NOT_ADMIN, NO_USERS_FOUND, REGISTERED_USERS_HEADER, NO_PENDING_MENTORS, MENTOR_APPROVED, MENTOR_REJECTED, NO_MENTORS_FOUND, REMOVE_USER_USAGE, USER_REMOVED, MENTOR_NOT_FOUND, USER_PROFILE_USAGE, REMOVE_USER_EXCEPTION, MENTOR_HAS_TEAM_EXCEPTION

router = Router()

@router.message(F.text == "/list_users")
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


@router.message(Command("pending_mentors"))
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


@router.message(Command("list_mentors"))
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
    await callback.answer("Approved ✅")


@router.callback_query(F.data.startswith("mentor_reject:"))
async def reject_mentor(callback: CallbackQuery):
    if str(callback.from_user.id) not in ADMINS:
        return await callback.answer(NOT_ADMIN)

    mentor_id = int(callback.data.split(":")[1])
    await database.delete_user(mentor_id)
    await callback.message.edit_text(MENTOR_REJECTED)
    await callback.answer("Rejected ❌")


@router.message(F.text.startswith("/remove_user"))
async def remove_user_cmd(message: Message):
    if str(message.from_user.id) not in ADMINS:
        await message.answer(NOT_ADMIN)
        return

    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer(REMOVE_USER_USAGE)
        return

    user_id = int(parts[1]) 
    try:
        await database.delete_user(user_id)
        await message.answer(USER_REMOVED)
    except ForeignKeyViolationError:
        await message.answer(MENTOR_HAS_TEAM_EXCEPTION, show_alert=True)
    except Exception:
        await message.answer(REMOVE_USER_EXCEPTION, show_alert=True)


@router.message(F.text.startswith("/user_profile"))
async def user_profile_cmd(message: Message):
    if str(message.from_user.id) not in ADMINS:
        await message.answer(NOT_ADMIN)
        return

    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer(USER_PROFILE_USAGE)
        return

    user_id = int(parts[1]) 
    user = await database.get_user_by_id(user_id)
    text = await format_profile(user_id)

    if user.get("photo_url"):
        document = user["photo_url"]
    else:
        document = FSInputFile("resources/default.png", filename="no-profile-picture.png")
    await message.answer_document(document=document, caption=text, parse_mode="HTML")
