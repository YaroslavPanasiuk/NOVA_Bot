from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from bot.keyboards.common import phone_request_kb, role_choice_kb
from bot.db import database
from bot.handlers.mentor import MentorProfile, router as mentor_router
from bot.handlers.participant import ParticipantProfile, router as participant_router
from aiogram.fsm.context import FSMContext
from bot.handlers.participant import start_participant
from bot.handlers.mentor import start_mentor
from bot.utils.formatters import format_profile
from bot.texts import WELCOME, SELECT_ROLE, UNKNOWN_ROLE, USER_NOT_REGISTERED, START_PROMPT, RESTART_PROMPT, MENU_PROMPT, MENTOR_COMMANDS, PARTICIPANT_COMMANDS, ADMIN_COMMANDS
from bot.config import ADMINS

router = Router()

@router.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer(
        WELCOME,
        reply_markup=phone_request_kb()
    )

@router.message(F.contact)
async def phone_verification(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    # Add Telegram ID to DB without role yet
    await database.add_user(phone=phone, from_user=message.from_user)
    
    await message.answer(
        START_PROMPT
    )
    await message.bot.send_message(
        chat_id=message.from_user.id,
        text=SELECT_ROLE,
        reply_markup=role_choice_kb()
    )

@router.message(F.text == "/restart")
async def phone_verification(message: Message, state: FSMContext):
    await message.answer(
        RESTART_PROMPT
    )
    await message.bot.send_message(
        chat_id=message.from_user.id,
        text=SELECT_ROLE,
        reply_markup=role_choice_kb()
    )

# Role selection now starts the FSM dialogue
@router.callback_query(F.data.startswith("role:"))
async def role_choice(callback: CallbackQuery, state: FSMContext):
    role_str = callback.data.split(":")[1]

    if role_str == "mentor":
        # Start mentor FSM
        await state.set_state(MentorProfile.instagram)
        await database.set_role(telegram_id=callback.from_user.id, role="mentor")
        await start_mentor(callback, state)
    elif role_str == "participant":
        # Start participant FSM
        # We'll fetch mentors in the participant FSM handler  # import handler
        await database.set_role(telegram_id=callback.from_user.id, role="participant")
        await start_participant(callback, state)
    else:
        await callback.message.answer(UNKNOWN_ROLE)

    await callback.answer()


@router.message(F.text == "/profile")
async def show_my_profile(message: Message):
    telegram_id = message.from_user.id

    # Fetch user by telegram_id
    user = await database.get_user_by_id(telegram_id)
    if not user:
        await message.answer(USER_NOT_REGISTERED)
        return

    # Format profile
    text = await format_profile(telegram_id)

    if user.get("photo_url"):
        await message.answer_document(document=user["photo_url"], caption=text, parse_mode="HTML")
    else:
        await message.answer(text, parse_mode="HTML")


@router.message(F.text == "/menu")
async def show_my_profile(message: Message):
    text = MENU_PROMPT
    user = await database.get_user_by_id(message.from_user.id)
    print(user)
    print(user.get("role"))
    print(str(user.get("telegram_id")))
    if not user:
        await message.answer(USER_NOT_REGISTERED)
        return
    if user.get("role") == "mentor":
        text  += MENTOR_COMMANDS
    if user.get("role") == "participant":
        text  += PARTICIPANT_COMMANDS
    if str(user.get("telegram_id")) in ADMINS:
        text  += ADMIN_COMMANDS
    print(text)
    await message.answer(text)
