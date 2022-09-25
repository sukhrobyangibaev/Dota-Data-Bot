import requests
from telegram import Update
from telegram.ext import ContextTypes

from constants import ACCOUNT_ID
from helpers import helpers
from main_menu.players_menu import player_menu
from plots import get_pie_plot


async def wordcloud(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    account_id = context.user_data.get(ACCOUNT_ID)
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/wordcloud")
    res_json = response.json()
    word_list = helpers.get_wordcloud_list(res_json)

    plot = get_pie_plot(word_list)
    await update.message.reply_photo(photo=plot)

    return await player_menu(update, context)
