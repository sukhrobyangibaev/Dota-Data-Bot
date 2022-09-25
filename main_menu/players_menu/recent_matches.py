import requests
from telegram import Update
from telegram.ext import ContextTypes

from constants import ACCOUNT_ID
from helpers import helpers
from main_menu.players_menu import player_menu


async def recent_matches(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    account_id = context.user_data.get(ACCOUNT_ID)
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/recentMatches")
    res_json = response.json()
    text = helpers.matches_to_str(res_json)

    await update.message.reply_text(text=text)

    return await player_menu(update, context)
