from bot.db import database
from aiogram.exceptions import AiogramError
from bot.texts import SEPARATOR, PROFILE_NAME, PROFILE_PHONE, PROFILE_INSTAGRAM, PROFILE_GOAL, PROFILE_STATUS, PROFILE_MENTOR, PARTICIPANT_PROFILE_HEADER, MENTOR_PROFILE_HEADER, PROFILE_DESCRIPTION, PROFILE_JAR, REGISTERED_USERS_HEADER

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
        f"{PROFILE_JAR}{user.get('jar_url', '—')}\n"
    )

    if user.get('role') == "mentor":
        base_info += f"{PROFILE_DESCRIPTION}{user['description']}\n"
        base_info += f"{PROFILE_STATUS}{user['status']}\n"

    if user.get('role') == "participant":
        mentor = await database.get_user_by_id(user.get('mentor_id'))
        if mentor:
            base_info += f"{PROFILE_MENTOR}{mentor.get('first_name', '')} {mentor.get('last_name', '')} @{mentor.get('username', '')}\n"

    return base_info


def format_amount(value: float) -> str:
    try:
        if value == int(value):
            return f"{int(value):,} грн".replace(",", " ")
        return f"{value:,.2f} грн".replace(",", " ")
    except (ValueError, TypeError):
        return value


async def format_user_list() -> str:
    users = await database.get_all_users()

    if not users:
        return None

    # Format output
    text_lines = [REGISTERED_USERS_HEADER]
    for u in users:
        if u['role'] == "mentor":
            role_str = f" | Status: {u['status']}"
        elif u['role'] == "participant":
            role_str = f" | Mentor: {u['mentor_id']}"
        else:
            role_str = ""
        if role_str == None:
            role_str = ""
        try:
            username_str = f"@{u['username']}"
        except Exception:
            print("exception")
            username_str = "no_username"
        text_lines.append(
            f"ID: {u['telegram_id']} | Name: {u['first_name']} {u['last_name']} | Username: {username_str} | Phone: {u['phone_number']} | Role: {u['role']}{role_str} | Registaerd at: {u['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
        )

    text = "\n".join(text_lines)
    return text