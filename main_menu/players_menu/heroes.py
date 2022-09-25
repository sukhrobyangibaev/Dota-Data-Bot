import requests
from telegram import Update
from telegram.ext import ContextTypes

from constants import ACCOUNT_ID
from helpers import helpers
from plots import get_most_picked_heroes_plot
from .players_menu import player_menu


async def player_heroes_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    account_id = context.user_data.get(ACCOUNT_ID)
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/heroes",
                            params={"sort": "games"})
    res_json = response.json()
    heroes_dict = helpers.hero_stats(res_json)
    plot = get_most_picked_heroes_plot(heroes_dict)

    await update.message.reply_photo(photo=plot)

    return await player_menu(update, context)
