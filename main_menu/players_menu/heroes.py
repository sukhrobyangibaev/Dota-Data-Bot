import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from constants import ACCOUNT_ID, PLAYER_HEROES
from helpers import helpers
from plots import get_most_picked_heroes_plot


async def player_heroes_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    account_id = context.user_data.get(ACCOUNT_ID)
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/heroes",
                            params={"sort": "games"})
    res_json = response.json()
    heroes_dict = helpers.hero_stats(res_json)
    plot = get_most_picked_heroes_plot(heroes_dict)
    button = [["BACK"]]
    keyboard = ReplyKeyboardMarkup(button)
    await update.message.reply_photo(photo=plot, reply_markup=keyboard)

    return PLAYER_HEROES
