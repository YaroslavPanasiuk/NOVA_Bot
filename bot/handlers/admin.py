from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asyncpg.exceptions import ForeignKeyViolationError
from bot.db import database
from bot.config import ADMINS, DB_CHAT_ID
from aiogram.filters import Command
from bot.keyboards.admin import pending_mentors_kb, mentor_action_kb, select_user_kb
from bot.keyboards.common import role_choice_kb
from bot.utils.formatters import format_profile, format_user_list, format_design_msg, format_profile_image
from bot.utils.texts import NOT_ADMIN, NO_USERS_FOUND, REGISTERED_USERS_HEADER, NO_PENDING_MENTORS, MENTOR_APPROVED, MENTOR_REJECTED, NO_MENTORS_FOUND, REMOVE_USER_USAGE, USER_REMOVED, MENTOR_NOT_FOUND, USER_PROFILE_USAGE, REMOVE_USER_EXCEPTION, MENTOR_HAS_TEAM_EXCEPTION, SELECT_USER, SEND_AS_FILE_WARNING, NOT_IMAGE_FILE, USER_NOT_FOUND, DESIGN_SENT, DESIGN_INSTRUCTIONS, LIST_USERS_BUTTON, PENDING_MENTORS_BUTTON, LIST_MENTORS_BUTTON, REMOVE_USER_BUTTON, USER_PROFILE_BUTTON, SEND_DESIGN_BUTTON, YOU_HAVE_BEEN_APPROVED_MENTOR, YOU_HAVE_BEEN_REJECTED_MENTOR, DESIGN_CAPTION, USER_NOT_REGISTERED, SELECT_ROLE
from bot.utils.files import reupload_as_photo

router = Router()

