from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.db import database
from aiogram.fsm.storage.base import StorageKey
from bot.config import TECH_SUPPORT_ID, ADMINS
from bot.handlers.start import GeneralStates
from bot.utils.formatters import format_question_list, send_long_message, format_profile, format_profile_image
from bot.keyboards.common import questions_kb, text_kb
from bot.keyboards.admin import select_user_kb
from bot.utils.texts import *

router = Router()

class TechSupportStates(StatesGroup):
    waiting_for_answer = State()
    waiting_for_message = State()
    waiting_for_question = State()

@router.message((F.text == "/list_questions" ) | ( F.text == LIST_QUESTIONS_BUTTON))
async def list_questions_cmd(message: Message):
    if str(message.from_user.id) != TECH_SUPPORT_ID:
        await message.answer(NOT_ADMIN)
        return

    text = await format_question_list()
    if not text:
        await message.answer(QUESTIONS_NOT_FOUND)
    await send_long_message(message.bot, message.from_user.id, text)


@router.message((F.text == "/answer") | (F.text == ANSWER_BUTTON))
async def answer_cmd(message: Message):
    if str(message.from_user.id) != TECH_SUPPORT_ID and str(message.from_user.id) not in ADMINS:
        await message.answer(NOT_ADMIN)
        return
    
    questions = await database.get_questions()
    not_answered = []
    for question in questions:
        if question['status'] == "not answered":
            not_answered.append(question)

    if len(questions) == 0:
        await message.answer(QUESTIONS_NOT_FOUND)
        return
    kb = questions_kb(not_answered)
    await message.answer(SELECT_QUESTION, reply_markup=kb)


@router.callback_query(F.data.startswith("answer_question:"))
async def start_answer_question(callback: CallbackQuery, state: FSMContext):
    question_id = int(callback.data.split(":")[1])
    question = await database.get_question_by_id(question_id)
    user = await database.get_user_by_id(question['telegram_id'])
    await state.update_data(selected_question_id=question_id)
    await state.set_state(TechSupportStates.waiting_for_answer)
    await callback.message.answer(f"✍️ Напиши відповідь на запитання від @{user['username']}: '''{question['question_text']}''' (відмінити - /cancel)")
    await callback.answer()


@router.message(TechSupportStates.waiting_for_answer)
async def send_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    question_id = data.get("selected_question_id")
    if not question_id:
        await message.answer("⚠️ Обери запитання.")
        await state.clear()
        return

    question = await database.get_question_by_id(question_id)
    user = await database.get_user_by_id(question['telegram_id'])
    
    if not user:
        await message.answer(USER_NOT_FOUND)
        return

    try:
        await message.bot.send_message(
            user["telegram_id"],
            f"💬 <b>Привіт, ти запитував:</b> `{question['question_text']}`\n\n"
            f"🧠 <b>Ось відповідь від тех підтримки:</b> {message.text}",
            parse_mode="HTML"
        )
        await database.set_question_status(question_id, "answered")
        await message.answer("✅ Відповідь надіслана.")
    except Exception as e:
        await message.answer(f"⚠️ Не вдалося надіслати відповідь: {e}")

    await state.clear()


@router.message((F.text == "/send_message") | (F.text == SEND_MESSAGE_BUTTON))
async def send_message_cmd(message: Message):
    if str(message.from_user.id) != TECH_SUPPORT_ID and str(message.from_user.id) not in ADMINS:
        await message.answer(NOT_ADMIN)
        return
    
    users = await database.get_all_users_sorted(key='created_at DESC')
    if not users:
        await message.answer(USER_NOT_FOUND)
        return
    kb = select_user_kb(users, 'send_message', page_size=20)
    await message.answer(SELECT_USER, reply_markup=kb)@router.message((F.text == "/send_message") | (F.text == SEND_MESSAGE_BUTTON))


