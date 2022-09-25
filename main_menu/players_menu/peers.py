import requests
from telegram import Update
from telegram.ext import ContextTypes

from constants import ACCOUNT_ID
from helpers import helpers
from main_menu.players_menu import player_menu
from plots import get_peers_plot


async def peers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    account_id = context.user_data.get(ACCOUNT_ID)
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/peers",
                            params={"sort": "games"})
    res_json = response.json()
    peers_dict = helpers.peers_to_dict(res_json)
    plot = get_peers_plot(peers_dict)

    await update.message.reply_photo(photo=plot)

    return await player_menu(update, context)
