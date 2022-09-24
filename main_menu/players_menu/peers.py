import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from constants import ACCOUNT_ID, PEERS
from helpers import helpers
from plots import get_peers_plot


async def peers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    account_id = context.user_data.get(ACCOUNT_ID)
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/peers",
                            params={"sort": "games"})
    res_json = response.json()
    peers_dict = helpers.peers_to_dict(res_json)
    plot = get_peers_plot(peers_dict)
    button = [["BACK"]]
    keyboard = ReplyKeyboardMarkup(button)
    await update.message.reply_photo(photo=plot, reply_markup=keyboard)

    return PEERS
