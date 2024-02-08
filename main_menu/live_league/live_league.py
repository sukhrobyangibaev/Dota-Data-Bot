import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from constants import LIVE_LEAGUE, SELECTED_LEAGUE_MATCH
from main_menu import main_menu
from dotenv import load_dotenv
import os

load_dotenv()

LEAGUE_GAMES_URL = "https://api.steampowered.com/IDOTA2Match_570/getLiveLeagueGames/v1/"
KEY = os.getenv("STEAM_KEY")


async def live_league(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    buttons = []
    
    response = requests.get(LEAGUE_GAMES_URL, params={"key": KEY})
    res_json = response.json()

    for match in res_json["result"]["games"]:
        if 'scoreboard' not in match or match['scoreboard']['duration'] == 0:
            continue

        radiant = dire = "unknown"
        radiant_score = dire_score = 0
        duration = '0:0'
        if "radiant_team" in match:
            radiant = match["radiant_team"]["team_name"]
        if "dire_team" in match:
            dire = match["dire_team"]["team_name"]
        h, m = divmod(match["scoreboard"]["duration"], 60)
        duration = "{}:{:02}".format(int(h), int(m))
        radiant_score = match["scoreboard"]["radiant"]["score"]
        dire_score = match["scoreboard"]["dire"]["score"]

        text = "\n\n{} [{}] 🆚 [{}] {} ⏲ {}".format(
            radiant, radiant_score, dire_score, dire, duration
        )
        buttons.append([InlineKeyboardButton(text, callback_data=match['match_id'])])

    keyboard = InlineKeyboardMarkup(buttons)
    await update.message.reply_text('Live League Matches:', reply_markup=keyboard)

    return LIVE_LEAGUE


async def select_league_match(update: Update, _) -> int:
    query = update.callback_query
    await query.answer()

    match_id = query.data

    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('text', callback_data=match_id)]])

    await query.edit_message_text('text', reply_markup=keyboard)
    return SELECTED_LEAGUE_MATCH
