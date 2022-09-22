import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from constants import ACCOUNT_ID, PEERS
from helpers import helpers


async def peers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    account_id = context.user_data.get(ACCOUNT_ID)
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/peers",
                            params={"sort": "games"})
    res_json = response.json()
    text = helpers.peers_to_text(res_json)
    button = [["BACK"]]
    keyboard = ReplyKeyboardMarkup(button)
    await update.message.reply_text(text=text, reply_markup=keyboard)

    return PEERS
