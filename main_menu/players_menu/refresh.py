import requests
from telegram import Update
from telegram.ext import ContextTypes

from constants import ACCOUNT_ID
from main_menu.players_menu import player_menu


async def refresh(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    account_id = context.user_data.get(ACCOUNT_ID)
    response = requests.post(f"https://api.opendota.com/api/players/{account_id}/refresh")
    if response.status_code == 200:
        text = "account refreshed"
    else:
        text = "wrong request"

    await update.message.reply_text(text=text)

    return await player_menu(update, context)