class AdminProfile(StatesGroup):
    waiting_for_design = State()
    waiting_for_design_caption = State()
    add_compressed_photo = State()
    add_uncompressed_photo = State()
    add_video = State()
    add_animation = State()

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
    document = await format_profile_image(mentor_id)

    await callback.message.answer_document(
        document=document,
        caption=text,
        reply_markup=mentor_action_kb(mentor_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("mentor_approve:"))
async def approve_mentor(callback: CallbackQuery):
    if str(callback.from_user.id) not in ADMINS:
        return await callback.answer(NOT_ADMIN)

    mentor_id = int(callback.data.split(":")[1])
    await database.update_status(mentor_id, "approved")
    await callback.message.edit_caption(MENTOR_APPROVED)
    await callback.bot.send_message(chat_id=mentor_id, text=YOU_HAVE_BEEN_APPROVED_MENTOR)
    await callback.answer("Approved ✅")



@router.callback_query(F.data.startswith("mentor_reject:"))
async def reject_mentor(callback: CallbackQuery):
    if str(callback.from_user.id) not in ADMINS:
        return await callback.answer(NOT_ADMIN)

    mentor_id = int(callback.data.split(":")[1])
    await database.set_status(mentor_id, 'rejected')
    await callback.message.edit_text(MENTOR_REJECTED)
    await callback.bot.send_message(chat_id=mentor_id, text=YOU_HAVE_BEEN_REJECTED_MENTOR)
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
        users = await database.get_all_users()
        kb = select_user_kb(users, "delete_user")
        print(kb)
        await callback.message.edit_reply_markup(reply_markup=kb)
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
    text = await format_profile(user_id)
    photo = await format_profile_image(user_id)
    await callback.message.answer_document(document=photo, caption=text, parse_mode="HTML")
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
async def design_caption(message: Message, state: FSMContext):
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
    compressed_id = await reupload_as_photo(message.bot, file_id)
    await database.set_photo(user_id, file_id, 'design_uncompressed')
    await database.set_photo(user_id, compressed_id, 'design_compressed')
    await state.update_data(design_id=file_id)

    caption = await format_design_msg(user)
    await message.answer(DESIGN_CAPTION.format(user=user['username'], goal=user['fundraising_goal'], caption=caption))

    await state.set_state(AdminProfile.waiting_for_design_caption)


@router.message(AdminProfile.waiting_for_design_caption, F.text)
async def send_design(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("selected_user_id")
    file_id = data.get("design_id")
    user = await database.get_user_by_id(user_id)
    
    if not user:
        await message.answer(USER_NOT_FOUND)
        return
    try:
        caption = message.text
        await message.bot.send_message(chat_id=user_id, text=DESIGN_SENT)
        await message.bot.send_document(chat_id=user_id, document=file_id, caption=caption)
        await message.bot.send_message(chat_id=user_id, text=DESIGN_INSTRUCTIONS)
        await message.answer("✅ Дизайн надіслано.")
    except Exception as e:
        await message.answer(f"⚠️ Не вдалося надіслати дизайн: {e}")

    await state.clear()



@router.message((F.text == "/add_compressed_photo" ))
async def add_compressed_photo(message: Message, state:FSMContext):
    if str(message.from_user.id) not in ADMINS:
        await message.answer(NOT_ADMIN)
        return
    await state.set_state(AdminProfile.add_compressed_photo)
    await message.answer('send compressed photo with caption as its name')

@router.message(AdminProfile.add_compressed_photo)
async def set_compressed_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    name = message.caption
    await database.add_file(photo_id, 'photo_compressed', name)
    await message.bot.send_photo(chat_id=DB_CHAT_ID, photo=photo_id)
    await state.clear()



@router.message((F.text == "/add_uncompressed_photo" ))
async def add_compressed_photo(message: Message, state: FSMContext):
    if str(message.from_user.id) not in ADMINS:
        await message.answer(NOT_ADMIN)
        return
    await state.set_state(AdminProfile.add_uncompressed_photo)
    await message.answer('send uncompressed photo with caption as its name')
    
@router.message(AdminProfile.add_uncompressed_photo)
async def set_uncompressed_photo(message: Message, state: FSMContext):
    photo_id = message.document.file_id
    name = message.caption
    await database.add_file(photo_id, 'photo_uncompressed', name)
    await message.bot.send_document(chat_id=DB_CHAT_ID, document=photo_id)
    await state.clear()


@router.message((F.text == "/add_video" ))
async def add_compressed_photo(message: Message, state:FSMContext):
    if str(message.from_user.id) not in ADMINS:
        await message.answer(NOT_ADMIN)
        return
    await state.set_state(AdminProfile.add_video)
    await message.answer('send video with caption as its name')
    

@router.message(AdminProfile.add_video)
async def set_video(message: Message, state: FSMContext):
    video_id = message.video.file_id
    name = message.caption
    await database.add_file(video_id, 'video', name)
    await message.bot.send_video(chat_id=DB_CHAT_ID, video=video_id)
    await state.clear()


@router.message((F.text == "/add_animation" ))
async def add_compressed_photo(message: Message, state:FSMContext):
    if str(message.from_user.id) not in ADMINS:
        await message.answer(NOT_ADMIN)
        return
    await state.set_state(AdminProfile.add_animation)
    await message.answer('send animation with caption as its name')
    

@router.message(AdminProfile.add_animation)
async def set_video(message: Message, state: FSMContext):
    animation_id = message.animation.file_id
    name = message.caption
    await database.add_file(animation_id, 'animation', name)
    await message.bot.send_animation(chat_id=DB_CHAT_ID, animation=animation_id)
    await state.clear()


@router.message(F.text.startswith("/force_remove_user"))
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
        await database.force_delete_user(user_id)
        await message.answer(USER_REMOVED)
    except ForeignKeyViolationError:
        await message.answer(MENTOR_HAS_TEAM_EXCEPTION, show_alert=True)
    except Exception:
        await message.answer(REMOVE_USER_EXCEPTION, show_alert=True)


@router.message(F.text == "/force_restart" )
async def phone_verification(message: Message, state: FSMContext):
    if str(message.from_user.id) not in ADMINS:
        await message.answer(NOT_ADMIN)
        return
    user = await database.get_user_by_id(message.from_user.id)
    if not user:
        await message.answer(USER_NOT_REGISTERED)
        return
    await database.set_role(message.from_user.id, "pending")
    await database.set_mentor(message.from_user.id, None)
    await message.bot.send_message(
        chat_id=message.from_user.id,
        text=SELECT_ROLE,
        reply_markup=role_choice_kb()
    )