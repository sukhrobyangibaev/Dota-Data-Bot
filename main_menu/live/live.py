import requests
from telegram import Update, ReplyKeyboardMarkup

from constants import LIVE, fav_players_col
from helpers import helpers


async def live(update: Update, _) -> int:
    user_id = update.effective_user.id
    fav_players = fav_players_col.find_one({"user_id": user_id})
    response = requests.get(f"https://api.opendota.com/api/live")
    res_json = response.json()

    text = helpers.get_pro_matches(res_json)
    if not text:
        text = "no pro matches\n\n"
    text += helpers.get_public_matches(res_json, fav_players)

    button = [["MAIN MENU"]]
    keyboard = ReplyKeyboardMarkup(button)
    while len(text) > 4096:
        last_pos = text[0:4096].rfind("\n\n")
        await update.message.reply_html(text=text[0:last_pos])
        text = text[last_pos:len(text)]

    await update.message.reply_html(text=text, reply_markup=keyboard)

    return LIVE
