import requests
from telegram import Update, ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from constants import TYPING_MATCH_ID, MATCHES
from helpers import helpers
from main_menu import main_menu


async def matches(update: Update, _) -> int:
    await update.message.reply_text(text="✍ write match id (e.g. 6720147701)", reply_markup=ReplyKeyboardRemove())

    return TYPING_MATCH_ID


async def get_match_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    match_id = update.message.text
    buttons = [["WRITE OTHER ID"], ["MAIN MENU"]]
    keyboard = ReplyKeyboardMarkup(buttons)

    response = requests.get(f"https://api.opendota.com/api/matches/{match_id}")
    if response.status_code == 200:
        res_json = response.json()
        if "radiant_team" in response.json():
            teams = {
                "radiant": res_json["radiant_team"]["name"],
                "dire": res_json["dire_team"]["name"]
            }
        else:
            teams = {
                "radiant": "Radiant",
                "dire": "Dire"
            }
        text = teams["radiant"] + " vs " + teams["dire"]
        if res_json["radiant_win"]:
            text += "\nVictory: " + teams[helpers.who_won(res_json["radiant_win"])]
        if res_json["radiant_score"]:
            text += "\nKills: " + teams["radiant"] + " " + str(res_json["radiant_score"]) + ":" \
                    + str(res_json["dire_score"]) + " " + teams["radiant"]
        if res_json["duration"]:
            text += "\nDuration of match: " + helpers.seconds_to_minutes(res_json["duration"])
        if res_json["picks_bans"]:
            text += "\n\nPicks:\n" + helpers.get_picks(teams, res_json["picks_bans"])
        await update.message.reply_text(text=text)
    else:
        text = "wrong match id"
        await update.message.reply_text(text=text)

    return await main_menu(update, context)
