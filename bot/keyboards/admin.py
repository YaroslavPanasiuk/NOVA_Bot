from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.texts import APPROVE, REJECT

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
