import time
import requests
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import ContextTypes
import pandas as pd
from constants import LIVE_LEAGUE, SELECTED_LEAGUE_MATCH
from dotenv import load_dotenv
import os

from helpers.helpers import get_league_match_button_text, get_league_match_features, get_league_match_info, predict_league_match_result

load_dotenv()

LEAGUE_GAMES_URL = "https://api.steampowered.com/IDOTA2Match_570/getLiveLeagueGames/v1/"
KEY = os.getenv("STEAM_KEY")


async def live_league(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    buttons = []

    response = requests.get(LEAGUE_GAMES_URL, params={"key": KEY})
    res_json = response.json()

    context.chat_data["last_league_response"] = res_json

    for match in res_json["result"]["games"]:
        button_text = get_league_match_button_text(match)

        if button_text:
            buttons.append(
                [InlineKeyboardButton(button_text, callback_data=match["match_id"])]
            )

    keyboard = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("Live League Matches:", reply_markup=keyboard)

    return LIVE_LEAGUE


async def select_league_match(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    match_id = query.data

    context.chat_data['selected_league_match_id'] = match_id

    res_json = context.chat_data["last_league_response"]


    for entry in res_json["result"]["games"]:
        if str(entry["match_id"]) != match_id:
            continue

        match_info = get_league_match_info(entry)

        X = get_league_match_features(entry)
        
        prediction = predict_league_match_result(X)

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔙", callback_data='back'),
          InlineKeyboardButton("🔃", callback_data='refresh')]]
    )

    await query.edit_message_text(match_info + prediction, reply_markup=keyboard)
    return SELECTED_LEAGUE_MATCH


async def league_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    buttons = []

    response = requests.get(LEAGUE_GAMES_URL, params={"key": KEY})
    res_json = response.json()

    context.chat_data["last_league_response"] = res_json

    for match in res_json["result"]["games"]:
        button_text = get_league_match_button_text(match)

        if button_text:
            buttons.append(
                [InlineKeyboardButton(button_text, callback_data=match["match_id"])]
            )

    keyboard = InlineKeyboardMarkup(buttons)
    await query.edit_message_text("Live League Matches:", reply_markup=keyboard)

    return LIVE_LEAGUE


async def league_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text('refreshing') #TODO remove keyboard while refreshing

    match_id = context.chat_data['selected_league_match_id']

    response = requests.get(LEAGUE_GAMES_URL, params={"key": KEY})
    res_json = response.json()

    print(type(match_id), match_id)

    for entry in res_json["result"]["games"]:
        if str(entry["match_id"]) != match_id:
            continue
        print('found')

        match_info = get_league_match_info(entry)

        X = get_league_match_features(entry)
        
        prediction = predict_league_match_result(X)
    
    print(match_info, prediction)
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔙", callback_data='back'),
          InlineKeyboardButton("🔃", callback_data='refresh')]]
    )

    
    await query.edit_message_text(match_info + prediction, reply_markup=keyboard)

    return SELECTED_LEAGUE_MATCH