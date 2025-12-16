from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from bot.utils.texts import APPROVE, REJECT

def pending_mentors_kb(mentors: list):
    """Generate a list of pending mentors as buttons"""
    keyboard = []
    for mentor in mentors:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{mentor['first_name']} {mentor['last_name']} (@{mentor['username']})",
                callback_data=f"mentor:{mentor['telegram_id']}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def mentor_action_kb(mentor_id: int):
    """Approve / Reject keyboard for a specific mentor"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=APPROVE, callback_data=f"mentor_approve:{mentor_id}"),
            InlineKeyboardButton(text=REJECT, callback_data=f"mentor_reject:{mentor_id}")
        ]
    ])

def select_user_kb(users, callback, page=0, page_size=20):
    start = page * page_size
    end = start + page_size
    buttons = [
        [InlineKeyboardButton(
            text=f"{user['first_name']} {user.get('last_name', '')} (@{user.get('username', '')})".strip(),
            callback_data=f"{callback}:{user['telegram_id']}"
        )]
        for user in users[start:end]
    ]
    
    # Navigation buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Prev", callback_data=f"page:{callback}:{page-1}"))
    if end < len(users):
        nav_buttons.append(InlineKeyboardButton(text="➡️ Next", callback_data=f"page:{callback}:{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def select_user_for_design_kb(users, callback, page=0, page_size=20):
    start = page * page_size
    end = start + page_size
    buttons = []
    for user in users[start:end]:
        appendix = ""
        if user['design_uncompressed'] or user['design_compressed'] or user['design_video'] or user['design_animation']:
            appendix = "✅"
        buttons.append([InlineKeyboardButton(
            text=f"{user['first_name']} {user.get('last_name', '')} (@{user.get('username', '')}) {appendix}".strip(),
            callback_data=f"{callback}:{user['telegram_id']}"
        )])
   
    # Navigation buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Prev", callback_data=f"page:{callback}:{page-1}"))
    if end < len(users):
        nav_buttons.append(InlineKeyboardButton(text="➡️ Next", callback_data=f"page:{callback}:{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def send_messages_kb(callback_data_prefix="send_messages", additional_buttons=None):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Надіслати всім користувачам", callback_data=f"{callback_data_prefix}:all")],
            [InlineKeyboardButton(text="Надіслати лише учасникам", callback_data=f"{callback_data_prefix}:participants")],
            [InlineKeyboardButton(text="Надіслати лише амбасадорам", callback_data=f"{callback_data_prefix}:mentors")]
        ]
    )
    keyboard.inline_keyboard.extend(additional_buttons or [])
    return keyboard


def ask_addresses_kb(additional_buttons=None):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Надіслати учасникам, які зібрали 3000грн і більше", callback_data=f"ask_addresses:participants")],
            [InlineKeyboardButton(text="Надіслати лише амбасадорам, які зібрали 50000грн і більше", callback_data=f"ask_addresses:mentors")]
        ]
    )
    keyboard.inline_keyboard.extend(additional_buttons or [])
    return keyboard