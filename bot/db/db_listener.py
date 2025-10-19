import asyncio
import asyncpg
import json
from bot.db import database
from bot.config import DATABASE_URL
from bot.utils.spreadsheets import append_user_to_sheet, export_users_to_sheet

async def handle_notification(payload: str):
    """Process the received notification payload."""
    data = json.loads(payload)

    if data["operation"] == "INSERT":
        user = await database.get_user_by_id(data['telegram_id'])
        await append_user_to_sheet(user)
        print("✅INSERT")
    elif data["operation"] == "UPDATE":
        print("✅UPDATE")
    elif data["operation"] == "DELETE":
        await export_users_to_sheet()
        print("✅DELETE")

async def listen_for_changes():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.add_listener("user_changes", lambda *args: asyncio.create_task(handle_notification(args[-1])))
    print("✅ Listening for database changes on 'user_changes' channel...")

    try:
        while True:
            await asyncio.sleep(3600)  # keep alive
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(listen_for_changes())
