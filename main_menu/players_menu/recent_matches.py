import requests
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from constants import RECENT_MATCHES, ACCOUNT_ID
from helpers import helpers


async def recent_matches(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    account_id = context.user_data.get(ACCOUNT_ID)
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/recentMatches")
    res_json = response.json()
    text = helpers.matches_to_str(res_json)

    button = [["BACK"]]
    keyboard = ReplyKeyboardMarkup(button)
    await update.message.reply_text(text=text, reply_markup=keyboard)

    return RECENT_MATCHES
