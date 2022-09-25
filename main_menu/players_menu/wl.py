import requests
from telegram import Update
from telegram.ext import ContextTypes

from constants import ACCOUNT_ID
from helpers import helpers
from main_menu.players_menu import player_menu


async def wl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    account_id = context.user_data[ACCOUNT_ID]
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/wl")
    if response.status_code == 200:
        res_json = response.json()
        text = "Won: " + str(res_json["win"]) + "\nLost: " + str(res_json["lose"])
        text += "\nWinrate: " + helpers.count_winrate(res_json["win"] + res_json["lose"], res_json["win"])
    else:
        text = "Error"
    await update.message.reply_text(text=text)
    return await player_menu(update, context)
