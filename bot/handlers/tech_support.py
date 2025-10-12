from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.db import database
from bot.config import TECH_SUPPORT_ID
from bot.utils.formatters import format_question_list, send_long_message
from bot.keyboards.common import questions_kb
from bot.utils.texts import NOT_ADMIN, SELECT_QUESTION, QUESTIONS_NOT_FOUND, USER_NOT_FOUND, LIST_QUESTIONS_BUTTON, ANSWER_BUTTON

router = Router()

class TechSupportStates(StatesGroup):
    waiting_for_answer = State()

@router.message((F.text == "/list_questions" ) | ( F.text == LIST_QUESTIONS_BUTTON))
async def list_questions_cmd(message: Message):
    if str(message.from_user.id) != TECH_SUPPORT_ID:
        await message.answer(NOT_ADMIN)
        return

    text = await format_question_list()
    if not text:
        await message.answer(QUESTIONS_NOT_FOUND)
    await send_long_message(message.bot, message.from_user.id, text)


@router.message((F.text == "/answer" | F.text == ANSWER_BUTTON))
async def answer_cmd(message: Message):
    if str(message.from_user.id) != TECH_SUPPORT_ID:
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
            f"💬 <b>Привіт, ти запитував:</b> `{question["question_text"]}`\n\n"
            f"🧠 <b>Ось відповідь від тех підтримки:</b> {message.text}",
            parse_mode="HTML"
        )
        await database.set_question_status(question_id, "answered")
        await message.answer("✅ Відповідь надіслана.")
    except Exception as e:
        await message.answer(f"⚠️ Не вдалося надіслати відповідь: {e}")

    await state.clear()
