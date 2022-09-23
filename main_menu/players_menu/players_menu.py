# MAIN MENU -> PLAYERS MENU --------------------------------------------------------------------------------
import requests
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from constants import *
from helpers import helpers


async def check_account_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if ACCOUNT_ID in context.user_data:
        return await player_menu(update, context)
    else:
        return await type_account_id(update, context)


async def type_account_id(update: Update, _) -> int:
    await update.message.reply_text(text="✍ write player's id (e.g. 311360822)", reply_markup=ReplyKeyboardRemove())

    return TYPE_ACCOUNT_ID


async def save_account_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    account_id = update.message.text
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}")
    if response.status_code == 200 and "profile" in response.json():
        buttons = [["PLAYER'S MENU"], ["WRITE OTHER ID"], ["MAIN MENU"]]

        context.user_data[ACCOUNT_ID] = account_id
        res_json = response.json()
        context.user_data[PLAYER_NAME] = res_json["profile"]["personaname"]
        text = "Player's name: " + res_json["profile"]["personaname"]
    else:
        buttons = [["WRITE OTHER ID"], ["MAIN MENU"]]
        text = "wrong player's id"

    keyboard = ReplyKeyboardMarkup(buttons)
    await update.message.reply_text(text=text, reply_markup=keyboard)
    return PLAYERS


async def player_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    search_buttons = [
        ["WIN/LOSE", "RECENT MATCHES", "SORTED MATCHES"],
        ["MOST PICKED HEROES", "PEERS", "TOTALS"],
        ["LEAVER STATUS", "WORDCLOUD", "REFRESH"],
        ["WRITE OTHER ID", "MAIN MENU"]
    ]
    keyboard = ReplyKeyboardMarkup(search_buttons)
    text = "account id: " + context.user_data[ACCOUNT_ID] + ", name: " + context.user_data[PLAYER_NAME]
    await update.message.reply_text(text=text, reply_markup=keyboard)

    return PLAYERS
