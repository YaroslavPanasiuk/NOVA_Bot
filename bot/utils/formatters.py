from bot.db import database
from bot.texts import SEPARATOR, PROFILE_NAME, PROFILE_PHONE, PROFILE_INSTAGRAM, PROFILE_GOAL, PROFILE_STATUS, PROFILE_MENTOR, PARTICIPANT_PROFILE_HEADER, MENTOR_PROFILE_HEADER, PROFILE_DESCRIPTION

async def format_profile(user_id: int) -> str:
    user = await database.get_user_by_id(user_id)
    if not user:
        return "❌ User not found."
    header = PARTICIPANT_PROFILE_HEADER if user.get('role') == "participant" else MENTOR_PROFILE_HEADER
    base_info = (
        f"{SEPARATOR}"        
        f"{f"{header}":<100}\n"
        f"{SEPARATOR}"
        f"{PROFILE_NAME}{user.get('first_name') or ''} {user.get('last_name') or ''} @{user.get('username') or ''}\n"
        f"{PROFILE_PHONE}{user.get('phone_number') or '—'}\n"
        f"{PROFILE_INSTAGRAM}{user.get('instagram') or '—'}\n"
        f"{PROFILE_GOAL}{format_amount(user.get('fundraising_goal', 0.0))}\n"
    )

    if user.get('role') == "mentor":
        base_info += f"{PROFILE_DESCRIPTION}{user['description']}\n"
        base_info += f"{PROFILE_STATUS}{user['status']}\n"

    if user.get('role') == "participant":
        mentor = await database.get_user_by_id(user.get('mentor_id'))
        base_info += f"{PROFILE_MENTOR}{mentor.get('first_name', '')} {mentor.get('last_name', '')} @{mentor.get('username', '')}\n"

    return base_info


def format_amount(value: float) -> str:
    try:
        if value == int(value):
            return f"{int(value):,} грн".replace(",", " ")
        return f"{value:,.2f} грн".replace(",", " ")
    except (ValueError, TypeError):
        return value