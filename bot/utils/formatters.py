from bot.db import database
from aiogram.exceptions import AiogramError
from aiogram.types import InputMediaPhoto, FSInputFile
from bot.utils.texts import SEPARATOR, PROFILE_NAME, PROFILE_PHONE, PROFILE_INSTAGRAM, PROFILE_GOAL, PROFILE_STATUS, PROFILE_MENTOR, PARTICIPANT_PROFILE_HEADER, MENTOR_PROFILE_HEADER, PROFILE_DESCRIPTION, PROFILE_JAR, REGISTERED_USERS_HEADER, QUESTION_LIST_HEADER, SUGGEST_ANSWER_COMMAND, FUNDRAISING_DESIGN_2000_10000, FUNDRAISING_DESIGN_10000_150000, FUNDRAISING_DESIGN_150000_20000, FUNDRAISING_DESIGN_20000_25000, FUNDRAISING_DESIGN_25000_50000, FUNDRAISING_DESIGN_MENTOR, DEFAULT_PROFILE_NAME, DESIGN_WHEEL_BUTTON, DESIGN_CAMERA_BUTTON, DESIGN_CIRCUIT_BUTTON, DESIGN_CONNECTION_BUTTON, DESIGN_ENGINE_BUTTON, PROFILE_DESIGN_PREFERENCE
MAX_MESSAGE_LENGTH = 4096


async def format_profile(user_id: int) -> str:
    user = await database.get_user_by_id(user_id)
    if not user:
        return "❌ User not found."
    header = PARTICIPANT_PROFILE_HEADER if user.get('role') == "participant" else MENTOR_PROFILE_HEADER
    base_info = (
        f"{SEPARATOR}"        
        f"{header}\n"
        f"{SEPARATOR}"
        f"{DEFAULT_PROFILE_NAME}{user.get('default_name') or ''}\n"
        f"{PROFILE_NAME}{user.get('first_name') or ''} {user.get('last_name') or ''} @{user.get('username') or ''}\n"
        f"{PROFILE_PHONE}{user.get('phone_number') or '—'}\n"
        f"{PROFILE_INSTAGRAM}{user.get('instagram') or '—'}\n"
        f"{PROFILE_GOAL}{format_amount(user.get('fundraising_goal', 0.0))}\n"
        f"{PROFILE_JAR}{user.get('jar_url', '—')}\n"
        f"{PROFILE_DESIGN_PREFERENCE}{user.get('design_preference', '—')}\n"
    )

    if user.get('role') == "mentor":
        base_info += f"{PROFILE_DESCRIPTION}{user['description']}\n"
        base_info += f"{PROFILE_STATUS}{user['status']}\n"

    if user.get('role') == "participant":
        mentor = await database.get_user_by_id(user.get('mentor_id'))
        if mentor:
            base_info += f"{PROFILE_MENTOR}{mentor.get('default_name', '')}\n"

    return base_info


async def format_profile_image(user_id: int):
    file_id = await database.get_user_design_animation(user_id)
    if not file_id:
        file_id = await database.get_user_design_video(user_id)
    if not file_id:
        file_id = await database.get_user_uncompressed_design(user_id)
    if not file_id:
        file_id = await database.get_user_uncompressed_photo(user_id)
    if not file_id:
        photo = await database.get_file_by_name('default_uncompressed')
        file_id = photo.get('file_id')
    if file_id:
        return file_id
    photo = FSInputFile("resources/photos/default.png", filename="no-profile-picture.png")
    return photo


async def format_mentor_profile_view(mentor_id: int):
    mentor = await database.get_user_by_id(mentor_id)
    text = mentor.get('description', "No description provided.")
    file_id = await database.get_user_design_animation(mentor_id)
    type = 'animation'
    if not file_id:
        file_id = await database.get_user_design_video(mentor_id)
        type = 'video'
    if not file_id:
        type = 'photo'
        file_id = await database.get_user_compressed_design(mentor_id)
    if not file_id:
        file_id = await database.get_user_compressed_photo(mentor_id)
    if not file_id:
        photo = await database.get_file_by_name('default_compressed')
        file_id = photo.get('file_id')
    if file_id:
        return file_id, text, type
    photo = FSInputFile("resources/photos/default.png", filename="no-profile-picture.png")
    return photo, text

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
            f"ID: {u['telegram_id']} | Name: {u['default_name']} | Fullname: {u['first_name']} {u['last_name']} | Username: {username_str} | Phone: {u['phone_number']} | Role: {u['role']}{role_str} | Registaerd at: {u['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
        )

    text = "\n".join(text_lines)
    return text


