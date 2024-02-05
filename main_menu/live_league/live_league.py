import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from constants import fav_players_col
from helpers import helpers
from main_menu import main_menu
from dotenv import load_dotenv
import os

load_dotenv()

LEAGUE_GAMES_URL = 'https://api.steampowered.com/IDOTA2Match_570/getLiveLeagueGames/v1/'
KEY = os.getenv("STEAM_KEY")

async def live_league(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    fav_players = fav_players_col.find_one({"user_id": user_id})

    response = requests.get(LEAGUE_GAMES_URL, params={"key": KEY})
    res_json = response.json()

    text = ''
    for game in res_json['result']['games']:
        text += str(game['match_id']) + '\n'

    while len(text) > 4096:
        last_pos = text[0:4096].rfind("\n\n")
        await update.message.reply_html(text=text[0:last_pos])
        text = text[last_pos:len(text)]

    await update.message.reply_html(text=text)

    return await main_menu(update, context)
