import gspread
from google.oauth2.service_account import Credentials
from bot.config import SHEET_KEY, SHEET_NAME, GOOGLE_SERVICE_ACCOUNT_JSON
import os
from bot.utils.formatters import format_spreadsheets_data
import json
from bot.db import database

def get_gspread_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]

    try:
        service_account_info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
        creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
        #creds = Credentials.from_service_account_file(".secrets/service_account.json", scopes=scopes)
        print("✅ Loaded Google credentials from environment variable.")
    except json.JSONDecodeError:
        raise ValueError("❌ GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON.")
    
    client = gspread.authorize(creds)
    return client

client = get_gspread_client()
spreadsheet = client.open_by_key(SHEET_KEY)
print("✅ opened sheets")

async def export_users_to_sheet(users = None, sheet_name: str = SHEET_NAME):
    try:
        sheet = spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
    
    sheet.batch_clear(['A1:L1000'])

    if not users:
        users = await database.get_all_users()

    if not users:
        sheet.update("A1", [["No users found in the database."]])
        return

    headers, rows = await format_spreadsheets_data(users)
    sheet.update("A1", [headers] + rows)
    sheet.spreadsheet.batch_update({
        "requests": [
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet.id,
                        "startColumnIndex": 7,
                        "endColumnIndex": 9
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "numberFormat": {
                                "type": "CURRENCY", 
                                "pattern": "₴#,##0.00"
                            }
                        }
                    },
                    "fields": "userEnteredFormat.numberFormat"
                }
            }
        ]
    })


async def append_user_to_sheet(user, sheet_name: str = SHEET_NAME):
    try:
        sheet = spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
        headers, _ = await format_spreadsheets_data([])
        sheet.append_row(headers, value_input_option="USER_ENTERED")

    if not user:
        return
    
    _, row = await format_spreadsheets_data([user])

    sheet.append_row(row[0], value_input_option="USER_ENTERED")
