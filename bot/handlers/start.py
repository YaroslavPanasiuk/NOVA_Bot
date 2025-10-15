from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from bot.keyboards.common import start_kb, role_choice_kb, phone_request_kb, menu_kb
from bot.db import database
from aiogram.fsm.context import FSMContext
from bot.handlers.participant import start_participant
from bot.handlers.mentor import start_mentor
from bot.utils.formatters import format_profile, format_profile_image
from bot.utils.texts import WELCOME, SELECT_ROLE, UNKNOWN_ROLE, USER_NOT_REGISTERED, RESTART_PROMPT, MENU_PROMPT, MENTOR_COMMANDS, PARTICIPANT_COMMANDS, ADMIN_COMMANDS, ALREADY_REGISTERED_MENTOR, SHARE_PHONE, HELP_PROMPT, HELP_REQUESTED_PROMPT, TECH_SUPPORT_COMMANDS, SUGGEST_ANSWER_COMMAND, CANCELED, RESTART_BUTTON, PROFILE_BUTTON, HELP_BUTTON, CANCEL_REGISTRATION_BUTTON
from bot.config import TECH_SUPPORT_ID

router = Router()

class GeneralStates(StatesGroup):
    help = State()

@router.message(Command("start"))
async def start_cmd(message: Message):
    user = await database.get_user_by_id(message.from_user.id)
    if user and user.get("role") == "mentor" and user.get("status") == "approved":
        return await message.answer(ALREADY_REGISTERED_MENTOR, show_alert=True)
    animation = await database.get_file_by_name('start_animation')
    await message.answer_animation(
        animation=animation['file_id'],
        caption=WELCOME,
        reply_markup=start_kb(), 
        parse_mode="HTML"
    )

@router.message((F.text == "/cancel") | (F.text == CANCEL_REGISTRATION_BUTTON))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(CANCELED)

@router.callback_query(F.data == "start_button")
async def share_contact(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    await callback.message.answer(
        SHARE_PHONE,
        reply_markup=phone_request_kb()
    )

@router.message(F.contact)
async def phone_verification(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    temp_msg = await message.answer("...", reply_markup=ReplyKeyboardRemove())
    await temp_msg.delete()
    # Add Telegram ID to DB without role yet
    await database.add_user(phone=phone, from_user=message.from_user)
    
    await message.bot.send_message(
        chat_id=message.from_user.id,
        text=SELECT_ROLE,
        reply_markup=role_choice_kb()
    )

@router.message((F.text == "/restart" ) | ( F.text == RESTART_BUTTON))
async def phone_verification(message: Message, state: FSMContext):
    user = await database.get_user_by_id(message.from_user.id)
    if not user:
        await message.answer(USER_NOT_REGISTERED)
        return
    if user.get("role") == "mentor" and user.get("status") == "approved":
        return await message.answer(ALREADY_REGISTERED_MENTOR, show_alert=True)
    await message.answer(
        RESTART_PROMPT
    )
    #await database.set_role(message.from_user.id, "pending")
    await database.set_mentor(message.from_user.id, None)
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
        await callback.message.edit_reply_markup()
        await database.set_role(telegram_id=callback.from_user.id, role="mentor")
        await start_mentor(callback, state)
    elif role_str == "participant":
        await callback.message.edit_reply_markup()
        await database.set_role(telegram_id=callback.from_user.id, role="participant")
        await start_participant(callback, state)
    else:
        await callback.message.answer(UNKNOWN_ROLE)

    await callback.answer()


@router.message((F.text == PROFILE_BUTTON)|(F.text == '/profile'))
async def show_my_profile(message: Message):
    telegram_id = message.from_user.id

    # Fetch user by telegram_id
    user = await database.get_user_by_id(telegram_id)
    if not user:
        await message.answer(USER_NOT_REGISTERED)
        return

    # Format profile
    text = await format_profile(telegram_id)
    photo = await format_profile_image(telegram_id)

    if photo:
        await message.answer_document(document=photo, caption=text, parse_mode="HTML")
    else:
        await message.answer(text, parse_mode="HTML")


@router.message(F.text == "/menu")
async def show_menu(message: Message):
    user = await database.get_user_by_id(message.from_user.id)
    if not user:
        await message.answer(USER_NOT_REGISTERED)
        return
    text = MENU_PROMPT
    user = await database.get_user_by_id(message.from_user.id)
    kb = menu_kb(user)
    await message.answer(text, reply_markup=kb)


@router.message((F.text == "/help" ) | ( F.text == HELP_BUTTON))
async def show_help(message: Message, state: FSMContext):
    user = await database.get_user_by_id(message.from_user.id)
    if not user:
        await message.answer(USER_NOT_REGISTERED)
        return
    await message.answer(HELP_PROMPT)
    await state.set_state(GeneralStates.help)

@router.message(GeneralStates.help)
async def send_help_message(message: Message, state: FSMContext):
    await state.clear()
    user = await database.get_user_by_id(message.from_user.id)
    if not user:
        await message.answer(USER_NOT_REGISTERED)
        return
    await database.add_question(user['telegram_id'], message.text)
    await message.bot.send_message(TECH_SUPPORT_ID, text=f"{user['first_name']} {user['last_name']} (@{user['username']}) Має питання:")
    await message.forward(chat_id=TECH_SUPPORT_ID)
    await message.bot.send_message(TECH_SUPPORT_ID, text=SUGGEST_ANSWER_COMMAND)
    await message.answer(HELP_REQUESTED_PROMPT)


@router.message((F.text == "/chat_id" ))
async def show_help(message: Message, state: FSMContext):
    await message.answer(str(message.chat.id))

