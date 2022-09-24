import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from constants import fav_players_col
from helpers import helpers
from main_menu import main_menu


async def live(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    fav_players = fav_players_col.find_one({"user_id": user_id})
    response = requests.get(f"https://api.opendota.com/api/live")
    res_json = response.json()

    text = helpers.get_pro_matches(res_json)
    if not text:
        text = "no pro matches\n\n"
    text += helpers.get_public_matches(res_json, fav_players)

    while len(text) > 4096:
        last_pos = text[0:4096].rfind("\n\n")
        await update.message.reply_html(text=text[0:last_pos])
        text = text[last_pos:len(text)]

    await update.message.reply_html(text=text)

    return await main_menu(update, context)
