from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.texts import PHONE_SHARE_BUTTON, ROLE_MENTOR_BUTTON, ROLE_PARTICIPANT_BUTTON, CONFIRM_YES, CONFIRM_NO, CAROUSEL_LEFT, CAROUSEL_RIGHT, CAROUSEL_SELECT, APPROVE, REJECT, START_BUTTON, PROFILE_BUTTON, PROFILE_VIEW_BUTTON, TEAM_BUTTON, CHANGE_GOAL_BUTTON, CHANGE_INSTAGRAM_BUTTON, CHANGE_MONOBANK_BUTTON, CHANGE_DESCRIPTION_BUTTON, MENTOR_BUTTON, LIST_USERS_BUTTON, PENDING_MENTORS_BUTTON, LIST_MENTORS_BUTTON, REMOVE_USER_BUTTON, USER_PROFILE_BUTTON, SEND_DESIGN_BUTTON, LIST_QUESTIONS_BUTTON, ANSWER_BUTTON, RESTART_BUTTON, HELP_BUTTON
from bot.config import ADMINS, TECH_SUPPORT_ID

def phone_request_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=PHONE_SHARE_BUTTON, request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def role_choice_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=ROLE_MENTOR_BUTTON, callback_data="role:mentor")],
            [InlineKeyboardButton(text=ROLE_PARTICIPANT_BUTTON, callback_data="role:participant")]
        ]
    )

def mentor_confirm_profile_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text=CONFIRM_YES, callback_data="mentor_confirm_profile:yes"),
            InlineKeyboardButton(text=CONFIRM_NO, callback_data="mentor_confirm_profile:no")
        ]]
    )

def participant_confirm_profile_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text=CONFIRM_YES, callback_data="participant_confirm_profile:yes"),
            InlineKeyboardButton(text=CONFIRM_NO, callback_data="participant_confirm_profile:no")
        ]]
    )

def mentor_confirm_profile_view_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text=APPROVE, callback_data="mentor_confirm_profile:yes"),
            InlineKeyboardButton(text=REJECT, callback_data="mentor_confirm_profile:no")
        ]]
    )

def mentor_carousel_kb(index: int, total: int, mentor_id: int) -> InlineKeyboardMarkup:

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=CAROUSEL_LEFT, callback_data=f"mentor_nav:left:{index}"),
            InlineKeyboardButton(text=f"{index+1}/{total}", callback_data="noop"),
            InlineKeyboardButton(text=CAROUSEL_RIGHT, callback_data=f"mentor_nav:right:{index}")
        ],
        [   
            InlineKeyboardButton(text=f"{CAROUSEL_SELECT}", callback_data=f"mentor_select:{mentor_id}")
        ]
    ])
    return keyboard

def start_kb() -> InlineKeyboardMarkup:

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=START_BUTTON, callback_data=f"start_button")
        ]
    ])
    return keyboard


def confirm_data_processing_kb() -> InlineKeyboardMarkup:

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text=CONFIRM_YES, callback_data="confirm_data_processing:yes"),
            InlineKeyboardButton(text=CONFIRM_NO, callback_data="confirm_data_processing:no")
        ]]
    )
    return keyboard


def questions_kb(questions) -> InlineKeyboardMarkup:

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{q['id']}): {q['question_text'][:40]}",
                callback_data=f"answer_question:{q['id']}"
            )] for q in questions
        ]
    )
    return keyboard


def menu_kb(user) -> InlineKeyboardMarkup:
    buttons = [
            [KeyboardButton(text=PROFILE_BUTTON)],
        ]
    if user['role'] == 'mentor' and user['status'] == 'approved':
        buttons.append([KeyboardButton(text=TEAM_BUTTON)])
        buttons.append([KeyboardButton(text=PROFILE_VIEW_BUTTON)])
        buttons.append([KeyboardButton(text=CHANGE_GOAL_BUTTON), KeyboardButton(text=CHANGE_DESCRIPTION_BUTTON)])
        buttons.append([KeyboardButton(text=CHANGE_MONOBANK_BUTTON), KeyboardButton(text=CHANGE_INSTAGRAM_BUTTON)])

    if user['role'] == 'mentor' and user['status'] != 'approved':
        buttons.append([KeyboardButton(text=RESTART_BUTTON)])
        
    if user['role'] == 'participant':
        buttons.append([KeyboardButton(text=MENTOR_BUTTON)])
        buttons.append([KeyboardButton(text=RESTART_BUTTON)])
    if str(user['telegram_id']) in ADMINS:
        buttons.append([KeyboardButton(text=LIST_USERS_BUTTON), KeyboardButton(text=LIST_MENTORS_BUTTON)])
        buttons.append([KeyboardButton(text=PENDING_MENTORS_BUTTON), KeyboardButton(text=REMOVE_USER_BUTTON)])
        buttons.append([KeyboardButton(text=USER_PROFILE_BUTTON), KeyboardButton(text=SEND_DESIGN_BUTTON)])
       
    if str(user['telegram_id']) == TECH_SUPPORT_ID:
        buttons.append([KeyboardButton(text=LIST_QUESTIONS_BUTTON), KeyboardButton(text=ANSWER_BUTTON)])
    
    buttons.append([KeyboardButton(text=HELP_BUTTON)])
    print(len(buttons))

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=False,
        selective=True
    )