@router.message((F.text == "/send_question") | (F.text == SEND_QUESTION_BUTTON))
async def send_message_cmd(message: Message):
    if str(message.from_user.id) != TECH_SUPPORT_ID and str(message.from_user.id) not in ADMINS:
        await message.answer(NOT_ADMIN)
        return
    
    users = await database.get_all_users_sorted(key='created_at DESC')
    if not users:
        await message.answer(USER_NOT_FOUND)
        return
    kb = select_user_kb(users, 'send_question', page_size=20)
    await message.answer(SELECT_USER, reply_markup=kb)


@router.callback_query((F.data.startswith("page:send_message")) | (F.data.startswith("page:send_question")))
async def paginate_users(callback: CallbackQuery):
    callback_data = callback.data.split(":")[1]
    page = int(callback.data.split(":")[2])
    users = await database.get_all_users_sorted(key='created_at DESC')
    kb = select_user_kb(users, callback=callback_data, page=page, page_size=20)
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("send_message:"))
async def message_text(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split(":")[1])
    user = await database.get_user_by_id(user_id)
    await state.update_data(selected_user_id=user_id)
    await state.set_state(TechSupportStates.waiting_for_message)
    await callback.message.answer(f"✍️ Напиши текст повідомлення для @{user['username']}")
    await callback.answer()


@router.callback_query(F.data.startswith("send_question:"))
async def message_text(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split(":")[1])
    user = await database.get_user_by_id(user_id)
    await state.update_data(selected_user_id=user_id)
    await state.set_state(TechSupportStates.waiting_for_question)
    await callback.message.answer(f"✍️ Напиши текст запитання для @{user['username']}")
    await callback.answer()


@router.message(TechSupportStates.waiting_for_message, F.text)
async def send_message(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("selected_user_id")
    if not user_id:
        await message.answer("⚠️ Обери запитання.")
        await state.clear()
        return

    user = await database.get_user_by_id(user_id)
    
    if not user:
        await message.answer(USER_NOT_FOUND)
        return

    try:
        await message.bot.send_message(
            user_id,
            message.text,
            parse_mode="HTML"
        )
        await message.answer("✅ Повідомлення надіслано.")
    except Exception as e:
        await message.answer(f"⚠️ Не вдалося надіслати повідомлення: {e}")
    
    await state.clear()


@router.message(TechSupportStates.waiting_for_question, F.text)
async def send_message(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("selected_user_id")
    if not user_id:
        await state.clear()
        return

    user = await database.get_user_by_id(user_id)
    
    if not user:
        await message.answer(USER_NOT_FOUND)
        return

    try:
        await message.bot.send_message(
            user_id,
            message.text,
            parse_mode="HTML"
        )
        await message.answer("✅ Повідомлення надіслано.")
    except Exception as e:
        await message.answer(f"⚠️ Не вдалося надіслати повідомлення: {e}")
    
    await state.clear()

    user_key = StorageKey(
        bot_id=message.bot.id,
        user_id=user_id,
        chat_id=user_id,
    )
    user_state = FSMContext(storage=state.storage, key=user_key)
    await user_state.update_data(sender_id=message.from_user.id)
    await user_state.update_data(sender_message=message.text)

    await user_state.set_state(GeneralStates.waiting_for_response)


@router.message((F.text == ("/unfinished_registrations")) | (F.text == UNFINISHED_REGISTRATIONS_BUTTON))
async def list_unfinished_registrations(message: Message):
    if str(message.from_user.id) not in ADMINS and str(message.from_user.id) != TECH_SUPPORT_ID:
        await message.answer(NOT_ADMIN)
        return
    users = await database.get_unfinished_registrations()
    
    if not users:
        await message.answer(USER_NOT_FOUND)
        return
    
    kb = select_user_kb(users, "remind_to_register")
    await message.answer(
        "Учасники, які не завершили реєстрацію:",
        reply_markup=kb
    )


@router.callback_query(F.data.startswith("remind_to_register:"))
async def message_text(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split(":")[1])
    await state.update_data(selected_user_id=user_id)
    kb = text_kb("Написати повідомлення", f'send_message:{user_id}')
    
    text = await format_profile(user_id)
    document = await format_profile_image(user_id)

    await callback.message.answer_document(
        document=document,
        caption=text,
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()