async def format_question_list() -> str:
    questions = await database.get_questions()
    if not questions:
        return None

    text_lines = [QUESTION_LIST_HEADER]
    for q in questions:
        user = await database.get_user_by_id(q['telegram_id'])
        if not user:
            continue
        text_lines.append(
            f"❓{q['id']}) Запитує: {user['default_name']} ({user['first_name']} {user['last_name']} @{user['username']}) | Статус: {q['status']} | Text: {q['question_text']} | Запитання надіслано: {q['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
        )

    text = "\n".join(text_lines)
    text += f"\n{SUGGEST_ANSWER_COMMAND}"
    return text


async def format_design_msg(user) -> str:
    goal = user['fundraising_goal']
    insta = ''
    if user['role'] == 'participant':
        mentor = await database.get_user_by_id(user['mentor_id'])
        insta = mentor['instagram']
    if user['role'] == 'mentor':
        return FUNDRAISING_DESIGN_MENTOR.format(amount=goal)
    if goal < 2000:
        return None
    if goal < 10000:
        return FUNDRAISING_DESIGN_2000_10000.format(amount=goal, instagram=insta)
    if goal < 15000:
        return FUNDRAISING_DESIGN_10000_150000.format(amount=goal, instagram=insta)
    if goal < 20000:
        return FUNDRAISING_DESIGN_150000_20000.format(amount=goal, instagram=insta)
    if goal < 25000:
        return FUNDRAISING_DESIGN_20000_25000.format(amount=goal, instagram=insta)
    return FUNDRAISING_DESIGN_25000_50000.format(amount=goal, instagram=insta)


async def send_long_message(bot, chat_id: int, text: str, **kwargs):
    while text:
        chunk = text[:MAX_MESSAGE_LENGTH]
        if len(text) > MAX_MESSAGE_LENGTH:
            split_at = max(chunk.rfind("\n"), chunk.rfind(" "))
            if split_at == -1:
                split_at = MAX_MESSAGE_LENGTH
            chunk = text[:split_at]
            text = text[split_at:].lstrip()
        else:
            text = ""
        
        await bot.send_message(chat_id, chunk, **kwargs)


def format_design_preference(design_preference: str):
    if design_preference == 'wheel':
        return DESIGN_WHEEL_BUTTON
    if design_preference == 'connection':
        return DESIGN_CONNECTION_BUTTON
    if design_preference == 'camera':
        return DESIGN_CAMERA_BUTTON
    if design_preference == 'engine':
        return DESIGN_ENGINE_BUTTON
    if design_preference == 'circuit':
        return DESIGN_CIRCUIT_BUTTON
    

async def format_design_photos():
    design_wheel = await database.get_file_by_name('design_wheel_compressed')
    design_camera = await database.get_file_by_name('design_camera_compressed')
    design_circuit = await database.get_file_by_name('design_circuit_compressed')
    design_connection = await database.get_file_by_name('design_connection_compressed')
    design_engine = await database.get_file_by_name('design_engine_compressed')
    media = [
        InputMediaPhoto(media=design_wheel['file_id'], caption=DESIGN_WHEEL_BUTTON),
        InputMediaPhoto(media=design_camera['file_id'], caption=DESIGN_CONNECTION_BUTTON),
        InputMediaPhoto(media=design_circuit['file_id'], caption=DESIGN_CIRCUIT_BUTTON),
        InputMediaPhoto(media=design_connection['file_id'], caption=DESIGN_CONNECTION_BUTTON),
        InputMediaPhoto(media=design_engine['file_id'], caption=DESIGN_ENGINE_BUTTON)
    ]    
    return media