import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from constants import ACCOUNT_ID, WL
from helpers import helpers


async def wl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    button = [["BACK"]]
    keyboard = ReplyKeyboardMarkup(button)

    account_id = context.user_data[ACCOUNT_ID]
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/wl")
    if response.status_code == 200:
        res_json = response.json()
        text = "Won: " + str(res_json["win"]) + "\nLost: " + str(res_json["lose"])
        text += "\nWinrate: " + helpers.count_winrate(res_json["win"] + res_json["lose"], res_json["win"])
    else:
        text = "Error"
    await update.message.reply_text(text=text, reply_markup=keyboard)
    return WL
