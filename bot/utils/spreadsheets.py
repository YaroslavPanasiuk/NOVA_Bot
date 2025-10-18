import gspread
from google.oauth2.service_account import Credentials
from bot.config import SHEET_URL, SHEET_NAME, GOOGLE_SERVICE_ACCOUNT_JSON
import os
import json

def get_gspread_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]

    try:
        service_account_info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
        creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
        print("✅ Loaded Google credentials from environment variable.")
    except json.JSONDecodeError:
        raise ValueError("❌ GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON.")
    
    client = gspread.authorize(creds)
    return client

async def export_users_to_sheet(users, sheet_name: str = SHEET_NAME):
    client = get_gspread_client()
    spreadsheet = client.open_by_url(SHEET_URL)
    try:
        sheet = spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)

    sheet.clear()

    if not users:
        sheet.update("A1", [["No users found in the database."]])
        return

    headers = ["Ім'я", "Ім'я в телеграм", "Нікнейм", "Роль", "Статус", "Інстаграм", "Банка", "Ціль", "Дизайн", "Номер телефону", "Час реєстрації"]
    rows = []
    for u in users:
        if u.get("instagram", "") == "":
            insta = ""
        else:
            insta = f"https://www.instagram.com/{u.get('instagram', '')}"
        if u['design_uncompressed'] is None and u['design_video'] is None and u['design_animation'] is None:
            design = ""
        else:
            design = "✅"
        rows.append([
            u.get("default_name", ""),
            f"{u.get('first_name', '')} {u.get('last_name', '')}",
            f"@{u.get('username', '')}",
            u.get("role", ""),
            u.get("status", ""),
            insta,
            u.get("jar_url", ""),
            str(u.get("fundraising_goal", "")),
            design,
            u.get("phone_number", ""),
            u.get("created_at", "").strftime("%Y-%m-%d %H:%M:%S")
        ])
    sheet.update("A1", [headers] + rows)

async def append_users_to_sheet(users, sheet_name: str = SHEET_NAME):
    client = get_gspread_client()
    spreadsheet = client.open_by_url(SHEET_URL)

    try:
        sheet = spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
        headers = ["Ім'я", "Ім'я в телеграм", "Нікнейм", "Роль", "Статус", "Інстаграм", "Банка", "Ціль", "Дизайн", "Час реєстрації", "Номер телефону"]
        sheet.append_row(headers, value_input_option="USER_ENTERED")

    if not users:
        return

    for u in users:

        row = [
            u.get("default_name", ""),
            f"{u.get('first_name', '')} {u.get('last_name', '')}",
            f"@{u.get('username', '')}" if u.get("username") else "",
            u.get("role", ""),
            u.get("status", ""),
            f"https://www.instagram.com/{u.get('instagram', '')}" if u.get("instagram") else "",
            u.get("jar_url", ""),
            str(u.get("fundraising_goal", "")),
            u.get("design_uncompressed", ""),
            u.get("created_at").strftime("%Y-%m-%d %H:%M:%S"),
            u.get("phone_number", ""),
        ]

        sheet.append_row(row, value_input_option="USER_ENTERED")
