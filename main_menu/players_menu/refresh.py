import requests
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from constants import REFRESH, ACCOUNT_ID


async def refresh(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    account_id = context.user_data.get(ACCOUNT_ID)
    response = requests.post(f"https://api.opendota.com/api/players/{account_id}/refresh")
    if response.status_code == 200:
        text = "account refreshed"
    else:
        text = "wrong request"
    button = [["BACK"]]
    keyboard = ReplyKeyboardMarkup(button)
    await update.message.reply_text(text=text, reply_markup=keyboard)

    return REFRESH
