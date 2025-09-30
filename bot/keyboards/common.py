from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from bot.texts import PHONE_SHARE_BUTTON, ROLE_MENTOR_BUTTON, ROLE_PARTICIPANT_BUTTON, CONFIRM_YES, CONFIRM_NO, CAROUSEL_LEFT, CAROUSEL_RIGHT, CAROUSEL_SELECT, APPROVE, REJECT

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